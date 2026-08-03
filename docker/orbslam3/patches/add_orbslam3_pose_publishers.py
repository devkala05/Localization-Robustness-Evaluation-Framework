#!/usr/bin/env python3
"""Add read-only pose and sparse-map outputs to the native RGB-D example.

The ROS example interface is made lossless and two sparse-RGBD integration
rules are applied to the pinned native tracker: a bounded keyframe cadence and
correct lost-frame bookkeeping. Optimization, loop closure, place recognition,
feature extraction, and pose math remain native.

Design: producer-consumer threading, matching add_rgbd_inertial.py. The ROS
sync callback (GrabRGBD) enqueues frames and returns immediately; a dedicated
processing thread calls TrackRGBD(). Every synchronized frame is retained.
Dropping frames during local mapping breaks feature continuity on fast public
drives, so playback is slowed enough to keep this lossless queue bounded.

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
 * It enqueues each frame and returns immediately. A separate thread drains
 * the frame queue and calls TrackRGBD() in timestamp order.
 *
 * The example provides lossless delivery, a configured camera ROI, and
 * read-only pose/map/path publishing. Native feature matching, optimisation,
 * map geometry, and loop closure are retained.
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
#include <stdexcept>

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
        : mpSLAM(pSLAM), mRunning(true),
          mMaskTopFraction(0.0), mMaskBottomFraction(0.0)
    {
        nh.param<double>("mask_top_fraction", mMaskTopFraction, 0.0);
        nh.param<double>("mask_bottom_fraction", mMaskBottomFraction, 0.0);
        mMaskTopFraction = std::max(0.0, std::min(0.9, mMaskTopFraction));
        mMaskBottomFraction = std::max(0.0, std::min(0.9, mMaskBottomFraction));
        if (mMaskTopFraction + mMaskBottomFraction >= 0.95)
            throw std::runtime_error("ORB camera ROI masks leave no usable image");
        ROS_INFO("ORB camera ROI mask: top=%.3f bottom=%.3f",
                 mMaskTopFraction, mMaskBottomFraction);
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

                cv::Mat rgb = cv_rgb->image;
                cv::Mat depth = cv_depth->image;
                if (mMaskTopFraction > 0.0 || mMaskBottomFraction > 0.0)
                {
                    rgb = rgb.clone();
                    depth = depth.clone();
                    const int top = static_cast<int>(rgb.rows * mMaskTopFraction);
                    const int bottom = static_cast<int>(rgb.rows * mMaskBottomFraction);
                    if (top > 0)
                    {
                        rgb.rowRange(0, top).setTo(cv::Scalar::all(0));
                        depth.rowRange(0, top).setTo(cv::Scalar::all(0));
                    }
                    if (bottom > 0)
                    {
                        rgb.rowRange(rgb.rows - bottom, rgb.rows).setTo(cv::Scalar::all(0));
                        depth.rowRange(depth.rows - bottom, depth.rows).setTo(cv::Scalar::all(0));
                    }
                }

                Sophus::SE3f Tcw = mpSLAM->TrackRGBD(rgb, depth,
                                                       stamp.toSec());

                const int tracking_state = mpSLAM->GetTrackingState();
                if (tracking_state == 2 && finitePose(Tcw))
                {
                    pose_pub.publish(poseFromTcw(Tcw, stamp));
                }
                else
                {
                    ROS_WARN("ORB RGB-D frame %.6f not published: state=%d finite=%d",
                             stamp.toSec(), tracking_state, finitePose(Tcw));
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
    double                  mMaskTopFraction;
    double                  mMaskBottomFraction;
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

    // Keep transport queues larger than the synchronizer queue. Difficult
    // high-resolution frames can briefly take longer than one input period;
    // a queue of one silently dropped the next RGB/depth pair before it ever
    // reached the lossless processing queue above.
    message_filters::Subscriber<sensor_msgs::Image> rgb_sub(nh, "/camera/rgb/image_raw", 100);
    message_filters::Subscriber<sensor_msgs::Image> depth_sub(nh, "camera/depth_registered/image_raw", 100);
    typedef message_filters::sync_policies::ApproximateTime<sensor_msgs::Image, sensor_msgs::Image> sync_pol;
    message_filters::Synchronizer<sync_pol> sync(sync_pol(100), rgb_sub,depth_sub);
    sync.registerCallback(boost::bind(&ImageGrabber::GrabRGBD,&igb,_1,_2));

    ros::spin();

    igb.Stop();
    processingThread.join();

    // Stop all threads
    SLAM.Shutdown();

    // Save ORB-SLAM3's native finalized all-frame trajectory. System rebuilds
    // every tracked frame from its optimized reference keyframe, so this is
    // the correct post-loop-closure RGB-D result rather than a live-map trace
    // or a sparse keyframe-only approximation.
    const char* trajectory_env = std::getenv("ORB_SLAM3_TRAJECTORY_FILE");
    const std::string trajectory_file =
        trajectory_env ? trajectory_env : "CameraTrajectory.txt";
    SLAM.SaveTrajectoryTUM(trajectory_file);

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

# Plain RGBD and stereo share a 30-inlier local-map gate upstream. A projected
# lidar depth image is intentionally sparse, and ORB's own motion-model and
# RECENTLY_LOST recovery paths use 10 map-point inliers. Apply that internally
# consistent floor to RGBD only. Matching, optimization, and outlier rejection
# are unchanged.
tracking_path = root / "src/Tracking.cc"
tracking = tracking_path.read_text()
gate = """    else
    {
        if(mnMatchesInliers<30)
            return false;
        else
            return true;
    }"""
replacement = """    else
    {
        const int minInliers = (mSensor == System::RGBD) ? 15 : 30;
        if(mnMatchesInliers<minInliers)
            return false;
        else
            return true;
    }"""
if gate in tracking:
    tracking = tracking.replace(gate, replacement, 1)
elif "const int minInliers = (mSensor == System::RGBD) ? 15 : 30;" not in tracking:
    raise RuntimeError("pinned Tracking.cc RGBD local-map gate no longer matches")

# ORB's RGB-D keyframe policy assumes a dense depth camera. Boreas instead
# supplies sparse calibrated LiDAR returns which are locally rasterized at
# visual keypoints. Counting every unsupported rasterized point as a close
# RGB-D opportunity forces nearly every 10 Hz image to become a keyframe and
# eventually starves tracking while local mapping catches up. Disable only
# that dense-depth insertion trigger for plain RGBD; the ordinary temporal,
# weak-tracking, mapper-idle, and reference-ratio criteria remain active, and
# all measured depths remain available when a normal keyframe is inserted.
close_gate = """    bNeedToInsertClose = (nTrackedClose<100) && (nNonTrackedClose>70);"""
close_replacement = """    bNeedToInsertClose = (mSensor != System::RGBD) &&
                         (nTrackedClose<100) && (nNonTrackedClose>70);"""
if close_gate in tracking:
    tracking = tracking.replace(close_gate, close_replacement, 1)
elif "bNeedToInsertClose = (mSensor != System::RGBD)" not in tracking:
    raise RuntimeError("pinned Tracking.cc RGBD close-point gate no longer matches")

# The dense-depth trigger above cannot be used with rasterized LiDAR depth: it
# requests keyframes at almost every image and overwhelms LocalMapping. The
# remaining upstream policy, however, combines its one-second c1a timer with a
# weak-tracking ratio, so a long, strongly tracked drive can go too long without
# a fresh place-recognition/keyframe anchor. At highway speed that makes a brief
# projection failure unrecoverable after a long pre-roll. For plain sparse
# RGBD, guarantee at most the configured mMaxFrames interval (10 frames in the
# Boreas camera config), but only while LocalMapping is idle. This is bounded at
# 1 Hz and does not change any pose, match, optimizer, or outlier decision.
keyframe_decision = """    if(((c1a||c1b||c1c) && c2)||c3 ||c4)
    {"""
keyframe_replacement = """    const bool sparseRGBDPeriodic =
        (mSensor == System::RGBD) && c1a && bLocalMappingIdle;

    if(((c1a||c1b||c1c) && c2)||c3 ||c4 || sparseRGBDPeriodic)
    {"""
if keyframe_decision in tracking:
    tracking = tracking.replace(keyframe_decision, keyframe_replacement, 1)
elif "sparseRGBDPeriodic" not in tracking:
    raise RuntimeError("pinned Tracking.cc keyframe decision no longer matches")

# ORB-SLAM3 keeps a placeholder relative pose while RECENTLY_LOST. Upstream
# repeats the prior timestamp in this branch but marks it lost only when the
# state has already advanced to LOST. SaveTrajectoryTUM therefore emits several
# duplicate timestamps during a normal short relocalization. Mark an unset
# current frame as lost so the native saver omits it, as its own contract says.
# The live ROS publisher already follows this same current-pose validity rule.
lost_bookkeeping = """            mlFrameTimes.push_back(mlFrameTimes.back());
            mlbLost.push_back(mState==LOST);"""
lost_replacement = """            mlFrameTimes.push_back(mCurrentFrame.mTimeStamp);
            mlbLost.push_back(true);"""
if lost_bookkeeping in tracking:
    tracking = tracking.replace(lost_bookkeeping, lost_replacement, 1)
elif "mlFrameTimes.push_back(mCurrentFrame.mTimeStamp);\n            mlbLost.push_back(true);" not in tracking:
    raise RuntimeError("pinned Tracking.cc lost-frame bookkeeping no longer matches")

# Preserve the native failure decision, but include the already-computed local
# map inlier count in its diagnostic. This makes sparse-depth failures
# actionable without reading GT or changing the returned tracking state.
plain_failure = 'cout << "Fail to track local map!" << endl;'
diagnostic_failure = '''cout << "Fail to track local map! frame="
                     << mCurrentFrame.mnId << " inliers="
                     << mnMatchesInliers << " state=" << mState << endl;'''
if plain_failure in tracking:
    tracking = tracking.replace(plain_failure, diagnostic_failure, 1)
elif "inliers=" not in tracking or "mCurrentFrame.mnId" not in tracking:
    raise RuntimeError("pinned Tracking.cc local-map diagnostic no longer matches")

tracking_path.write_text(tracking)
