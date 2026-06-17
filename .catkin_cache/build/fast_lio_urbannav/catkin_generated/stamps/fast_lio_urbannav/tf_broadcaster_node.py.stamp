#!/usr/bin/env python3
"""
tf_broadcaster_node.py
======================
Static UrbanNav-HK-TST sensor calibration TFs used by FAST-LIO2, LVI-SAM and RViz.

This file is based on the working FAST-LIVO2 reference wrapper from example.zip.
It keeps the same UrbanNav calibration matrices and exposes small ROS params so
FAST-LIO2 and LVI-SAM can use the same calibration without TF conflicts:

  FAST-LIO2 mode/default:
    publish_map_odom:=true
    publish_camera_init_map:=false
    publish_base_link_body:=false

  LVI-SAM mode:
    publish_map_odom:=false       # LVI-SAM publishes dynamic map -> odom itself
    publish_camera_init_map:=true # connects RViz fixed frame camera_init to LVI map
    publish_base_link_body:=true  # publishes body -> base_link/lidar_link aliases.
                                  # body must never be a static child because
                                  # native LVI-SAM publishes odom -> body.

All sensor transforms are STATIC. Message timestamps are never altered here.
"""

import os
import rospy
import numpy as np
import tf2_ros
import geometry_msgs.msg as gm

try:
    import transforms3d
    _HAS_T3D = True
except ImportError:
    _HAS_T3D = False

# ─── Calibration matrices from UrbanNav extrinsic.yaml ───────────────────────
# UrbanNav convention used by the uploaded dataset tools:
# SENSOR_T_IMU means p_body/imu = SENSOR_T_IMU * p_sensor.
# In ROS TF, parent body -> child sensor stores exactly T_body_sensor,
# so these raw matrices are used directly for body->sensor static transforms.

LEFT_CAMERA_T_IMU = np.array([
    [ 9.9885234402635936e-01,  1.3591158885981787e-03,  4.7876378696062108e-02, -8.4994249456545504e-02],
    [-4.7864188349269129e-02, -7.9091258538426246e-03,  9.9882253939420773e-01,  6.6169337079143220e-01],
    [ 1.7361758877140372e-03, -9.9996779874765440e-01, -7.8349959194297103e-03, -3.0104266183335913e+00],
    [ 0.,                      0.,                      0.,                      1.                    ],
], dtype=float)

RIGHT_CAMERA_T_IMU = np.array([
    [ 9.9872871452749812e-01,  1.5287637777597791e-03,  5.0384696680271013e-02,  7.5332297629590136e-02],
    [-5.0367177375936031e-02, -9.8967686259809895e-03,  9.9868173179143760e-01,  6.8331281093016005e-01],
    [ 2.0253941424080261e-03, -9.9994985716888607e-01, -9.8071874914416046e-03, -3.0079627649520204e+00],
    [ 0.,                      0.,                      0.,                      1.                    ],
], dtype=float)

CENTER_LIDAR_T_IMU = np.array([
    [1., 0., 0., 0.  ],
    [0., 1., 0., 0.  ],
    [0., 0., 1., 0.28],
    [0., 0., 0., 1.  ],
], dtype=float)

LEFT_LIDAR_T_CENTER = np.array([
    [-0.00848239, -0.561875,   -0.827179,  -0.267094   ],
    [ 0.999415,   -0.0321631,   0.0115987, -0.000706537],
    [-0.0331216,  -0.826597,    0.561819,  -0.224038   ],
    [ 0.,          0.,          0.,         1.         ],
], dtype=float)

RIGHT_LIDAR_T_CENTER = np.array([
    [ 0.566085,   0.0347042,   0.823616,    0.323744   ],
    [-0.0296934,  0.999323,   -0.0216991,  -0.00124153 ],
    [-0.823812,  -0.0121725,   0.566732,   -0.200876   ],
    [ 0.,         0.,          0.,          1.         ],
], dtype=float)

ANTENNA_T_IMU = np.array([
    [1., 0., 0.,  0.  ],
    [0., 1., 0.,  0.86],
    [0., 0., 1., -0.31],
    [0., 0., 0.,  1.  ],
], dtype=float)

# ROS optical frame convention: x right, y down, z forward.
CAM_TO_OPTICAL = np.array([
    [ 0.,  0.,  1.,  0.],
    [-1.,  0.,  0.,  0.],
    [ 0., -1.,  0.,  0.],
    [ 0.,  0.,  0.,  1.],
], dtype=float)

# E2O front-camera calibration used by the working E2O FAST-LIVO2 reference.
# Convention: p_camera = E2O_FRONT_CAMERA_T_LIDAR103 * p_lidar103.
# ROS static TF body->camera must store T_body_camera, so invert this matrix.
E2O_FRONT_CAMERA_T_LIDAR103 = np.array([
    [-0.18256836, -0.98306216, -0.01604916,  0.07383026],
    [ 0.11110754, -0.00440978, -0.99379861, -0.53581120],
    [ 0.97689503, -0.18321936,  0.11003070, -0.31010858],
    [ 0.0,         0.0,         0.0,         1.0       ],
], dtype=float)


def invert_rigid(T: np.ndarray) -> np.ndarray:
    R = T[:3, :3]
    t = T[:3, 3]
    Ti = np.eye(4)
    Ti[:3, :3] = R.T
    Ti[:3, 3] = -(R.T @ t)
    return Ti


def rot_to_quat(R: np.ndarray):
    if _HAS_T3D:
        wxyz = transforms3d.quaternions.mat2quat(R)
        return wxyz[1], wxyz[2], wxyz[3], wxyz[0]

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
    ts = gm.TransformStamped()
    ts.header.stamp = rospy.Time.now()
    ts.header.frame_id = parent
    ts.child_frame_id = child
    ts.transform.translation.x = float(T[0, 3])
    ts.transform.translation.y = float(T[1, 3])
    ts.transform.translation.z = float(T[2, 3])
    x, y, z, w = rot_to_quat(T[:3, :3])
    ts.transform.rotation.x = float(x)
    ts.transform.rotation.y = float(y)
    ts.transform.rotation.z = float(z)
    ts.transform.rotation.w = float(w)
    return ts


def build_static_transforms():
    publish_map_odom = bool(rospy.get_param("~publish_map_odom", True))
    publish_camera_init_map = bool(rospy.get_param("~publish_camera_init_map", False))
    publish_base_link_body = bool(rospy.get_param("~publish_base_link_body", False))

    tfs = []
    dataset_id = str(rospy.get_param("~dataset_id", os.environ.get("DATASET_ID", "urbannav"))).lower()

    if dataset_id == "e2o":
        # E2O working reference treats lidar103 as body origin. Do not reuse
        # UrbanNav's +0.28 m LiDAR/IMU lever arm or ZED2 camera calibration.
        tfs.append(make_stamped_tf(np.eye(4), "body", "velodyne"))
        tfs.append(make_stamped_tf(invert_rigid(E2O_FRONT_CAMERA_T_LIDAR103), "body", "camera_right"))
        tfs.append(make_stamped_tf(np.eye(4), "camera_right", "camera_right_optical"))
        tfs.append(make_stamped_tf(np.eye(4), "body", "gnss_antenna"))
    else:
        # Reference FAST-LIVO2/UrbanNav calibration TFs.
        tfs.append(make_stamped_tf(CENTER_LIDAR_T_IMU, "body", "velodyne"))
        tfs.append(make_stamped_tf(LEFT_LIDAR_T_CENTER, "velodyne", "velodyne_left"))
        tfs.append(make_stamped_tf(RIGHT_LIDAR_T_CENTER, "velodyne", "velodyne_right"))
        tfs.append(make_stamped_tf(LEFT_CAMERA_T_IMU, "body", "camera_left"))
        tfs.append(make_stamped_tf(RIGHT_CAMERA_T_IMU, "body", "camera_right"))
        tfs.append(make_stamped_tf(CAM_TO_OPTICAL, "camera_right", "camera_right_optical"))
        tfs.append(make_stamped_tf(CAM_TO_OPTICAL, "camera_left", "camera_left_optical"))
        tfs.append(make_stamped_tf(ANTENNA_T_IMU, "body", "gnss_antenna"))

    identity = np.eye(4)
    if publish_map_odom:
        tfs.append(make_stamped_tf(identity, "map", "camera_init"))
    if publish_camera_init_map:
        tfs.append(make_stamped_tf(identity, "camera_init", "map"))
    if publish_base_link_body:
        # Native LVI-SAM odometry uses `body` as the moving child frame
        # (odom -> body). Publishing base_link -> body or lidar_link -> body
        # would give `body` multiple TF parents and can make RViz/clouds jump.
        # Keep body as parent and expose aliases below it.
        tfs.append(make_stamped_tf(identity, "body", "base_link"))
        tfs.append(make_stamped_tf(identity, "body", "lidar_link"))

    return tfs


def main():
    rospy.init_node("tf_broadcaster_node", anonymous=False)
    broadcaster = tf2_ros.StaticTransformBroadcaster()
    transforms = build_static_transforms()
    broadcaster.sendTransform(transforms)
    rospy.loginfo(
        "[TF Broadcaster] Published %d static transforms:\n%s",
        len(transforms),
        "\n".join(f"  {t.header.frame_id} -> {t.child_frame_id}" for t in transforms),
    )
    rospy.spin()


if __name__ == "__main__":
    main()
