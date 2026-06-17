#!/usr/bin/env python3
"""
tf_broadcaster_node.py  (orbslam3_urbannav)
============================================
Publishes static UrbanNav calibration TFs for ORB-SLAM3 RViz context.

Dynamic pose is published by pose_republisher_node.py as:
  camera_init -> body

This node publishes only static context frames:
  map -> camera_init                   identity
  body -> camera_right                 calibration
  body -> camera_left                  calibration
  body -> velodyne                     calibration/context
  body -> gnss_antenna                 UrbanNav GNSS antenna lever arm
  camera_* -> camera_*_optical         ROS optical convention

It intentionally does NOT publish a static parent for body, because ORB-SLAM3
owns the live body pose.
"""

import os
import rospy
import numpy as np
import tf2_ros
import geometry_msgs.msg as gm
import transforms3d


def invert_rigid(T: np.ndarray) -> np.ndarray:
    R = T[:3, :3]
    t = T[:3, 3]
    Ti = np.eye(4)
    Ti[:3, :3] = R.T
    Ti[:3, 3] = -(R.T @ t)
    return Ti


def make_tf(T: np.ndarray, parent: str, child: str) -> gm.TransformStamped:
    ts = gm.TransformStamped()
    ts.header.stamp = rospy.Time.now()
    ts.header.frame_id = parent
    ts.child_frame_id = child
    ts.transform.translation.x = float(T[0, 3])
    ts.transform.translation.y = float(T[1, 3])
    ts.transform.translation.z = float(T[2, 3])
    q = transforms3d.quaternions.mat2quat(T[:3, :3])  # w, x, y, z
    ts.transform.rotation.w = float(q[0])
    ts.transform.rotation.x = float(q[1])
    ts.transform.rotation.y = float(q[2])
    ts.transform.rotation.z = float(q[3])
    return ts


LEFT_CAMERA_T_IMU = np.array([
    [9.9885234402635936e-01, 1.3591158885981787e-03, 4.7876378696062108e-02, -8.4994249456545504e-02],
    [-4.7864188349269129e-02, -7.9091258538426246e-03, 9.9882253939420773e-01, 6.6169337079143220e-01],
    [1.7361758877140372e-03, -9.9996779874765440e-01, -7.8349959194297103e-03, -3.0104266183335913e+00],
    [0.0, 0.0, 0.0, 1.0],
], dtype=float)

RIGHT_CAMERA_T_IMU = np.array([
    [9.9872871452749812e-01, 1.5287637777597791e-03, 5.0384696680271013e-02, 7.5332297629590136e-02],
    [-5.0367177375936031e-02, -9.8967686259809895e-03, 9.9868173179143760e-01, 6.8331281093016005e-01],
    [2.0253941424080261e-03, -9.9994985716888607e-01, -9.8071874914416046e-03, -3.0079627649520204e+00],
    [0.0, 0.0, 0.0, 1.0],
], dtype=float)

CENTER_LIDAR_T_IMU = np.array([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.28],
    [0.0, 0.0, 0.0, 1.0],
], dtype=float)

# UrbanNav antenna calibration: ANTENNA_T_IMU is p_body = T_body_antenna * p_antenna.
ANTENNA_T_IMU = np.array([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.86],
    [0.0, 0.0, 1.0, -0.31],
    [0.0, 0.0, 0.0, 1.0],
], dtype=float)

CAM_TO_OPTICAL = np.array([
    [0.0, 0.0, 1.0, 0.0],
    [-1.0, 0.0, 0.0, 0.0],
    [0.0, -1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0],
], dtype=float)

E2O_FRONT_CAMERA_T_LIDAR103 = np.array([
    [-0.18256836, -0.98306216, -0.01604916,  0.07383026],
    [ 0.11110754, -0.00440978, -0.99379861, -0.53581120],
    [ 0.97689503, -0.18321936,  0.11003070, -0.31010858],
    [ 0.0,         0.0,         0.0,         1.0       ],
], dtype=float)


def build_static_transforms():
    world_frame = rospy.get_param("~world_frame_id", "camera_init")
    publish_map_identity = rospy.get_param("~publish_map_identity", True)

    tfs = []
    if publish_map_identity and world_frame != "map":
        tfs.append(make_tf(np.eye(4), "map", world_frame))

    dataset_id = str(rospy.get_param("~dataset_id", os.environ.get("DATASET_ID", "urbannav"))).lower()
    if dataset_id == "e2o":
        # E2O mono camera image is already published in camera_right_optical.
        tfs.append(make_tf(np.eye(4), "body", "velodyne"))
        tfs.append(make_tf(E2O_FRONT_CAMERA_T_LIDAR103, "body", "camera_right"))
        tfs.append(make_tf(np.eye(4), "camera_right", "camera_right_optical"))
        tfs.append(make_tf(np.eye(4), "body", "gnss_antenna"))
        tfs.append(make_tf(np.eye(4), "body", "gps_link"))
    else:
        # SENSOR_T_IMU stores T_body_sensor (p_body = T_body_sensor * p_sensor), so use it raw in ROS TF.
        tfs.append(make_tf(RIGHT_CAMERA_T_IMU, "body", "camera_right"))
        tfs.append(make_tf(LEFT_CAMERA_T_IMU, "body", "camera_left"))
        tfs.append(make_tf(CENTER_LIDAR_T_IMU, "body", "velodyne"))
        tfs.append(make_tf(ANTENNA_T_IMU, "body", "gnss_antenna"))
        # Backward-compatible alias for older GPS configs. The GPS provider now uses
        # gnss_antenna by default, but publishing gps_link avoids lookup failures if a
        # user still has an old CSV replayer/launch param.
        tfs.append(make_tf(ANTENNA_T_IMU, "body", "gps_link"))
        tfs.append(make_tf(CAM_TO_OPTICAL, "camera_right", "camera_right_optical"))
        tfs.append(make_tf(CAM_TO_OPTICAL, "camera_left", "camera_left_optical"))
    return tfs


def main():
    rospy.init_node("tf_broadcaster_node", anonymous=False)
    broadcaster = tf2_ros.StaticTransformBroadcaster()
    transforms = build_static_transforms()
    broadcaster.sendTransform(transforms)
    rospy.loginfo(
        "[ORB-SLAM3 TF Broadcaster] Published %d static transforms:\n%s",
        len(transforms),
        "\n".join(f"  {t.header.frame_id} -> {t.child_frame_id}" for t in transforms),
    )
    rospy.spin()


if __name__ == "__main__":
    main()
