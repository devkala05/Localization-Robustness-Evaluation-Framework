#!/usr/bin/env python3
"""Add RGBD_Inertial (IMU_RGBD) ROS node to the pinned ORB-SLAM3 build.

Creates Examples_old/ROS/ORB_SLAM3/src/ros_rgbd_inertial.cc and appends the
RGBD_Inertial target to the rosbuild CMakeLists.  Everything else in the native
build is unchanged.

Design: producer-consumer threading. ROS callbacks enqueue frames and return
immediately; a dedicated processing thread calls TrackRGBD(). Every synchronized
frame is retained. Dropping frames during local mapping made the next visual
update span too much vehicle motion and caused genuine tracking loss on Boreas.
The benchmark playback rate is selected so this lossless queue stays bounded.
"""
import os
from pathlib import Path

root = Path(os.environ.get("ORB_SLAM3_ROOT", "/root/ORB_SLAM3"))
ros_dir = root / "Examples_old/ROS/ORB_SLAM3"
src_dir = ros_dir / "src"
cmake   = ros_dir / "CMakeLists.txt"

# ── 1. Write ros_rgbd_inertial.cc ────────────────────────────────────────────
source_path = src_dir / "ros_rgbd_inertial.cc"
if source_path.exists():
    print(f"[add_rgbd_inertial] {source_path.name} already exists — skipping source write")
else:
    source = r'''/**
 * ros_rgbd_inertial.cc
 * ORB-SLAM3 RGB-D + IMU (IMU_RGBD) ROS node for the E2O wrapper.
 *
 * Architecture: producer-consumer with a dedicated processing thread.
 *
 * ROS subscriber callbacks (IMU + synced RGB-D) NEVER call TrackRGBD() directly.
 * They only enqueue data and return immediately.  A separate thread drains the
 * frame queue, waits until the IMU buffer brackets the image timestamp,
 * collects IMU measurements, and calls TrackRGBD(). Every synchronized input
 * frame is processed in timestamp order.
 *
 * Derived from ros_rgbd.cc (message_filters sync) and ros_mono_inertial.cc
 * (IMU buffering pattern).  Tracking, optimisation, and loop-closure are untouched.
 */
#include <iostream>
#include <algorithm>
#include <fstream>
#include <chrono>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <cstdlib>

#include <ros/ros.h>
#include <cv_bridge/cv_bridge.h>
#include <sensor_msgs/Imu.h>
#include <message_filters/subscriber.h>
#include <message_filters/time_synchronizer.h>
#include <message_filters/sync_policies/approximate_time.h>

#include <geometry_msgs/PoseStamped.h>
#include <geometry_msgs/Point32.h>
#include <sensor_msgs/PointCloud.h>
#include <nav_msgs/Path.h>
#include <Eigen/Geometry>
#include <sophus/se3.hpp>

#include <opencv2/core/core.hpp>

#include "../../../include/System.h"
#include "../include/ImuTypes.h"
#include "Atlas.h"
#include "Map.h"
#include "MapPoint.h"
#include "KeyFrame.h"

using namespace std;

// ── helpers ──────────────────────────────────────────────────────────────────
static bool finitePose(const Sophus::SE3f& Tcw)
{
    return Tcw.matrix().allFinite();
}

static geometry_msgs::PoseStamped poseFromTcw(const Sophus::SE3f& Tcw,
                                               const ros::Time& stamp)
{
    const Eigen::Matrix3f Rcw = Tcw.rotationMatrix();
    const Eigen::Vector3f tcw = Tcw.translation();
    const Eigen::Matrix3f Rwc = Rcw.transpose();
    const Eigen::Vector3f twc = -Rwc * tcw;
    Eigen::Quaternionf q(Rwc);
    q.normalize();
    geometry_msgs::PoseStamped pose;
    pose.header.stamp    = stamp;
    pose.header.frame_id = "orbslam3_map";
    pose.pose.position.x    = twc.x();
    pose.pose.position.y    = twc.y();
    pose.pose.position.z    = twc.z();
    pose.pose.orientation.x = q.x();
    pose.pose.orientation.y = q.y();
    pose.pose.orientation.z = q.z();
    pose.pose.orientation.w = q.w();
    return pose;
}

// ── IMU grabber ───────────────────────────────────────────────────────────────
class ImuGrabber
{
public:
    ImuGrabber() : mRunning(true) {}

    void GrabImu(const sensor_msgs::ImuConstPtr& msg)
    {
        {
            std::lock_guard<std::mutex> lock(mBufMutex);
            if (!mRunning) return;
            imuBuf.push(msg);
        }
        mBufCv.notify_all();
    }

    // Match the native mono-inertial frontend: do not process an image until
    // the IMU buffer reaches its timestamp. Draining a merely-current buffer
    // can omit measurements still queued in another ROS callback.
    bool WaitAndDrainUpTo(double tImg,
                          vector<ORB_SLAM3::IMU::Point>& vImuMeas)
    {
        std::unique_lock<std::mutex> lock(mBufMutex);
        mBufCv.wait(lock, [this, tImg] {
            return !mRunning ||
                   (!imuBuf.empty() &&
                    imuBuf.back()->header.stamp.toSec() >= tImg);
        });
        if (imuBuf.empty() ||
            imuBuf.back()->header.stamp.toSec() < tImg)
            return false;

        while (!imuBuf.empty() &&
               imuBuf.front()->header.stamp.toSec() <= tImg)
        {
            const auto& m = imuBuf.front();
            double t = m->header.stamp.toSec();
            cv::Point3f acc(m->linear_acceleration.x,
                            m->linear_acceleration.y,
                            m->linear_acceleration.z);
            cv::Point3f gyr(m->angular_velocity.x,
                            m->angular_velocity.y,
                            m->angular_velocity.z);
            vImuMeas.emplace_back(acc, gyr, t);
            imuBuf.pop();
        }
        return true;
    }

    void Stop()
    {
        {
            std::lock_guard<std::mutex> lock(mBufMutex);
            mRunning = false;
        }
        mBufCv.notify_all();
    }

    queue<sensor_msgs::ImuConstPtr> imuBuf;
    std::mutex mBufMutex;
    std::condition_variable mBufCv;
    bool mRunning;
};

// ── Frame pair ────────────────────────────────────────────────────────────────
struct ImageFrame {
    sensor_msgs::ImageConstPtr rgb;
    sensor_msgs::ImageConstPtr depth;
};

// ── Image+Depth grabber with processing thread ────────────────────────────────
class ImageGrabber
{
public:
    ImageGrabber(ORB_SLAM3::System* pSLAM, ImuGrabber* pImuGb,
                 ros::NodeHandle& nh)
        : mpSLAM(pSLAM), mpImuGb(pImuGb), mRunning(true)
    {
        pose_pub          = nh.advertise<geometry_msgs::PoseStamped>("/orb_slam3/camera_pose", 10);
        map_pub           = nh.advertise<sensor_msgs::PointCloud>("/orb_slam3/map_points", 2);
        keyframe_path_pub = nh.advertise<nav_msgs::Path>("/orb_slam3/keyframe_path", 2, true);
    }

    // ROS callback: enqueue without blocking the tracking thread. Public
    // offline evaluation must not silently discard measurements.
    void GrabRGBD(const sensor_msgs::ImageConstPtr& msgRGB,
                  const sensor_msgs::ImageConstPtr& msgD)
    {
        std::lock_guard<std::mutex> lock(mBufMutex);
        mFrameBuf.push({msgRGB, msgD});
        mBufCv.notify_one();
    }

    void Stop()
    {
        {
            std::lock_guard<std::mutex> lock(mBufMutex);
            mRunning = false;
        }
        mBufCv.notify_all();
    }

    // Processing thread: runs TrackRGBD() without blocking ROS callbacks.
    void ProcessFrames()
    {
        double last_map_t = -1.0;
        while (true)
        {
            ImageFrame frame;
            {
                std::unique_lock<std::mutex> lock(mBufMutex);
                mBufCv.wait_for(lock, std::chrono::milliseconds(100),
                                [this]{ return !mFrameBuf.empty() || !mRunning; });
                if (!mRunning && mFrameBuf.empty()) break;
                if (mFrameBuf.empty()) continue;
                frame = mFrameBuf.front();
                mFrameBuf.pop();
            }

            const double tImg = frame.rgb->header.stamp.toSec();

            vector<ORB_SLAM3::IMU::Point> vImuMeas;
            if (!mpImuGb->WaitAndDrainUpTo(tImg, vImuMeas))
                continue;

            cv_bridge::CvImageConstPtr cv_rgb, cv_depth;
            try { cv_rgb   = cv_bridge::toCvShare(frame.rgb); }
            catch (cv_bridge::Exception& e)
            { ROS_ERROR("cv_bridge RGB exception: %s", e.what()); continue; }
            try { cv_depth = cv_bridge::toCvShare(frame.depth); }
            catch (cv_bridge::Exception& e)
            { ROS_ERROR("cv_bridge depth exception: %s", e.what()); continue; }

            Sophus::SE3f Tcw = mpSLAM->TrackRGBD(cv_rgb->image, cv_depth->image,
                                                   tImg, vImuMeas);

            if (mpSLAM->GetTrackingState() != 2 || !finitePose(Tcw))
                continue;

            pose_pub.publish(poseFromTcw(Tcw, frame.rgb->header.stamp));

            if (last_map_t < 0.0 || tImg - last_map_t >= 0.5)
            {
                last_map_t = tImg;
                sensor_msgs::PointCloud cloud;
                cloud.header.stamp    = frame.rgb->header.stamp;
                cloud.header.frame_id = "orbslam3_map";
                ORB_SLAM3::Map* current_map = mpSLAM->GetAtlas()->GetCurrentMap();
                const auto points = current_map
                    ? current_map->GetAllMapPoints()
                    : vector<ORB_SLAM3::MapPoint*>();
                cloud.points.reserve(points.size());
                for (ORB_SLAM3::MapPoint* p : points)
                {
                    if (!p || p->isBad()) continue;
                    Eigen::Vector3f wp = p->GetWorldPos();
                    if (!wp.allFinite()) continue;
                    geometry_msgs::Point32 pt;
                    pt.x = wp.x(); pt.y = wp.y(); pt.z = wp.z();
                    cloud.points.push_back(pt);
                }
                map_pub.publish(cloud);

                nav_msgs::Path kf_path;
                kf_path.header = cloud.header;
                auto kfs = current_map
                    ? current_map->GetAllKeyFrames()
                    : vector<ORB_SLAM3::KeyFrame*>();
                sort(kfs.begin(), kfs.end(),
                     [](const ORB_SLAM3::KeyFrame* a, const ORB_SLAM3::KeyFrame* b)
                     { return a->mnId < b->mnId; });
                for (ORB_SLAM3::KeyFrame* kf : kfs)
                {
                    if (!kf || kf->isBad()) continue;
                    kf_path.poses.push_back(
                        poseFromTcw(kf->GetPose(), ros::Time(kf->mTimeStamp)));
                }
                keyframe_path_pub.publish(kf_path);
            }
        }
    }

    ORB_SLAM3::System*      mpSLAM;
    ImuGrabber*             mpImuGb;
    ros::Publisher          pose_pub;
    ros::Publisher          map_pub;
    ros::Publisher          keyframe_path_pub;

    std::queue<ImageFrame>  mFrameBuf;
    std::mutex              mBufMutex;
    std::condition_variable mBufCv;
    bool                    mRunning;
};

// ── main ──────────────────────────────────────────────────────────────────────
int main(int argc, char** argv)
{
    ros::init(argc, argv, "RGBD_Inertial");
    ros::start();

    if (argc != 3)
    {
        cerr << "\nUsage: rosrun ORB_SLAM3 RGBD_Inertial "
                "path_to_vocabulary path_to_settings\n";
        ros::shutdown();
        return 1;
    }

    ORB_SLAM3::System SLAM(argv[1], argv[2],
                           ORB_SLAM3::System::IMU_RGBD, false);

    ros::NodeHandle nh;
    ImuGrabber imugb;
    ImageGrabber igb(&SLAM, &imugb, nh);

    // Processing thread runs TrackRGBD() — never blocks ROS callbacks.
    std::thread processingThread(&ImageGrabber::ProcessFrames, &igb);

    ros::Subscriber imu_sub = nh.subscribe(
        "/imu", 1000, &ImuGrabber::GrabImu, &imugb);

    message_filters::Subscriber<sensor_msgs::Image>
        rgb_sub(nh, "/camera/rgb/image_raw", 100);
    message_filters::Subscriber<sensor_msgs::Image>
        depth_sub(nh, "/camera/depth_registered/image_raw", 100);
    typedef message_filters::sync_policies::ApproximateTime<
        sensor_msgs::Image, sensor_msgs::Image> sync_pol;
    message_filters::Synchronizer<sync_pol> sync(sync_pol(10), rgb_sub, depth_sub);
    sync.registerCallback(boost::bind(&ImageGrabber::GrabRGBD, &igb, _1, _2));

    ros::spin();

    igb.Stop();
    imugb.Stop();
    processingThread.join();

    SLAM.Shutdown();
    const char* trajectory_env = std::getenv("ORB_SLAM3_TRAJECTORY_FILE");
    const std::string trajectory_file =
        trajectory_env ? trajectory_env : "CameraTrajectory.txt";
    SLAM.SaveTrajectoryTUM(trajectory_file);
    ros::shutdown();
    return 0;
}
'''
    source_path.write_text(source)
    print(f"[add_rgbd_inertial] wrote {source_path}")

# ── 2. Add RGBD_Inertial target to CMakeLists.txt ────────────────────────────
cmake_text = cmake.read_text()
if "RGBD_Inertial" in cmake_text:
    print("[add_rgbd_inertial] CMakeLists.txt already has RGBD_Inertial — skipping")
else:
    addition = """
# Node for RGB-D + IMU camera (added by E2O wrapper)
rosbuild_add_executable(RGBD_Inertial
src/ros_rgbd_inertial.cc
)

target_link_libraries(RGBD_Inertial
${LIBS}
)
"""
    cmake_text += addition
    cmake.write_text(cmake_text)
    print("[add_rgbd_inertial] patched CMakeLists.txt with RGBD_Inertial target")

print("[add_rgbd_inertial] done")
