#!/usr/bin/env python3
"""Install lossless native monocular frontends with trajectory publishers."""
import os
from pathlib import Path

path = Path(os.environ.get("ORB_SLAM3_ROOT", "/root/ORB_SLAM3")) / \
       "Examples_old/ROS/ORB_SLAM3/src/ros_mono_inertial.cc"
source = r'''#include <chrono>
#include <condition_variable>
#include <cstdlib>
#include <iostream>
#include <mutex>
#include <queue>
#include <thread>

#include <Eigen/Geometry>
#include <cv_bridge/cv_bridge.h>
#include <geometry_msgs/PoseStamped.h>
#include <ros/ros.h>
#include <sensor_msgs/Image.h>
#include <sensor_msgs/Imu.h>
#include <sensor_msgs/image_encodings.h>

#include "../../../include/System.h"
#include "../include/ImuTypes.h"

using namespace std;

class ImuGrabber
{
public:
    ImuGrabber() : running(true) {}

    void GrabImu(const sensor_msgs::ImuConstPtr& msg)
    {
        {
            lock_guard<mutex> lock(buffer_mutex);
            if (!running) return;
            buffer.push(msg);
        }
        buffer_cv.notify_all();
    }

    bool WaitAndDrainUpTo(double image_time,
                          vector<ORB_SLAM3::IMU::Point>& measurements)
    {
        unique_lock<mutex> lock(buffer_mutex);
        buffer_cv.wait(lock, [this, image_time] {
            return !running ||
                   (!buffer.empty() &&
                    buffer.back()->header.stamp.toSec() >= image_time);
        });
        if (buffer.empty() ||
            buffer.back()->header.stamp.toSec() < image_time)
            return false;
        while (!buffer.empty() &&
               buffer.front()->header.stamp.toSec() <= image_time)
        {
            const auto& msg = buffer.front();
            measurements.emplace_back(
                cv::Point3f(msg->linear_acceleration.x,
                            msg->linear_acceleration.y,
                            msg->linear_acceleration.z),
                cv::Point3f(msg->angular_velocity.x,
                            msg->angular_velocity.y,
                            msg->angular_velocity.z),
                msg->header.stamp.toSec());
            buffer.pop();
        }
        return true;
    }

    void Stop()
    {
        {
            lock_guard<mutex> lock(buffer_mutex);
            running = false;
        }
        buffer_cv.notify_all();
    }

private:
    queue<sensor_msgs::ImuConstPtr> buffer;
    mutex buffer_mutex;
    condition_variable buffer_cv;
    bool running;
};

class ImageGrabber
{
public:
    ImageGrabber(ORB_SLAM3::System* slam, ImuGrabber* imu,
                 ros::NodeHandle& node)
        : slam_(slam), imu_(imu), running_(true)
    {
        pose_pub_ = node.advertise<geometry_msgs::PoseStamped>(
            "/orb_slam3/camera_pose", 20);
    }

    void GrabImage(const sensor_msgs::ImageConstPtr& msg)
    {
        {
            lock_guard<mutex> lock(buffer_mutex_);
            if (!running_) return;
            buffer_.push(msg);
        }
        buffer_cv_.notify_one();
    }

    void ProcessImages()
    {
        while (true)
        {
            sensor_msgs::ImageConstPtr msg;
            {
                unique_lock<mutex> lock(buffer_mutex_);
                buffer_cv_.wait(lock, [this] {
                    return !buffer_.empty() || !running_;
                });
                if (!running_ && buffer_.empty()) break;
                msg = buffer_.front();
                buffer_.pop();
            }

            const double image_time = msg->header.stamp.toSec();
            vector<ORB_SLAM3::IMU::Point> measurements;
            if (!imu_->WaitAndDrainUpTo(image_time, measurements))
                continue;

            cv_bridge::CvImageConstPtr image;
            try
            {
                image = cv_bridge::toCvShare(
                    msg, sensor_msgs::image_encodings::MONO8);
            }
            catch (cv_bridge::Exception& error)
            {
                ROS_ERROR("cv_bridge exception: %s", error.what());
                continue;
            }

            Sophus::SE3f Tcw = slam_->TrackMonocular(
                image->image, image_time, measurements);
            if (slam_->GetTrackingState() != 2 ||
                !Tcw.matrix().allFinite())
                continue;

            const Eigen::Matrix3f Rwc =
                Tcw.rotationMatrix().transpose();
            const Eigen::Vector3f twc = -Rwc * Tcw.translation();
            Eigen::Quaternionf quaternion(Rwc);
            quaternion.normalize();
            geometry_msgs::PoseStamped pose;
            pose.header = msg->header;
            pose.header.frame_id = "orbslam3_map";
            pose.pose.position.x = twc.x();
            pose.pose.position.y = twc.y();
            pose.pose.position.z = twc.z();
            pose.pose.orientation.x = quaternion.x();
            pose.pose.orientation.y = quaternion.y();
            pose.pose.orientation.z = quaternion.z();
            pose.pose.orientation.w = quaternion.w();
            pose_pub_.publish(pose);
        }
    }

    void Stop()
    {
        {
            lock_guard<mutex> lock(buffer_mutex_);
            running_ = false;
        }
        buffer_cv_.notify_all();
    }

private:
    ORB_SLAM3::System* slam_;
    ImuGrabber* imu_;
    ros::Publisher pose_pub_;
    queue<sensor_msgs::ImageConstPtr> buffer_;
    mutex buffer_mutex_;
    condition_variable buffer_cv_;
    bool running_;
};

int main(int argc, char** argv)
{
    ros::init(argc, argv, "Mono_Inertial");
    ros::start();
    if (argc != 3)
    {
        cerr << "Usage: rosrun ORB_SLAM3 Mono_Inertial "
                "path_to_vocabulary path_to_settings\n";
        ros::shutdown();
        return 1;
    }

    ORB_SLAM3::System SLAM(
        argv[1], argv[2], ORB_SLAM3::System::IMU_MONOCULAR, false);
    ros::NodeHandle node;
    ImuGrabber imu;
    ImageGrabber images(&SLAM, &imu, node);
    thread processing(&ImageGrabber::ProcessImages, &images);
    ros::Subscriber image_sub = node.subscribe(
        "/camera/image_raw", 100, &ImageGrabber::GrabImage, &images);
    ros::Subscriber imu_sub = node.subscribe(
        "/imu", 1000, &ImuGrabber::GrabImu, &imu);

    ros::spin();
    images.Stop();
    imu.Stop();
    processing.join();
    SLAM.Shutdown();
    const char* trajectory_env =
        std::getenv("ORB_SLAM3_TRAJECTORY_FILE");
    const string trajectory_file =
        trajectory_env ? trajectory_env : "CameraTrajectory.txt";
    SLAM.SaveTrajectoryEuRoC(trajectory_file);
    ros::shutdown();
    return 0;
}
'''
path.write_text(source, encoding="utf-8")

# The pure-monocular executable is a legitimate fallback for sequences whose
# inertial initialization is unobservable or unstable. Its trajectory remains
# scale-unobservable and must therefore be evaluated with Sim(3), never SE(3).
mono_path = Path(os.environ.get("ORB_SLAM3_ROOT", "/root/ORB_SLAM3")) / \
            "Examples_old/ROS/ORB_SLAM3/src/ros_mono.cc"
mono = mono_path.read_text(encoding="utf-8")
if 'advertise<geometry_msgs::PoseStamped>("/orb_slam3/camera_pose"' not in mono:
    mono = mono.replace("#include <cv_bridge/cv_bridge.h>", """#include <cv_bridge/cv_bridge.h>
#include <cstdlib>
#include <geometry_msgs/PoseStamped.h>
#include <Eigen/Geometry>""")
    mono = mono.replace("using namespace std;", r'''using namespace std;

static ros::Publisher gPosePub;

static void publishPose(const Sophus::SE3f& Tcw, double timestamp)
{
    if (!Tcw.matrix().allFinite()) return;
    const Eigen::Matrix3f Rwc = Tcw.rotationMatrix().transpose();
    const Eigen::Vector3f twc = -Rwc * Tcw.translation();
    Eigen::Quaternionf q(Rwc); q.normalize();
    geometry_msgs::PoseStamped pose;
    pose.header.stamp = ros::Time(timestamp);
    pose.header.frame_id = "orbslam3_map";
    pose.pose.position.x = twc.x(); pose.pose.position.y = twc.y(); pose.pose.position.z = twc.z();
    pose.pose.orientation.x = q.x(); pose.pose.orientation.y = q.y();
    pose.pose.orientation.z = q.z(); pose.pose.orientation.w = q.w();
    gPosePub.publish(pose);
}''')
    mono = mono.replace(
        "ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::MONOCULAR,true);",
        "ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::MONOCULAR,false);")
    mono = mono.replace(
        "ros::NodeHandle nodeHandler;",
        'ros::NodeHandle nodeHandler;\n    gPosePub = nodeHandler.advertise<geometry_msgs::PoseStamped>("/orb_slam3/camera_pose", 20);')
    mono_needle = "mpSLAM->TrackMonocular(cv_ptr->image,cv_ptr->header.stamp.toSec());"
    if mono_needle not in mono:
        raise RuntimeError("pinned ros_mono.cc no longer matches the patch")
    mono = mono.replace(
        mono_needle,
        "Sophus::SE3f Tcw = mpSLAM->TrackMonocular(cv_ptr->image,cv_ptr->header.stamp.toSec());\n"
        "    if (mpSLAM->GetTrackingState() == 2) publishPose(Tcw, cv_ptr->header.stamp.toSec());")
    trajectory_needle = 'SLAM.SaveKeyFrameTrajectoryTUM("KeyFrameTrajectory.txt");'
    if trajectory_needle not in mono:
        raise RuntimeError("pinned ros_mono.cc trajectory export no longer matches the patch")
    mono = mono.replace(
        trajectory_needle,
        """const char* trajectory_env = std::getenv("ORB_SLAM3_TRAJECTORY_FILE");
    const std::string trajectory_file =
        trajectory_env ? trajectory_env : "CameraTrajectory.txt";
    // SaveTrajectoryEuRoC supports monocular mode and reconstructs every
    // tracked frame from its finalized optimized reference keyframe.
    SLAM.SaveTrajectoryEuRoC(trajectory_file);""")
    mono_path.write_text(mono, encoding="utf-8")
