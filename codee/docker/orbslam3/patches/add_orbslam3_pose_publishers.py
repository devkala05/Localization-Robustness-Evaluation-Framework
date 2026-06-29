#!/usr/bin/env python3
"""Add read-only pose and sparse-map outputs to the native monocular example.

Only the example interface is changed. Tracking, map management, optimization,
loop closure, place recognition, and feature extraction are untouched.
"""
import os
from pathlib import Path

root = Path(os.environ.get("ORB_SLAM3_ROOT", "/root/ORB_SLAM3"))
path = root / "Examples_old/ROS/ORB_SLAM3/src/ros_mono.cc"
text = path.read_text()
if "/orb_slam3/camera_pose" in text and "/orb_slam3/map_points" in text:
    raise SystemExit(0)
helper = r'''
#include <geometry_msgs/PoseStamped.h>
#include <geometry_msgs/Point32.h>
#include <sensor_msgs/PointCloud.h>
#include <nav_msgs/Path.h>
#include <Eigen/Geometry>
#include <sophus/se3.hpp>
#include "Atlas.h"
#include "Map.h"
#include "MapPoint.h"
#include "KeyFrame.h"
#include <algorithm>
#include <cmath>

static bool finitePose(const Sophus::SE3f& Tcw)
{
    return Tcw.matrix().allFinite();
}

static geometry_msgs::PoseStamped poseFromTcw(const Sophus::SE3f& Tcw, const ros::Time& stamp)
{
    const Eigen::Matrix3f Rcw = Tcw.rotationMatrix();
    const Eigen::Vector3f tcw = Tcw.translation();
    const Eigen::Matrix3f Rwc = Rcw.transpose();
    const Eigen::Vector3f twc = -Rwc * tcw;
    Eigen::Quaternionf q(Rwc);
    q.normalize();
    geometry_msgs::PoseStamped pose;
    pose.header.stamp = stamp;
    pose.header.frame_id = "orbslam3_map";
    pose.pose.position.x = twc.x();
    pose.pose.position.y = twc.y();
    pose.pose.position.z = twc.z();
    pose.pose.orientation.x = q.x();
    pose.pose.orientation.y = q.y();
    pose.pose.orientation.z = q.z();
    pose.pose.orientation.w = q.w();
    return pose;
}
'''
for include in ("#include <cv_bridge/cv_bridge.h>\n", "#include<cv_bridge/cv_bridge.h>\n"):
    if include in text:
        text = text.replace(include, include + helper, 1)
        break
else:
    raise RuntimeError("cv_bridge include not found")
replacements = [
    (
        "    ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::MONOCULAR,true);\n",
        "    ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::MONOCULAR,false);\n",
    ),
    (
        "    ImageGrabber(ORB_SLAM3::System* pSLAM):mpSLAM(pSLAM){}\n",
        "    ImageGrabber(ORB_SLAM3::System* pSLAM, ros::NodeHandle& nh):mpSLAM(pSLAM)\n"
        "    { pose_pub = nh.advertise<geometry_msgs::PoseStamped>(\"/orb_slam3/camera_pose\", 10);\n"
        "      map_pub = nh.advertise<sensor_msgs::PointCloud>(\"/orb_slam3/map_points\", 2);\n"
        "      keyframe_path_pub = nh.advertise<nav_msgs::Path>(\"/orb_slam3/keyframe_path\", 2, true); }\n",
    ),
    ("    ORB_SLAM3::System* mpSLAM;\n",
     "    ORB_SLAM3::System* mpSLAM;\n    ros::Publisher pose_pub;\n    ros::Publisher map_pub;\n    ros::Publisher keyframe_path_pub;\n"),
    ("    ImageGrabber igb(&SLAM);\n\n    ros::NodeHandle nodeHandler;\n",
     "    ros::NodeHandle nodeHandler;\n    ImageGrabber igb(&SLAM, nodeHandler);\n\n"),
    ("    mpSLAM->TrackMonocular(cv_ptr->image,cv_ptr->header.stamp.toSec());\n",
     "    Sophus::SE3f Tcw = mpSLAM->TrackMonocular(cv_ptr->image,cv_ptr->header.stamp.toSec());\n"
     "    if (mpSLAM->GetTrackingState() == 2 && finitePose(Tcw))\n"
     "    {\n"
     "        pose_pub.publish(poseFromTcw(Tcw, cv_ptr->header.stamp));\n"
     "        static double last_map_publish_time = -1.0;\n"
     "        const double map_publish_time = cv_ptr->header.stamp.toSec();\n"
     "        if (last_map_publish_time < 0.0 || map_publish_time - last_map_publish_time >= 0.5)\n"
     "        {\n"
     "        last_map_publish_time = map_publish_time;\n"
     "        sensor_msgs::PointCloud cloud;\n"
     "        cloud.header.stamp = cv_ptr->header.stamp;\n"
     "        cloud.header.frame_id = \"orbslam3_map\";\n"
     "        ORB_SLAM3::Map* current_map = mpSLAM->GetAtlas()->GetCurrentMap();\n"
     "        const std::vector<ORB_SLAM3::MapPoint*> points = current_map\n"
     "            ? current_map->GetAllMapPoints() : std::vector<ORB_SLAM3::MapPoint*>();\n"
     "        cloud.points.reserve(points.size());\n"
     "        for (ORB_SLAM3::MapPoint* point : points)\n"
     "        {\n"
     "            if (!point || point->isBad()) continue;\n"
     "            const Eigen::Vector3f position = point->GetWorldPos();\n"
     "            if (!position.allFinite()) continue;\n"
     "            geometry_msgs::Point32 output;\n"
     "            output.x = position.x(); output.y = position.y(); output.z = position.z();\n"
     "            cloud.points.push_back(output);\n"
     "        }\n"
     "        map_pub.publish(cloud);\n"
     "        nav_msgs::Path keyframe_path;\n"
     "        keyframe_path.header = cloud.header;\n"
     "        std::vector<ORB_SLAM3::KeyFrame*> keyframes = current_map\n"
     "            ? current_map->GetAllKeyFrames() : std::vector<ORB_SLAM3::KeyFrame*>();\n"
     "        std::sort(keyframes.begin(), keyframes.end(),\n"
     "            [](const ORB_SLAM3::KeyFrame* a, const ORB_SLAM3::KeyFrame* b)\n"
     "            { return a->mnId < b->mnId; });\n"
     "        for (ORB_SLAM3::KeyFrame* keyframe : keyframes)\n"
     "        {\n"
     "            if (!keyframe || keyframe->isBad()) continue;\n"
     "            keyframe_path.poses.push_back(poseFromTcw(keyframe->GetPose(), cv_ptr->header.stamp));\n"
     "        }\n"
     "        keyframe_path_pub.publish(keyframe_path);\n"
     "        }\n"
     "    }\n"),
]
for old, new in replacements:
    if old not in text:
        raise RuntimeError(f"ORB-SLAM3 source pattern not found: {old[:80]!r}")
    text = text.replace(old, new, 1)
path.write_text(text)

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
