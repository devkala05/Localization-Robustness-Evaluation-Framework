#!/usr/bin/env python3
"""Dataset-aware static TF broadcaster for R3LIVE.

R3LIVE is sensitive to TF consistency because RViz displays both native body-frame
clouds and map-frame odometry.  The previous wrapper always published UrbanNav
ZED2/Velodyne calibration, even during E2O runs.  For E2O that makes RViz
transform clouds through the wrong camera/lidar tree and the scene appears to
roll around the vehicle.

This node publishes only static sensor/context transforms.  Dynamic map/body TF
must come from native R3LIVE, or from the benchmark republisher when explicitly
enabled.
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

# ---------------- UrbanNav-HK-TST calibration ----------------
LEFT_CAMERA_T_IMU = np.array([
    [ 9.9885234402635936e-01,  1.3591158885981787e-03,  4.7876378696062108e-02, -8.4994249456545504e-02],
    [-4.7864188349269129e-02, -7.9091258538426246e-03,  9.9882253939420773e-01,  6.6169337079143220e-01],
    [ 1.7361758877140372e-03, -9.9996779874765440e-01, -7.8349959194297103e-03, -3.0104266183335913e+00],
    [ 0., 0., 0., 1.]], dtype=float)

RIGHT_CAMERA_T_IMU = np.array([
    [ 9.9872871452749812e-01,  1.5287637777597791e-03,  5.0384696680271013e-02,  7.5332297629590136e-02],
    [-5.0367177375936031e-02, -9.8967686259809895e-03,  9.9868173179143760e-01,  6.8331281093016005e-01],
    [ 2.0253941424080261e-03, -9.9994985716888607e-01, -9.8071874914416046e-03, -3.0079627649520204e+00],
    [ 0., 0., 0., 1.]], dtype=float)

CENTER_LIDAR_T_IMU = np.array([
    [1., 0., 0., 0.  ],
    [0., 1., 0., 0.  ],
    [0., 0., 1., 0.28],
    [0., 0., 0., 1.  ]], dtype=float)

LEFT_LIDAR_T_CENTER = np.array([
    [-0.00848239, -0.561875,  -0.827179, -0.267094   ],
    [ 0.999415,  -0.0321631,  0.0115987,-0.000706537],
    [-0.0331216, -0.826597,   0.561819, -0.224038   ],
    [ 0.,         0.,         0.,        1.         ]], dtype=float)

RIGHT_LIDAR_T_CENTER = np.array([
    [ 0.566085,  0.0347042,  0.823616,   0.323744  ],
    [-0.0296934, 0.999323,  -0.0216991, -0.00124153],
    [-0.823812, -0.0121725,  0.566732,  -0.200876  ],
    [ 0.,        0.,         0.,         1.        ]], dtype=float)

ANTENNA_T_IMU = np.array([
    [1., 0., 0.,  0.  ],
    [0., 1., 0.,  0.86],
    [0., 0., 1., -0.31],
    [0., 0., 0.,  1.  ]], dtype=float)

# ---------------- E2O faculty-loop calibration ----------------
# Supplied convention: p_front_camera = R * p_lidar103 + t.
# In this benchmark body is lidar103, so ROS body->camera uses inverse(T_lidar_camera).
E2O_LIDAR103_TO_FRONT_CAMERA = np.array([
    [-0.18256836, -0.98306216, -0.01604916,  0.07383026],
    [ 0.11110754, -0.00440978, -0.99379861, -0.53581120],
    [ 0.97689503, -0.18321936,  0.11003070, -0.31010858],
    [ 0.,          0.,          0.,          1.        ]], dtype=float)

E2O_LIDAR102_TO_103 = np.array([
    [ 0.939229,  0.114115,  0.323769,  0.368830],
    [-0.183642,  0.963858,  0.193013,  0.290573],
    [-0.290041, -0.240741,  0.926240, -0.187366],
    [ 0.,        0.,        0.,        1.      ]], dtype=float)

E2O_LIDAR104_TO_103 = np.array([
    [ 0.936284,  0.272688,  0.221389,  0.241260],
    [-0.198318,  0.930633, -0.307559, -0.433314],
    [-0.289899,  0.244057,  0.925416, -0.154562],
    [ 0.,        0.,        0.,        1.      ]], dtype=float)

CAM_TO_OPTICAL = np.array([
    [ 0.,  0., 1., 0.],
    [-1.,  0., 0., 0.],
    [ 0., -1., 0., 0.],
    [ 0.,  0., 0., 1.]], dtype=float)


def invert_rigid(T):
    R = T[:3, :3]
    t = T[:3, 3]
    Ti = np.eye(4)
    Ti[:3, :3] = R.T
    Ti[:3, 3] = -(R.T @ t)
    return Ti


def rot_to_quat(R):
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


def make_tf(T, parent, child):
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


def urban_nav_tfs():
    return [
        make_tf(CENTER_LIDAR_T_IMU,  'body',     'velodyne'),
        make_tf(LEFT_LIDAR_T_CENTER,  'velodyne', 'velodyne_left'),
        make_tf(RIGHT_LIDAR_T_CENTER, 'velodyne', 'velodyne_right'),
        make_tf(LEFT_CAMERA_T_IMU,    'body',     'camera_left'),
        make_tf(RIGHT_CAMERA_T_IMU,   'body',     'camera_right'),
        make_tf(CAM_TO_OPTICAL, 'camera_right', 'camera_right_optical'),
        make_tf(CAM_TO_OPTICAL, 'camera_left',  'camera_left_optical'),
        make_tf(ANTENNA_T_IMU, 'body', 'gnss_antenna'),
        make_tf(np.eye(4), 'map', 'camera_init'),
        make_tf(np.eye(4), 'camera_init', 'world'),
        make_tf(np.eye(4), 'body', 'base_link'),
        make_tf(np.eye(4), 'body', 'lidar_link'),
    ]


def e2o_tfs():
    body_to_camera = invert_rigid(E2O_LIDAR103_TO_FRONT_CAMERA)
    return [
        make_tf(np.eye(4), 'body', 'velodyne'),
        make_tf(np.eye(4), 'body', 'velodyne103'),
        make_tf(E2O_LIDAR102_TO_103, 'velodyne103', 'velodyne102'),
        make_tf(E2O_LIDAR104_TO_103, 'velodyne103', 'velodyne104'),
        make_tf(body_to_camera, 'body', 'camera_right'),
        make_tf(np.eye(4), 'camera_right', 'camera_right_optical'),
        make_tf(np.eye(4), 'camera_right', 'camera_color_optical_frame'),
        make_tf(np.eye(4), 'body', 'gnss_antenna'),
        make_tf(np.eye(4), 'map', 'camera_init'),
        make_tf(np.eye(4), 'camera_init', 'world'),
        make_tf(np.eye(4), 'body', 'base_link'),
        make_tf(np.eye(4), 'body', 'lidar_link'),
    ]


def main():
    rospy.init_node('tf_broadcaster_node', anonymous=False)
    dataset_id = str(rospy.get_param('~dataset_id', rospy.get_param('/dataset_id', 'urbannav'))).strip().lower()
    tfs = e2o_tfs() if dataset_id == 'e2o' else urban_nav_tfs()
    broadcaster = tf2_ros.StaticTransformBroadcaster()
    broadcaster.sendTransform(tfs)
    rospy.loginfo('[R3LIVE TF Broadcaster] dataset=%s Published %d static transforms:\n%s',
                  dataset_id, len(tfs), '\n'.join(f'  {t.header.frame_id} -> {t.child_frame_id}' for t in tfs))
    rospy.spin()


if __name__ == '__main__':
    main()
