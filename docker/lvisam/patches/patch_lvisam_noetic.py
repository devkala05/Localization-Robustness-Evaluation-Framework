#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("LVI_SAM_ROOT", "/root/catkin_ws/src/LVI-SAM"))

replacements = {
    "#include <opencv/cv.h>": "#include <opencv2/opencv.hpp>",
    "CV_GRAY2RGB": "cv::COLOR_GRAY2RGB",
    "CV_RGB2GRAY": "cv::COLOR_RGB2GRAY",
    "CV_FONT_HERSHEY_SIMPLEX": "cv::FONT_HERSHEY_SIMPLEX",
}

for path in root.rglob("*"):
    if path.suffix not in {".cpp", ".cc", ".h", ".hpp"}:
        continue
    text = path.read_text()
    original = text
    for old, new in replacements.items():
        text = text.replace(old, new)
    if text != original:
        path.write_text(text)

map_optimization = root / "src/lidar_odometry/mapOptmization.cpp"
text = map_optimization.read_text()
old = '        subGPS                = nh.subscribe<nav_msgs::Odometry>      (gpsTopic,                                   50, &mapOptimization::gpsHandler, this, ros::TransportHints().tcpNoDelay());'
new = '''        if (!gpsTopic.empty())
            subGPS            = nh.subscribe<nav_msgs::Odometry>      (gpsTopic,                                   50, &mapOptimization::gpsHandler, this, ros::TransportHints().tcpNoDelay());'''
if old in text:
    map_optimization.write_text(text.replace(old, new))

# Upstream image projection wires translational deskew only to the VINS
# propagation topic. In lidar-inertial mode those visual nodes do not run, so
# road-speed scans are rotation-deskewed but never translation-deskewed. Use
# the configured native odometry topic (LiDAR IMU preintegration in this mode)
# and enable the interpolation code that upstream ships commented out.
image_projection = root / "src/lidar_odometry/imageProjection.cpp"
text = image_projection.read_text()
old = 'subOdom       = nh.subscribe<nav_msgs::Odometry>      (PROJECT_NAME + "/vins/odometry/imu_propagate_ros", 2000, &ImageProjection::odometryHandler, this, ros::TransportHints().tcpNoDelay());'
new = 'subOdom       = nh.subscribe<nav_msgs::Odometry>      (odomTopic, 2000, &ImageProjection::odometryHandler, this, ros::TransportHints().tcpNoDelay());'
if old in text:
    text = text.replace(old, new)
elif "(odomTopic, 2000, &ImageProjection::odometryHandler" not in text:
    raise RuntimeError("could not patch LVI-SAM deskew odometry topic")
old = """        // if (cloudInfo.odomAvailable == false || odomDeskewFlag == false)
        //     return;

        // float ratio = relTime / (timeScanNext - timeScanCur);

        // *posXCur = ratio * odomIncreX;
        // *posYCur = ratio * odomIncreY;
        // *posZCur = ratio * odomIncreZ;"""
new = """        if (cloudInfo.odomAvailable == false || odomDeskewFlag == false)
            return;

        const double scanDuration = timeScanNext - timeScanCur;
        if (scanDuration <= 0.0)
            return;
        const float ratio = std::max(0.0, std::min(1.0, relTime / scanDuration));

        *posXCur = ratio * odomIncreX;
        *posYCur = ratio * odomIncreY;
        *posZCur = ratio * odomIncreZ;"""
if old in text:
    text = text.replace(old, new)
elif "const double scanDuration = timeScanNext - timeScanCur;" not in text:
    raise RuntimeError("could not enable LVI-SAM translational deskew")
image_projection.write_text(text)

# Upstream treats 30 m/s as estimator failure and repeatedly resets IMU
# preintegration. Boreas legitimately reaches highway speed near this bound,
# so expose the guard as a configuration parameter.
lidar_utility = root / "src/lidar_odometry/utility.h"
text = lidar_utility.read_text()
anchor = "    float imuGravity;"
if anchor in text and "velocityFailureThreshold" not in text:
    text = text.replace(anchor, anchor + "\n    float velocityFailureThreshold;")
anchor = '        nh.param<float>(PROJECT_NAME + "/imuGravity", imuGravity, 9.80511);'
if anchor in text and '"/velocityFailureThreshold"' not in text:
    text = text.replace(
        anchor,
        anchor + '\n        nh.param<float>(PROJECT_NAME + "/velocityFailureThreshold", '
        'velocityFailureThreshold, 30.0);',
    )
if "velocityFailureThreshold" not in text:
    raise RuntimeError("could not add configurable LVI-SAM velocity failure threshold")
lidar_utility.write_text(text)

imu_preintegration = root / "src/lidar_odometry/imuPreintegration.cpp"
text = imu_preintegration.read_text()
old = "        if (vel.norm() > 30)"
new = "        if (vel.norm() > velocityFailureThreshold)"
if old in text:
    text = text.replace(old, new)
elif new not in text:
    raise RuntimeError("could not patch LVI-SAM velocity failure guard")
imu_preintegration.write_text(text)

# Upstream publishes one hard-coded 180-degree camera/LiDAR conversion as both
# the lidar mapper's VINS initial guess and the depth-registration TF. Keep that
# legacy path as the default for existing E2O runs, but allow public-dataset
# configs to provide the actual IMU<-LiDAR calibration. The depth TF then uses
# VINS's already-loaded IMU<-camera calibration, while the mapping odometry uses
# the independently supplied IMU<-LiDAR transform.
parameters_h = root / "src/visual_odometry/visual_estimator/parameters.h"
text = parameters_h.read_text()
anchor = "extern int ALIGN_CAMERA_LIDAR_COORDINATE;"
addition = """extern int ALIGN_CAMERA_LIDAR_COORDINATE;
extern int USE_CALIBRATED_VINS_LIDAR_TRANSFORM;
extern Eigen::Matrix3d R_IMU_LIDAR;
extern Eigen::Vector3d T_IMU_LIDAR;"""
if anchor in text and "USE_CALIBRATED_VINS_LIDAR_TRANSFORM" not in text:
    parameters_h.write_text(text.replace(anchor, addition))

parameters_cpp = root / "src/visual_odometry/visual_estimator/parameters.cpp"
text = parameters_cpp.read_text()
anchor = "int ALIGN_CAMERA_LIDAR_COORDINATE;"
addition = """int ALIGN_CAMERA_LIDAR_COORDINATE;
int USE_CALIBRATED_VINS_LIDAR_TRANSFORM = 0;
Eigen::Matrix3d R_IMU_LIDAR = Eigen::Matrix3d::Identity();
Eigen::Vector3d T_IMU_LIDAR = Eigen::Vector3d::Zero();"""
if anchor in text and "USE_CALIBRATED_VINS_LIDAR_TRANSFORM = 0" not in text:
    text = text.replace(anchor, addition)
anchor = "    fsSettings[\"align_camera_lidar_estimation\"] >> ALIGN_CAMERA_LIDAR_COORDINATE;"
addition = """    fsSettings[\"align_camera_lidar_estimation\"] >> ALIGN_CAMERA_LIDAR_COORDINATE;
    cv::FileNode calibrated_lidar_node = fsSettings[\"use_calibrated_vins_lidar_transform\"];
    if (!calibrated_lidar_node.empty())
        calibrated_lidar_node >> USE_CALIBRATED_VINS_LIDAR_TRANSFORM;
    if (USE_CALIBRATED_VINS_LIDAR_TRANSFORM)
    {
        cv::Mat cv_R_imu_lidar, cv_T_imu_lidar;
        fsSettings[\"vins_lidar_rotation\"] >> cv_R_imu_lidar;
        fsSettings[\"vins_lidar_translation\"] >> cv_T_imu_lidar;
        if (cv_R_imu_lidar.rows != 3 || cv_R_imu_lidar.cols != 3 ||
            cv_T_imu_lidar.rows != 3 || cv_T_imu_lidar.cols != 1)
            throw std::runtime_error(\"invalid calibrated VINS-to-lidar transform\");
        cv::cv2eigen(cv_R_imu_lidar, R_IMU_LIDAR);
        cv::cv2eigen(cv_T_imu_lidar, T_IMU_LIDAR);
        R_IMU_LIDAR = Eigen::Quaterniond(R_IMU_LIDAR).normalized().toRotationMatrix();
    }"""
if anchor in text and "calibrated_lidar_node" not in text:
    text = text.replace(anchor, addition)
parameters_cpp.write_text(text)

visualization = root / "src/visual_odometry/visual_estimator/utility/visualization.cpp"
text = visualization.read_text()
old = """    tf::Quaternion q_odom_cam(Q.x(), Q.y(), Q.z(), Q.w());
    tf::Quaternion q_cam_to_lidar(0, 1, 0, 0); // mark: camera - lidar
    tf::Quaternion q_odom_ros = q_odom_cam * q_cam_to_lidar;
    tf::quaternionTFToMsg(q_odom_ros, odometry.pose.pose.orientation);
    pub_latest_odometry_ros.publish(odometry);

    // TF of camera in vins_world in ROS format (change rotation), used for depth registration
    tf::Transform t_w_body = tf::Transform(q_odom_ros, tf::Vector3(P.x(), P.y(), P.z()));"""
new = """    tf::Quaternion q_odom_cam(Q.x(), Q.y(), Q.z(), Q.w());
    tf::Quaternion q_cam_to_lidar(0, 1, 0, 0); // legacy upstream convention
    tf::Quaternion q_odom_ros = q_odom_cam * q_cam_to_lidar;
    Eigen::Vector3d p_odom_lidar = P;
    tf::Transform t_w_body;
    if (USE_CALIBRATED_VINS_LIDAR_TRANSFORM)
    {
        Eigen::Quaterniond q_odom_imu = Q.normalized();
        Eigen::Quaterniond q_odom_lidar(q_odom_imu * Eigen::Quaterniond(R_IMU_LIDAR));
        p_odom_lidar = P + q_odom_imu * T_IMU_LIDAR;
        q_odom_ros = tf::Quaternion(q_odom_lidar.x(), q_odom_lidar.y(),
                                    q_odom_lidar.z(), q_odom_lidar.w());
        Eigen::Quaterniond q_odom_camera(q_odom_imu * Eigen::Quaterniond(RIC[0]));
        Eigen::Vector3d p_odom_camera = P + q_odom_imu * TIC[0];
        t_w_body = tf::Transform(
            tf::Quaternion(q_odom_camera.x(), q_odom_camera.y(),
                           q_odom_camera.z(), q_odom_camera.w()),
            tf::Vector3(p_odom_camera.x(), p_odom_camera.y(), p_odom_camera.z()));
    }
    else
    {
        t_w_body = tf::Transform(q_odom_ros, tf::Vector3(P.x(), P.y(), P.z()));
    }
    odometry.pose.pose.position.x = p_odom_lidar.x();
    odometry.pose.pose.position.y = p_odom_lidar.y();
    odometry.pose.pose.position.z = p_odom_lidar.z();
    tf::quaternionTFToMsg(q_odom_ros, odometry.pose.pose.orientation);
    pub_latest_odometry_ros.publish(odometry);

    // Calibrated camera TF used for depth registration (legacy default above).
"""
if old in text:
    text = text.replace(old, new)
elif "USE_CALIBRATED_VINS_LIDAR_TRANSFORM" not in text:
    raise RuntimeError("could not patch LVI-SAM VINS/lidar conversion")
visualization.write_text(text)

# The same legacy hard-coded 180-degree conversion is also used when LiDAR
# odometry initializes the VINS state. Parameterizing only the published pose
# (above) leaves VINS initialized in the wrong IMU frame and causes immediate
# failure/reboot cycles on any rig unlike upstream's example platform. Convert
# the native LiDAR pose to the IMU state with the supplied IMU<-LiDAR rigid
# transform. This is a frame-contract correction, not trajectory postprocessing.
initial_alignment = root / "src/visual_odometry/visual_estimator/initial/initial_alignment.h"
text = initial_alignment.read_text()
include_anchor = '#include "../feature_manager.h"'
if include_anchor in text and '#include "../parameters.h"' not in text:
    text = text.replace(include_anchor, include_anchor + '\n#include "../parameters.h"')
old = """        // convert odometry rotation from lidar ROS frame to VINS camera frame (only rotation, assume lidar, camera, and IMU are close enough)
        tf::Quaternion q_odom_lidar;
        tf::quaternionMsgToTF(odomCur.pose.pose.orientation, q_odom_lidar);

        tf::Quaternion q_odom_cam = tf::createQuaternionFromRPY(0, 0, M_PI) * (q_odom_lidar * q_lidar_to_cam); // global rotate by pi // mark: camera - lidar
        tf::quaternionTFToMsg(q_odom_cam, odomCur.pose.pose.orientation);

        // convert odometry position from lidar ROS frame to VINS camera frame
        Eigen::Vector3d p_eigen(odomCur.pose.pose.position.x, odomCur.pose.pose.position.y, odomCur.pose.pose.position.z);
        Eigen::Vector3d v_eigen(odomCur.twist.twist.linear.x, odomCur.twist.twist.linear.y, odomCur.twist.twist.linear.z);
        Eigen::Vector3d p_eigen_new = q_lidar_to_cam_eigen * p_eigen;
        Eigen::Vector3d v_eigen_new = q_lidar_to_cam_eigen * v_eigen;
"""
new = """        // Convert native LiDAR odometry into the IMU state expected by
        // VINS. Upstream's fixed camera/LiDAR rotation only matches its demo rig.
        tf::Quaternion q_odom_lidar;
        tf::quaternionMsgToTF(odomCur.pose.pose.orientation, q_odom_lidar);
        Eigen::Vector3d p_eigen(odomCur.pose.pose.position.x, odomCur.pose.pose.position.y, odomCur.pose.pose.position.z);
        Eigen::Vector3d v_eigen(odomCur.twist.twist.linear.x, odomCur.twist.twist.linear.y, odomCur.twist.twist.linear.z);
        Eigen::Vector3d p_eigen_new;
        Eigen::Vector3d v_eigen_new;
        if (USE_CALIBRATED_VINS_LIDAR_TRANSFORM)
        {
            Eigen::Quaterniond q_world_lidar(q_odom_lidar.w(), q_odom_lidar.x(),
                                             q_odom_lidar.y(), q_odom_lidar.z());
            Eigen::Quaterniond q_imu_lidar(R_IMU_LIDAR);
            Eigen::Quaterniond q_world_imu =
                (q_world_lidar * q_imu_lidar.conjugate()).normalized();
            p_eigen_new = p_eigen - q_world_imu * T_IMU_LIDAR;
            v_eigen_new = v_eigen;
            odomCur.pose.pose.orientation.x = q_world_imu.x();
            odomCur.pose.pose.orientation.y = q_world_imu.y();
            odomCur.pose.pose.orientation.z = q_world_imu.z();
            odomCur.pose.pose.orientation.w = q_world_imu.w();
        }
        else
        {
            tf::Quaternion q_odom_cam = tf::createQuaternionFromRPY(0, 0, M_PI) *
                                        (q_odom_lidar * q_lidar_to_cam);
            tf::quaternionTFToMsg(q_odom_cam, odomCur.pose.pose.orientation);
            p_eigen_new = q_lidar_to_cam_eigen * p_eigen;
            v_eigen_new = q_lidar_to_cam_eigen * v_eigen;
        }
"""
if old in text:
    text = text.replace(old, new)
elif "q_world_imu" not in text:
    raise RuntimeError("could not patch calibrated LiDAR-to-VINS initialization")
initial_alignment.write_text(text)

cmake = root / "CMakeLists.txt"
text = cmake.read_text()
text = text.replace('set(CMAKE_CXX_FLAGS "-std=c++11")', 'set(CMAKE_CXX_FLAGS "-std=c++14")')
text = text.replace(
    'set(CMAKE_CXX_FLAGS_RELEASE "-O3 -Wall -g -pthread")',
    'set(CMAKE_CXX_FLAGS_RELEASE "-O3 -Wall -pthread")',
)
text = text.replace("catkin_package(\n    DEPENDS PCL GTSAM\n)", "catkin_package(\n    DEPENDS PCL\n)")
cmake.write_text(text)
