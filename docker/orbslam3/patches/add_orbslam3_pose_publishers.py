#!/usr/bin/env python3
"""Add read-only pose and sparse-map outputs to the native RGB-D example.

Only the example interface is changed. Tracking, map management, optimization,
loop closure, place recognition, and feature extraction are untouched.

Design: producer-consumer threading, matching add_rgbd_inertial.py. The ROS
sync callback (GrabRGBD) only enqueues the newest frame and returns
immediately; a dedicated processing thread calls TrackRGBD(). When the
processor falls behind (e.g. during loop-closure/relocalization), old frames
are dropped so the system always works on the most recent data instead of
stalling frame delivery — matching real-time on-car behaviour.

The keyframe/map path publisher is throttled on a wall-clock timer and is NOT
gated on the current frame's tracking state, so RViz keeps showing the last
known (loop-closed) trajectory through a brief tracking loss instead of going
stale, and reflects new keyframes/corrections as soon as tracking recovers.
"""
import os
from pathlib import Path

root = Path(os.environ.get("ORB_SLAM3_ROOT", "/root/ORB_SLAM3"))
path = root / "Examples_old/ROS/ORB_SLAM3/src/ros_rgbd.cc"

MARKER = "ProcessFrames"
if MARKER in path.read_text():
    raise SystemExit(0)

source = r'''/**
 * ros_rgbd.cc
 * ORB-SLAM3 RGB-D (camera-only) ROS node for the E2O wrapper.
 *
 * Architecture: producer-consumer with a dedicated processing thread.
 *
 * The ROS synced-image callback (GrabRGBD) never calls TrackRGBD() directly.
 * It only enqueues the newest frame and returns immediately. A separate
 * thread drains the frame queue and calls TrackRGBD(). When the processor
 * falls behind, old frames are dropped so the system always works on the
 * most recent data — matching real-time on-car behaviour.
 *
 * Tracking, optimisation, and loop-closure are untouched; only the example
 * glue (frame delivery + read-only pose/map/path publishing) is changed.
 */
#include <iostream>
#include <algorithm>
#include <fstream>
#include <chrono>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>

#include <ros/ros.h>
#include <cv_bridge/cv_bridge.h>
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

// ── frame pair ───────────────────────────────────────────────────────────────
struct ImageFrame {
    sensor_msgs::ImageConstPtr rgb;
    sensor_msgs::ImageConstPtr depth;
};

// ── image+depth grabber with processing thread ────────────────────────────────
class ImageGrabber
{
public:
    ImageGrabber(ORB_SLAM3::System* pSLAM, ros::NodeHandle& nh)
        : mpSLAM(pSLAM), mRunning(true)
    {
        pose_pub          = nh.advertise<geometry_msgs::PoseStamped>("/orb_slam3/camera_pose", 10);
        map_pub           = nh.advertise<sensor_msgs::PointCloud>("/orb_slam3/map_points", 2);
        keyframe_path_pub = nh.advertise<nav_msgs::Path>("/orb_slam3/keyframe_path", 2, true);
    }

    // ROS callback: enqueue only the newest frame and return immediately.
    // If the processor is behind, stale frames are discarded — the system
    // always works on the most recent available data.
    void GrabRGBD(const sensor_msgs::ImageConstPtr& msgRGB,
                  const sensor_msgs::ImageConstPtr& msgD)
    {
        std::lock_guard<std::mutex> lock(mBufMutex);
        while (!mFrameBuf.empty()) mFrameBuf.pop();   // drop backlog
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
        auto last_map_wall = std::chrono::steady_clock::now() - std::chrono::seconds(1);
        while (true)
        {
            ImageFrame frame;
            bool got_frame = false;
            {
                std::unique_lock<std::mutex> lock(mBufMutex);
                mBufCv.wait_for(lock, std::chrono::milliseconds(100),
                                [this]{ return !mFrameBuf.empty() || !mRunning; });
                if (!mRunning && mFrameBuf.empty()) break;
                if (!mFrameBuf.empty())
                {
                    frame = mFrameBuf.front();
                    mFrameBuf.pop();
                    got_frame = true;
                }
            }

            ros::Time stamp = got_frame ? frame.rgb->header.stamp : ros::Time::now();

            if (got_frame)
            {
                cv_bridge::CvImageConstPtr cv_rgb, cv_depth;
                try { cv_rgb   = cv_bridge::toCvShare(frame.rgb); }
                catch (cv_bridge::Exception& e)
                { ROS_ERROR("cv_bridge RGB exception: %s", e.what()); continue; }
                try { cv_depth = cv_bridge::toCvShare(frame.depth); }
                catch (cv_bridge::Exception& e)
                { ROS_ERROR("cv_bridge depth exception: %s", e.what()); continue; }

                Sophus::SE3f Tcw = mpSLAM->TrackRGBD(cv_rgb->image, cv_depth->image,
                                                       stamp.toSec());

                if (mpSLAM->GetTrackingState() == 2 && finitePose(Tcw))
                {
                    pose_pub.publish(poseFromTcw(Tcw, stamp));
                }
            }

            // Publish the latest optimized keyframe path/map on a wall-clock
            // timer, independent of whether the current frame tracked. This
            // keeps RViz showing the last known (loop-closed) trajectory
            // through a brief tracking loss instead of freezing/going stale,
            // and reflects new keyframes/corrections as soon as tracking
            // recovers — instead of only publishing while state == OK.
            auto now_wall = std::chrono::steady_clock::now();
            if (std::chrono::duration<double>(now_wall - last_map_wall).count() >= 0.5)
            {
                last_map_wall = now_wall;
                sensor_msgs::PointCloud cloud;
                cloud.header.stamp    = stamp;
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
    ros::Publisher          pose_pub;
    ros::Publisher          map_pub;
    ros::Publisher          keyframe_path_pub;

    std::queue<ImageFrame>  mFrameBuf;
    std::mutex              mBufMutex;
    std::condition_variable mBufCv;
    bool                    mRunning;
};

// ── main ──────────────────────────────────────────────────────────────────────
int main(int argc, char **argv)
{
    ros::init(argc, argv, "RGBD");
    ros::start();

    if(argc != 3)
    {
        cerr << endl << "Usage: rosrun ORB_SLAM3 RGBD path_to_vocabulary path_to_settings" << endl;
        ros::shutdown();
        return 1;
    }

    // Create SLAM system. It initializes all system threads and gets ready to process frames.
    ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::RGBD,false);

    ros::NodeHandle nh;
    ImageGrabber igb(&SLAM, nh);

    // Processing thread runs TrackRGBD() — never blocks ROS callbacks.
    std::thread processingThread(&ImageGrabber::ProcessFrames, &igb);

    message_filters::Subscriber<sensor_msgs::Image> rgb_sub(nh, "/camera/rgb/image_raw", 1);
    message_filters::Subscriber<sensor_msgs::Image> depth_sub(nh, "camera/depth_registered/image_raw", 1);
    typedef message_filters::sync_policies::ApproximateTime<sensor_msgs::Image, sensor_msgs::Image> sync_pol;
    message_filters::Synchronizer<sync_pol> sync(sync_pol(10), rgb_sub,depth_sub);
    sync.registerCallback(boost::bind(&ImageGrabber::GrabRGBD,&igb,_1,_2));

    ros::spin();

    igb.Stop();
    processingThread.join();

    // Stop all threads
    SLAM.Shutdown();

    // Save camera trajectory
    SLAM.SaveKeyFrameTrajectoryTUM("KeyFrameTrajectory.txt");

    ros::shutdown();

    return 0;
}
'''
path.write_text(source)
print(f"[add_orbslam3_pose_publishers] rewrote {path} with producer-consumer threading")

# The pinned System API does not expose its Atlas, although the Atlas owns the
# optimized sparse map. Add a read-only accessor used only by the ROS example.
system_header = root / "include/System.h"
system_text = system_header.read_text()
accessor = "    Atlas* GetAtlas() { return mpAtlas; }\n\n"
if "GetAtlas()" not in system_text:
    marker = "\nprivate:\n"
    if marker not in system_text:
        raise RuntimeError("ORB-SLAM3 System private section not found")
    system_text = system_text.replace(marker, "\n" + accessor + "private:\n", 1)
    system_header.write_text(system_text)
