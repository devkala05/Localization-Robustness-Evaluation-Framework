#!/usr/bin/env python3
"""
tf_broadcaster_node.py  (orbslam3_urbannav)
============================================
Publishes all STATIC TF transforms required by ORB-SLAM3 and RViz.

TF Tree Design
──────────────
    map
    └── odom                      ← static identity (ORB-SLAM3 world frame)
        ├── camera_right          ← ORB-SLAM3 tracks this dynamically
        │   │                       (odom → camera_right published by pose_republisher_node.py)
        │   └── camera_right_optical       ← ROS optical convention
        └── body                  ← static identity anchor for context frames

Additional frames for context (not consumed by ORB-SLAM3):
    body                          ← IMU frame (from calibration)
        ├── velodyne              ← centre LiDAR
        └── camera_left

All static transforms are derived from extrinsic.yaml.
ORB-SLAM3 publishes odom → camera_right dynamically via /tf; this node must
not also publish a static parent for camera_right.
This node publishes everything else.

Extrinsic convention (same as fast_lio_urbannav):
  LEFT_CAMERA_T_IMU transforms p_imu → p_camleft
  So body → camera_left = inv(LEFT_CAMERA_T_IMU)
"""

import rospy
import numpy as np
import tf2_ros
import geometry_msgs.msg as gm
import transforms3d


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers (identical to fast_lio_urbannav)
# ─────────────────────────────────────────────────────────────────────────────

def mat4_to_stamped_transform(T: np.ndarray,
                               parent: str,
                               child: str) -> gm.TransformStamped:
    ts = gm.TransformStamped()
    ts.header.stamp    = rospy.Time.now()
    ts.header.frame_id = parent
    ts.child_frame_id  = child
    ts.transform.translation.x = T[0, 3]
    ts.transform.translation.y = T[1, 3]
    ts.transform.translation.z = T[2, 3]
    R    = T[:3, :3]
    wxyz = transforms3d.quaternions.mat2quat(R)
    ts.transform.rotation.w = wxyz[0]
    ts.transform.rotation.x = wxyz[1]
    ts.transform.rotation.y = wxyz[2]
    ts.transform.rotation.z = wxyz[3]
    return ts


def invert_T(T: np.ndarray) -> np.ndarray:
    R = T[:3, :3]
    t = T[:3, 3]
    T_inv = np.eye(4)
    T_inv[:3, :3] = R.T
    T_inv[:3,  3] = -R.T @ t
    return T_inv


# ─────────────────────────────────────────────────────────────────────────────
#  Calibration matrices from extrinsic.yaml
# ─────────────────────────────────────────────────────────────────────────────

LEFT_CAMERA_T_IMU = np.array([
    [ 9.9885234402635936e-01,  1.3591158885981787e-03,  4.7876378696062108e-02, -8.4994249456545504e-02],
    [-4.7864188349269129e-02, -7.9091258538426246e-03,  9.9882253939420773e-01,  6.6169337079143220e-01],
    [ 1.7361758877140372e-03, -9.9996779874765440e-01, -7.8349959194297103e-03, -3.0104266183335913e+00],
    [ 0.,                      0.,                      0.,                      1.                    ],
])

CENTER_LIDAR_T_IMU = np.array([
    [1., 0., 0., 0.   ],
    [0., 1., 0., 0.   ],
    [0., 0., 1., 0.28 ],
    [0., 0., 0., 1.   ],
])

# ROS optical-frame rotation: camera → camera_optical
# x right, y down, z forward in optical frame
CAM_TO_OPTICAL = np.array([
    [ 0.,  0.,  1.,  0.],
    [-1.,  0.,  0.,  0.],
    [ 0., -1.,  0.,  0.],
    [ 0.,  0.,  0.,  1.],
])


def build_static_transforms():
    transforms = []

    # ── map → odom  (identity — ORB-SLAM3 world frame anchor) ────────────────
    transforms.append(mat4_to_stamped_transform(np.eye(4), "map", "odom"))

    # ── odom → body  (identity anchor for static context frames) ─────────────
    transforms.append(mat4_to_stamped_transform(np.eye(4), "odom", "body"))

    # ── camera_right → camera_right_optical ──────────────────────────────────
    transforms.append(mat4_to_stamped_transform(
        CAM_TO_OPTICAL, "camera_right", "camera_right_optical"))

    # ── body → camera_left (for completeness / multi-sensor context) ─────────
    T_body_camleft = invert_T(LEFT_CAMERA_T_IMU)
    transforms.append(mat4_to_stamped_transform(
        T_body_camleft, "body", "camera_left"))

    transforms.append(mat4_to_stamped_transform(
        CAM_TO_OPTICAL, "camera_left", "camera_left_optical"))

    # ── body → velodyne (context only — LiDAR not used by ORB-SLAM3) ─────────
    T_body_lidar = invert_T(CENTER_LIDAR_T_IMU)
    transforms.append(mat4_to_stamped_transform(
        T_body_lidar, "body", "velodyne"))

    return transforms


def main():
    rospy.init_node("tf_broadcaster_node", anonymous=False)
    broadcaster = tf2_ros.StaticTransformBroadcaster()
    transforms  = build_static_transforms()
    broadcaster.sendTransform(transforms)

    rospy.loginfo(
        "[TF Broadcaster] Published %d static transforms:\n%s",
        len(transforms),
        "\n".join(
            f"  {t.header.frame_id} → {t.child_frame_id}"
            for t in transforms
        )
    )
    rospy.spin()


if __name__ == "__main__":
    main()
