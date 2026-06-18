#!/usr/bin/env python3
"""
tf_broadcaster_node.py
======================
Publishes all static TF transforms required by FAST-LIVO2 and RViz,
derived from the UrbanNav-HK-TST-20210517 calibration files:

    extrinsic.yaml        – sensor-to-IMU rigid-body transforms
    zed2_intrinsics.yaml  – camera model (intrinsics; not needed for TF)

TF Tree
───────
    camera_init               ← FAST-LIVO2 world/output frame (published
    └── body                    dynamically by FAST-LIVO2 itself)
        ├── velodyne            ← centre Velodyne LiDAR  (static)
        │   ├── velodyne_left   ← left   Velodyne LiDAR  (static)
        │   └── velodyne_right  ← right  Velodyne LiDAR  (static)
        ├── camera_left         ← ZED2 left  camera       (static)
        │   └── camera_left_optical
        └── camera_right        ← ZED2 right camera       (static)
            └── camera_right_optical

    map → odom               ← identity; kept for nav-stack compatibility

All transforms broadcast here are STATIC (StaticTransformBroadcaster).
FAST-LIVO2 provides the dynamic camera_init → body transform at runtime.

Notation from UrbanNav extrinsic.yaml/tools:
    SENSOR_T_IMU entries are camera_to_imu/lidar_to_imu transforms:
    p_body = T_body_sensor * p_sensor.
In ROS TF, parent body -> child sensor stores T_body_sensor, so use the raw matrices.

Source matrices: extrinsic.yaml (UrbanNav-HK-TST-20210517 calibration).
"""

import rospy
import numpy as np
import tf2_ros
import geometry_msgs.msg as gm

try:
    import transforms3d
    _HAS_T3D = True
except ImportError:
    _HAS_T3D = False
    rospy.logwarn_once(
        "[TF Broadcaster] transforms3d not found — falling back to "
        "manual quaternion computation (Shepperd's method)."
    )


# ─── Calibration matrices from extrinsic.yaml ─────────────────────────────────
# Convention from UrbanNav tools: SENSOR_T_IMU means p_body = M * p_sensor.
# In ROS TF, parent body -> child sensor stores this raw T_body_sensor.

# ZED2 left camera (≈ 85 mm left of IMU, 660 mm forward, 3.0 m up)
LEFT_CAMERA_T_IMU = np.array([
    [ 9.9885234402635936e-01,  1.3591158885981787e-03,  4.7876378696062108e-02, -8.4994249456545504e-02],
    [-4.7864188349269129e-02, -7.9091258538426246e-03,  9.9882253939420773e-01,  6.6169337079143220e-01],
    [ 1.7361758877140372e-03, -9.9996779874765440e-01, -7.8349959194297103e-03, -3.0104266183335913e+00],
    [ 0.,                      0.,                      0.,                      1.                    ],
], dtype=float)

# ZED2 right camera (≈ 75 mm right of IMU, 683 mm forward, 3.0 m up)
RIGHT_CAMERA_T_IMU = np.array([
    [ 9.9872871452749812e-01,  1.5287637777597791e-03,  5.0384696680271013e-02,  7.5332297629590136e-02],
    [-5.0367177375936031e-02, -9.8967686259809895e-03,  9.9868173179143760e-01,  6.8331281093016005e-01],
    [ 2.0253941424080261e-03, -9.9994985716888607e-01, -9.8071874914416046e-03, -3.0079627649520204e+00],
    [ 0.,                      0.,                      0.,                      1.                    ],
], dtype=float)

# Centre Velodyne VLP-16: pure Z-translation, 0.28 m above IMU
CENTER_LIDAR_T_IMU = np.array([
    [1., 0., 0., 0.  ],
    [0., 1., 0., 0.  ],
    [0., 0., 1., 0.28],
    [0., 0., 0., 1.  ],
], dtype=float)

# Left Velodyne relative to centre Velodyne
LEFT_LIDAR_T_CENTER = np.array([
    [-0.00848239, -0.561875,   -0.827179,  -0.267094   ],
    [ 0.999415,   -0.0321631,   0.0115987, -0.000706537],
    [-0.0331216,  -0.826597,    0.561819,  -0.224038   ],
    [ 0.,          0.,          0.,         1.         ],
], dtype=float)

# Right Velodyne relative to centre Velodyne
RIGHT_LIDAR_T_CENTER = np.array([
    [ 0.566085,   0.0347042,   0.823616,    0.323744   ],
    [-0.0296934,  0.999323,   -0.0216991,  -0.00124153 ],
    [-0.823812,  -0.0121725,   0.566732,   -0.200876   ],
    [ 0.,         0.,          0.,          1.         ],
], dtype=float)

# GNSS antenna (visualisation only — not forwarded to FAST-LIVO2)
ANTENNA_T_IMU = np.array([
    [1., 0., 0.,  0.  ],
    [0., 1., 0.,  0.86],
    [0., 0., 1., -0.31],
    [0., 0., 0.,  1.  ],
], dtype=float)

# ROS optical-frame convention: camera_link → camera_optical
# x right, y down, z forward  (from x right, y up, z backward in camera_link)
CAM_TO_OPTICAL = np.array([
    [ 0.,  0.,  1.,  0.],
    [-1.,  0.,  0.,  0.],
    [ 0., -1.,  0.,  0.],
    [ 0.,  0.,  0.,  1.],
], dtype=float)


# ─── Helper functions ─────────────────────────────────────────────────────────

def invert_rigid(T: np.ndarray) -> np.ndarray:
    """Invert a 4×4 rigid-body transform without full matrix inversion.

    Uses R^-1 = R^T for the rotation part, which is exact (no numerical error)
    and avoids np.linalg.inv numerical instability on near-identity rotations.
    """
    R  = T[:3, :3]
    t  = T[:3, 3]
    Ti = np.eye(4)
    Ti[:3, :3] = R.T
    Ti[:3,  3] = -(R.T @ t)
    return Ti


def rot_to_quat(R: np.ndarray):
    """Convert 3×3 rotation matrix to quaternion (x, y, z, w).

    Uses transforms3d if available (preferred), otherwise Shepperd's method
    which is numerically stable for all rotation magnitudes.
    """
    if _HAS_T3D:
        wxyz = transforms3d.quaternions.mat2quat(R)  # [w, x, y, z]
        return wxyz[1], wxyz[2], wxyz[3], wxyz[0]    # → (x, y, z, w)

    # Shepperd's method
    trace = R[0, 0] + R[1, 1] + R[2, 2]
    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (R[2, 1] - R[1, 2]) * s
        y = (R[0, 2] - R[2, 0]) * s
        z = (R[1, 0] - R[0, 1]) * s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s
    return x, y, z, w


def make_stamped_tf(T: np.ndarray, parent: str, child: str) -> gm.TransformStamped:
    """Build a TransformStamped from a 4×4 homogeneous matrix."""
    ts                   = gm.TransformStamped()
    ts.header.stamp      = rospy.Time.now()
    ts.header.frame_id   = parent
    ts.child_frame_id    = child

    ts.transform.translation.x = T[0, 3]
    ts.transform.translation.y = T[1, 3]
    ts.transform.translation.z = T[2, 3]

    x, y, z, w = rot_to_quat(T[:3, :3])
    ts.transform.rotation.x = x
    ts.transform.rotation.y = y
    ts.transform.rotation.z = z
    ts.transform.rotation.w = w
    return ts


# ─── Build all static transforms ─────────────────────────────────────────────

def build_static_transforms():
    """Compute and return the full list of TransformStamped messages.

    All transforms are from the UrbanNav extrinsic.yaml calibration.
    The body frame is the IMU frame (FAST-LIVO2 convention).
    """
    tfs = []

    # body → velodyne  (centre Velodyne LiDAR; 0.28 m above IMU along Z)
    tfs.append(make_stamped_tf(CENTER_LIDAR_T_IMU, "body", "velodyne"))

    # velodyne → velodyne_left / velodyne_right  (raw UrbanNav center→side LiDAR extrinsics)
    tfs.append(make_stamped_tf(LEFT_LIDAR_T_CENTER,  "velodyne", "velodyne_left"))
    tfs.append(make_stamped_tf(RIGHT_LIDAR_T_CENTER, "velodyne", "velodyne_right"))

    # body → camera_left / camera_right  (ZED2 stereo pair)
    tfs.append(make_stamped_tf(LEFT_CAMERA_T_IMU,  "body", "camera_left"))
    tfs.append(make_stamped_tf(RIGHT_CAMERA_T_IMU, "body", "camera_right"))

    # camera → camera_optical  (ROS optical-frame convention for image_view)
    tfs.append(make_stamped_tf(CAM_TO_OPTICAL, "camera_right", "camera_right_optical"))
    tfs.append(make_stamped_tf(CAM_TO_OPTICAL, "camera_left",  "camera_left_optical"))

    # body → gnss_antenna  (visualisation only — not fed to FAST-LIVO2)
    tfs.append(make_stamped_tf(ANTENNA_T_IMU, "body", "gnss_antenna"))

    # map → odom  (identity; required by rviz nav-stack visualisers)
    tfs.append(make_stamped_tf(np.eye(4), "map", "odom"))

    return tfs


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    rospy.init_node("tf_broadcaster_node", anonymous=False)
    broadcaster = tf2_ros.StaticTransformBroadcaster()

    transforms = build_static_transforms()
    broadcaster.sendTransform(transforms)

    rospy.loginfo(
        "[TF Broadcaster] Published %d static transforms:\n%s",
        len(transforms),
        "\n".join(f"  {t.header.frame_id}  →  {t.child_frame_id}" for t in transforms),
    )

    rospy.spin()


if __name__ == "__main__":
    main()
