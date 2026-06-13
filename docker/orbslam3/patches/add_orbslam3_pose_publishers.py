#!/usr/bin/env python3
from pathlib import Path


ROOT = Path("/root/ORB_SLAM3/Examples_old/ROS/ORB_SLAM3/src")
MONO = ROOT / "ros_mono.cc"
STEREO = ROOT / "ros_stereo.cc"

HELPER = r'''
#include <geometry_msgs/PoseStamped.h>
#include <Eigen/Geometry>
#include <sophus/se3.hpp>
#include <cmath>

static bool isFiniteTcw(const Sophus::SE3f& Tcw)
{
    const Eigen::Matrix3f Rcw = Tcw.rotationMatrix();
    const Eigen::Vector3f tcw = Tcw.translation();
    for (int r = 0; r < 3; ++r)
        for (int c = 0; c < 3; ++c)
            if (!std::isfinite(Rcw(r, c))) return false;
    for (int i = 0; i < 3; ++i)
        if (!std::isfinite(tcw(i))) return false;
    return true;
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
    pose.header.frame_id = "camera_init";
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


def replace_once(text: str, old: str, new: str, path: Path) -> str:
    if old not in text:
        raise RuntimeError(f"Pattern not found in {path}: {old[:80]!r}")
    return text.replace(old, new, 1)


def patch_mono():
    text = MONO.read_text()
    if "/orb_slam3/camera_pose" in text:
        print(f"{MONO}: already patched")
        return

    text = replace_once(text, '#include <cv_bridge/cv_bridge.h>\n', '#include <cv_bridge/cv_bridge.h>\n' + HELPER, MONO)
    text = replace_once(
        text,
        '    ImageGrabber(ORB_SLAM3::System* pSLAM):mpSLAM(pSLAM){}\n',
        '    ImageGrabber(ORB_SLAM3::System* pSLAM, ros::NodeHandle& nh):mpSLAM(pSLAM)\n'
        '    {\n'
        '        pose_pub = nh.advertise<geometry_msgs::PoseStamped>("/orb_slam3/camera_pose", 10);\n'
        '    }\n',
        MONO,
    )
    text = replace_once(
        text,
        '    ORB_SLAM3::System* mpSLAM;\n',
        '    ORB_SLAM3::System* mpSLAM;\n'
        '    ros::Publisher pose_pub;\n',
        MONO,
    )
    text = replace_once(
        text,
        '    ImageGrabber igb(&SLAM);\n\n'
        '    ros::NodeHandle nodeHandler;\n',
        '    ros::NodeHandle nodeHandler;\n'
        '    ImageGrabber igb(&SLAM, nodeHandler);\n\n',
        MONO,
    )
    text = replace_once(
        text,
        '    mpSLAM->TrackMonocular(cv_ptr->image,cv_ptr->header.stamp.toSec());\n',
        '    Sophus::SE3f Tcw = mpSLAM->TrackMonocular(cv_ptr->image,cv_ptr->header.stamp.toSec());\n'
        '    if (mpSLAM->GetTrackingState() == 2 && isFiniteTcw(Tcw))\n        pose_pub.publish(poseFromTcw(Tcw, cv_ptr->header.stamp));\n',
        MONO,
    )
    MONO.write_text(text)
    print(f"{MONO}: patched")


def patch_stereo():
    text = STEREO.read_text()
    if "/orb_slam3/camera_pose" in text:
        print(f"{STEREO}: already patched")
        return

    text = replace_once(text, '#include <cv_bridge/cv_bridge.h>\n', '#include <cv_bridge/cv_bridge.h>\n' + HELPER, STEREO)
    text = replace_once(
        text,
        '    ImageGrabber(ORB_SLAM3::System* pSLAM):mpSLAM(pSLAM){}\n',
        '    ImageGrabber(ORB_SLAM3::System* pSLAM, ros::NodeHandle& nh):mpSLAM(pSLAM)\n'
        '    {\n'
        '        pose_pub = nh.advertise<geometry_msgs::PoseStamped>("/orb_slam3/camera_pose", 10);\n'
        '    }\n',
        STEREO,
    )
    text = replace_once(
        text,
        '    ORB_SLAM3::System* mpSLAM;\n'
        '    bool do_rectify;\n',
        '    ORB_SLAM3::System* mpSLAM;\n'
        '    ros::Publisher pose_pub;\n'
        '    bool do_rectify;\n',
        STEREO,
    )
    text = replace_once(
        text,
        '    ImageGrabber igb(&SLAM);\n\n'
        '    stringstream ss(argv[3]);\n',
        '    ros::NodeHandle nh;\n'
        '    ImageGrabber igb(&SLAM, nh);\n\n'
        '    stringstream ss(argv[3]);\n',
        STEREO,
    )
    text = replace_once(text, '    ros::NodeHandle nh;\n\n    message_filters::Subscriber', '    message_filters::Subscriber', STEREO)
    text = replace_once(
        text,
        '    if(do_rectify)\n'
        '    {\n'
        '        cv::Mat imLeft, imRight;\n'
        '        cv::remap(cv_ptrLeft->image,imLeft,M1l,M2l,cv::INTER_LINEAR);\n'
        '        cv::remap(cv_ptrRight->image,imRight,M1r,M2r,cv::INTER_LINEAR);\n'
        '        mpSLAM->TrackStereo(imLeft,imRight,cv_ptrLeft->header.stamp.toSec());\n'
        '    }\n'
        '    else\n'
        '    {\n'
        '        mpSLAM->TrackStereo(cv_ptrLeft->image,cv_ptrRight->image,cv_ptrLeft->header.stamp.toSec());\n'
        '    }\n',
        '    Sophus::SE3f Tcw;\n'
        '    if(do_rectify)\n'
        '    {\n'
        '        cv::Mat imLeft, imRight;\n'
        '        cv::remap(cv_ptrLeft->image,imLeft,M1l,M2l,cv::INTER_LINEAR);\n'
        '        cv::remap(cv_ptrRight->image,imRight,M1r,M2r,cv::INTER_LINEAR);\n'
        '        Tcw = mpSLAM->TrackStereo(imLeft,imRight,cv_ptrLeft->header.stamp.toSec());\n'
        '    }\n'
        '    else\n'
        '    {\n'
        '        Tcw = mpSLAM->TrackStereo(cv_ptrLeft->image,cv_ptrRight->image,cv_ptrLeft->header.stamp.toSec());\n'
        '    }\n'
        '    if (mpSLAM->GetTrackingState() == 2 && isFiniteTcw(Tcw))\n        pose_pub.publish(poseFromTcw(Tcw, cv_ptrLeft->header.stamp));\n',
        STEREO,
    )
    STEREO.write_text(text)
    print(f"{STEREO}: patched")


def main():
    patch_mono()
    patch_stereo()


if __name__ == "__main__":
    main()
