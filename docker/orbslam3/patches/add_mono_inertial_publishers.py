#!/usr/bin/env python3
"""Add PoseStamped publishers to the pinned native monocular examples."""
import os
from pathlib import Path

path = Path(os.environ.get("ORB_SLAM3_ROOT", "/root/ORB_SLAM3")) / \
       "Examples_old/ROS/ORB_SLAM3/src/ros_mono_inertial.cc"
text = path.read_text(encoding="utf-8")
if 'advertise<geometry_msgs::PoseStamped>("/orb_slam3/camera_pose"' in text:
    raise SystemExit(0)
text = text.replace("#include<sensor_msgs/Imu.h>", """#include<sensor_msgs/Imu.h>
#include<geometry_msgs/PoseStamped.h>
#include<Eigen/Geometry>""")
text = text.replace("using namespace std;", r'''using namespace std;

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
text = text.replace('ros::console::set_logger_level(ROSCONSOLE_DEFAULT_NAME, ros::console::levels::Info);',
                    'ros::console::set_logger_level(ROSCONSOLE_DEFAULT_NAME, ros::console::levels::Info);\n  gPosePub = n.advertise<geometry_msgs::PoseStamped>("/orb_slam3/camera_pose", 20);')
viewer_ctor = 'ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::IMU_MONOCULAR,true);'
if viewer_ctor not in text:
    raise RuntimeError("pinned mono-inertial viewer constructor no longer matches")
text = text.replace(viewer_ctor,
                    'ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::IMU_MONOCULAR,false);')
needle = "mpSLAM->TrackMonocular(im,tIm,vImuMeas);"
replacement = "Sophus::SE3f Tcw = mpSLAM->TrackMonocular(im,tIm,vImuMeas);\n      if (mpSLAM->GetTrackingState() == 2) publishPose(Tcw, tIm);"
if needle not in text:
    raise RuntimeError("pinned ros_mono_inertial.cc no longer matches the patch")
path.write_text(text.replace(needle, replacement), encoding="utf-8")

# The pure-monocular executable is a legitimate fallback for sequences whose
# inertial initialization is unobservable or unstable. Its trajectory remains
# scale-unobservable and must therefore be evaluated with Sim(3), never SE(3).
mono_path = Path(os.environ.get("ORB_SLAM3_ROOT", "/root/ORB_SLAM3")) / \
            "Examples_old/ROS/ORB_SLAM3/src/ros_mono.cc"
mono = mono_path.read_text(encoding="utf-8")
if 'advertise<geometry_msgs::PoseStamped>("/orb_slam3/camera_pose"' not in mono:
    mono = mono.replace("#include <cv_bridge/cv_bridge.h>", """#include <cv_bridge/cv_bridge.h>
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
    mono_path.write_text(mono, encoding="utf-8")
