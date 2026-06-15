#!/usr/bin/env python3
"""
Adaptive-W LVIO UrbanNav node — independent localisation version.

This node is intentionally NOT a FAST-LIO2 relay. It estimates a local trajectory
from the perturbed UrbanNav LiDAR + IMU + camera streams directly:

  * LiDAR: sparse 2D/3D scan-to-scan ICP gives translation and yaw increments.
  * IMU: gyro-z integration is used as a yaw prior and fallback during weak ICP.
  * Camera: image timestamp continuity contributes to the adaptive health weights
    so visual drop/noise perturbations affect confidence instead of being ignored.

It is a lightweight benchmark implementation of an adaptive weighted LVIO-style
front-end, not the original paper's full GTSAM/eigendecomposition code. The key
fix is that it now performs its own localisation and does not subscribe to or
launch FAST-LIO2 /Odometry.

Inputs:
  /cloud_registered_raw    sensor_msgs/PointCloud2 from perturbation adapter
  /livox/imu               sensor_msgs/Imu from perturbation adapter
  /camera/right/image_raw  sensor_msgs/Image from perturbation adapter

Outputs:
  /adaptive_w_lvio/odometry/mapping nav_msgs/Odometry
  /adaptive_w_lvio/mapping/path     nav_msgs/Path
  /adaptive_w_lvio/cloud_registered sensor_msgs/PointCloud2 relay for RViz
  /adaptive_w_lvio/debug/weights    std_msgs/String
"""

import copy
import math
from typing import Optional, Tuple

import numpy as np
import rospy
import tf2_ros
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Odometry, Path
from sensor_msgs.msg import Image, Imu, PointCloud2, PointField
from std_msgs.msg import String
from tf.transformations import quaternion_from_euler

try:
    from scipy.spatial import cKDTree
    _HAS_SCIPY = True
except Exception:  # pragma: no cover - only hit if scipy missing in container
    cKDTree = None
    _HAS_SCIPY = False


_DATATYPE_TO_DTYPE = {
    PointField.INT8: np.int8,
    PointField.UINT8: np.uint8,
    PointField.INT16: np.int16,
    PointField.UINT16: np.uint16,
    PointField.INT32: np.int32,
    PointField.UINT32: np.uint32,
    PointField.FLOAT32: np.float32,
    PointField.FLOAT64: np.float64,
}


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def wrap_angle(a: float) -> float:
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def blend_angle(a: float, b: float, wb: float) -> float:
    """Return angle between a and b, with wb weight on b."""
    return wrap_angle(a + clamp(wb, 0.0, 1.0) * wrap_angle(b - a))


def yaw_to_rot2(yaw: float) -> np.ndarray:
    c = math.cos(yaw)
    s = math.sin(yaw)
    return np.array([[c, -s], [s, c]], dtype=np.float64)


def best_fit_2d(src_xy: np.ndarray, dst_xy: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Rigid transform src -> dst in XY using SVD."""
    src_cent = src_xy.mean(axis=0)
    dst_cent = dst_xy.mean(axis=0)
    src0 = src_xy - src_cent
    dst0 = dst_xy - dst_cent
    H = src0.T @ dst0
    U, _S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1.0
        R = Vt.T @ U.T
    t = dst_cent - (R @ src_cent)
    return R, t


def pointcloud2_xyz_array(msg: PointCloud2) -> np.ndarray:
    """Fast numpy extraction of x/y/z from a PointCloud2 message."""
    if not msg.fields or not msg.data:
        return np.empty((0, 3), dtype=np.float64)
    names = {f.name: f for f in msg.fields}
    if not all(k in names for k in ("x", "y", "z")):
        return np.empty((0, 3), dtype=np.float64)

    dtype_fields = []
    for f in sorted(msg.fields, key=lambda ff: ff.offset):
        np_dtype = _DATATYPE_TO_DTYPE.get(f.datatype)
        if np_dtype is None:
            continue
        count = max(1, int(f.count))
        dtype_fields.append((f.name, np_dtype, (count,)) if count > 1 else (f.name, np_dtype))
    try:
        dtype = np.dtype(dtype_fields, align=False)
        # Respect point_step by inserting padding when the dtype is smaller.
        if dtype.itemsize != msg.point_step:
            dtype_fields_with_offsets = []
            for f in sorted(msg.fields, key=lambda ff: ff.offset):
                np_dtype = _DATATYPE_TO_DTYPE.get(f.datatype)
                if np_dtype is None:
                    continue
                count = max(1, int(f.count))
                dt = np.dtype((np_dtype, (count,))) if count > 1 else np.dtype(np_dtype)
                dtype_fields_with_offsets.append((f.name, dt, f.offset))
            dtype = np.dtype({
                'names': [x[0] for x in dtype_fields_with_offsets],
                'formats': [x[1] for x in dtype_fields_with_offsets],
                'offsets': [x[2] for x in dtype_fields_with_offsets],
                'itemsize': msg.point_step,
            })
        count = int(msg.width) * int(msg.height)
        arr = np.frombuffer(msg.data, dtype=dtype, count=count)
        xyz = np.vstack((arr['x'], arr['y'], arr['z'])).T.astype(np.float64, copy=False)
        return xyz[np.isfinite(xyz).all(axis=1)]
    except Exception as exc:
        rospy.logwarn_throttle(5.0, "[Adaptive-W LVIO] PointCloud2 numpy decode failed: %s", exc)
        return np.empty((0, 3), dtype=np.float64)


class AdaptiveWLVIO:
    def __init__(self):
        self.input_cloud_topic = rospy.get_param("~input_cloud_topic", "/cloud_registered_raw")
        self.input_camera_topic = rospy.get_param("~input_camera_topic", "/camera/right/image_raw")
        self.input_imu_topic = rospy.get_param("~input_imu_topic", "/livox/imu")

        self.output_odom_topic = rospy.get_param("~output_odom_topic", "/adaptive_w_lvio/odometry/mapping")
        self.path_topic = rospy.get_param("~path_topic", "/adaptive_w_lvio/mapping/path")
        self.cloud_out_topic = rospy.get_param("~cloud_out_topic", "/adaptive_w_lvio/cloud_registered")
        self.debug_topic = rospy.get_param("~debug_topic", "/adaptive_w_lvio/debug/weights")

        self.frame_id = rospy.get_param("~frame_id", "camera_init")
        self.child_frame_id = rospy.get_param("~child_frame_id", "body")
        self.publish_tf = bool(rospy.get_param("~publish_tf", True))
        self.max_path_length = int(rospy.get_param("~max_path_length", 200000))

        self.max_sensor_age = float(rospy.get_param("~max_sensor_age", 0.35))
        self.min_cloud_points = float(rospy.get_param("~min_cloud_points", 2500.0))
        self.max_raw_points = int(rospy.get_param("~max_raw_points", 25000))
        self.max_icp_points = int(rospy.get_param("~max_icp_points", 3500))
        self.voxel_size = float(rospy.get_param("~voxel_size", 0.45))
        self.max_corr_dist = float(rospy.get_param("~max_corr_dist", 1.8))
        self.icp_iterations = int(rospy.get_param("~icp_iterations", 8))
        self.max_translation_step = float(rospy.get_param("~max_translation_step", 4.0))
        self.max_yaw_step = float(rospy.get_param("~max_yaw_step_deg", 12.0)) * math.pi / 180.0
        self.log_period = float(rospy.get_param("~log_period", 4.0))

        self.last_camera_stamp: Optional[rospy.Time] = None
        self.last_imu_stamp: Optional[rospy.Time] = None
        self.last_cloud_stamp: Optional[rospy.Time] = None
        self.last_imu_wall_stamp: Optional[rospy.Time] = None
        self.imu_yaw_accum = 0.0
        self.imu_yaw_at_last_cloud = 0.0
        self.last_cloud_points = 0

        self.prev_xy: Optional[np.ndarray] = None
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.yaw = 0.0
        self.count = 0

        self.path = Path()
        self.path.header.frame_id = self.frame_id

        self.pub_odom = rospy.Publisher(self.output_odom_topic, Odometry, queue_size=100)
        self.pub_path = rospy.Publisher(self.path_topic, Path, queue_size=10, latch=True)
        self.pub_cloud = rospy.Publisher(self.cloud_out_topic, PointCloud2, queue_size=10)
        self.pub_debug = rospy.Publisher(self.debug_topic, String, queue_size=10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster() if self.publish_tf else None

        rospy.Subscriber(self.input_cloud_topic, PointCloud2, self.cloud_cb, queue_size=5)
        rospy.Subscriber(self.input_camera_topic, Image, self.camera_cb, queue_size=30)
        rospy.Subscriber(self.input_imu_topic, Imu, self.imu_cb, queue_size=300)

        rospy.loginfo("[Adaptive-W LVIO] independent localisation: cloud=%s camera=%s imu=%s", self.input_cloud_topic, self.input_camera_topic, self.input_imu_topic)
        rospy.loginfo("[Adaptive-W LVIO] output odom=%s path=%s cloud=%s", self.output_odom_topic, self.path_topic, self.cloud_out_topic)
        if not _HAS_SCIPY:
            rospy.logwarn("[Adaptive-W LVIO] scipy unavailable; ICP disabled, IMU-only yaw/no translation fallback will be used")

    def camera_cb(self, msg: Image):
        self.last_camera_stamp = msg.header.stamp

    def imu_cb(self, msg: Imu):
        stamp = msg.header.stamp if msg.header.stamp != rospy.Time(0) else rospy.Time.now()
        if self.last_imu_wall_stamp is not None:
            dt = (stamp - self.last_imu_wall_stamp).to_sec()
            if 0.0 < dt < 0.2:
                self.imu_yaw_accum += float(msg.angular_velocity.z) * dt
        self.last_imu_wall_stamp = stamp
        self.last_imu_stamp = stamp

    def cloud_cb(self, msg: PointCloud2):
        stamp = msg.header.stamp if msg.header.stamp != rospy.Time(0) else rospy.Time.now()
        self.last_cloud_stamp = stamp
        self.last_cloud_points = int(msg.width) * int(msg.height)

        relay = copy.copy(msg)
        relay.header.frame_id = msg.header.frame_id or "velodyne"
        self.pub_cloud.publish(relay)

        points = self._prepare_cloud(msg)
        if points.shape[0] < 150:
            self._publish_pose(stamp, 0.0, 0.0, 0.0, 0.0, "too_few_points")
            return
        curr_xy = points[:, :2]

        imu_delta_yaw = wrap_angle(self.imu_yaw_accum - self.imu_yaw_at_last_cloud)
        self.imu_yaw_at_last_cloud = self.imu_yaw_accum

        lidar_h = self._time_health(stamp, self.last_cloud_stamp) * clamp(float(points.shape[0]) / self.min_cloud_points, 0.0, 1.0)
        visual_h = self._time_health(stamp, self.last_camera_stamp)
        imu_h = self._time_health(stamp, self.last_imu_stamp)

        if self.prev_xy is None:
            self.prev_xy = curr_xy
            self._publish_pose(stamp, lidar_h, visual_h, imu_h, 0.0, "initialised")
            return

        dx_local, dy_local, yaw_icp, fitness, inliers = self._estimate_scan_delta(self.prev_xy, curr_xy, imu_delta_yaw)
        lidar_match_h = clamp((inliers / max(250.0, min(len(self.prev_xy), len(curr_xy)) * 0.25)) * (1.0 - min(fitness, self.max_corr_dist) / self.max_corr_dist), 0.0, 1.0)
        lidar_h = 0.5 * lidar_h + 0.5 * lidar_match_h

        raw_lidar = 0.62 * lidar_h + 0.03
        raw_visual = 0.18 * visual_h + 0.02
        raw_imu = 0.20 * imu_h + 0.03
        total = max(raw_lidar + raw_visual + raw_imu, 1e-6)
        w_lidar = raw_lidar / total
        w_visual = raw_visual / total
        w_imu = raw_imu / total

        # Blend ICP yaw with IMU yaw. Translation comes from ICP but is damped
        # when the scan match is weak, so bad clouds don't create huge jumps.
        yaw_delta = blend_angle(yaw_icp, imu_delta_yaw, w_imu * (1.0 - lidar_match_h))
        yaw_delta = clamp(yaw_delta, -self.max_yaw_step, self.max_yaw_step)
        trans_norm = math.hypot(dx_local, dy_local)
        if trans_norm > self.max_translation_step:
            scale = self.max_translation_step / max(trans_norm, 1e-6)
            dx_local *= scale
            dy_local *= scale
            trans_norm = self.max_translation_step
        trans_scale = clamp(0.35 + 0.65 * lidar_match_h, 0.0, 1.0)
        dx_local *= trans_scale
        dy_local *= trans_scale

        R_world_prev = yaw_to_rot2(self.yaw)
        d_world = R_world_prev @ np.array([dx_local, dy_local], dtype=np.float64)
        self.x += float(d_world[0])
        self.y += float(d_world[1])
        self.z = float(np.median(points[:, 2])) if points.shape[0] else self.z
        self.yaw = wrap_angle(self.yaw + yaw_delta)

        self.prev_xy = curr_xy
        debug = (
            f"icp_fitness={fitness:.3f} inliers={inliers} "
            f"delta_local=({dx_local:.3f},{dy_local:.3f},{math.degrees(yaw_delta):.2f}deg) "
            f"w_lidar={w_lidar:.3f} w_visual={w_visual:.3f} w_imu={w_imu:.3f} "
            f"health_lidar={lidar_h:.3f} health_visual={visual_h:.3f} health_imu={imu_h:.3f} "
            f"points={points.shape[0]}"
        )
        self._publish_pose(stamp, lidar_h, visual_h, imu_h, w_lidar, debug)

    def _prepare_cloud(self, msg: PointCloud2) -> np.ndarray:
        pts = pointcloud2_xyz_array(msg)
        if pts.size == 0:
            return np.empty((0, 3), dtype=np.float64)
        r = np.linalg.norm(pts[:, :2], axis=1)
        mask = (r > 1.0) & (r < 75.0) & (pts[:, 2] > -3.0) & (pts[:, 2] < 5.0)
        pts = pts[mask]
        if pts.shape[0] > self.max_raw_points:
            stride = int(math.ceil(pts.shape[0] / float(self.max_raw_points)))
            pts = pts[::stride]
        if pts.shape[0] == 0:
            return pts
        if self.voxel_size > 0.0:
            keys = np.floor(pts[:, :3] / self.voxel_size).astype(np.int32)
            _, idx = np.unique(keys, axis=0, return_index=True)
            pts = pts[np.sort(idx)]
        if pts.shape[0] > self.max_icp_points:
            stride = int(math.ceil(pts.shape[0] / float(self.max_icp_points)))
            pts = pts[::stride]
        return pts.astype(np.float64, copy=False)

    def _estimate_scan_delta(self, prev_xy: np.ndarray, curr_xy: np.ndarray, imu_delta_yaw: float):
        if not _HAS_SCIPY or prev_xy.shape[0] < 100 or curr_xy.shape[0] < 100:
            return 0.0, 0.0, imu_delta_yaw, self.max_corr_dist, 0
        R = yaw_to_rot2(imu_delta_yaw)
        t = np.zeros(2, dtype=np.float64)
        tree = cKDTree(prev_xy)
        best_fitness = self.max_corr_dist
        best_inliers = 0
        for _ in range(max(1, self.icp_iterations)):
            transformed = curr_xy @ R.T + t
            dist, idx = tree.query(transformed, k=1, distance_upper_bound=self.max_corr_dist)
            valid = np.isfinite(dist) & (idx < prev_xy.shape[0]) & (dist < self.max_corr_dist)
            inliers = int(valid.sum())
            if inliers < 50:
                break
            src = curr_xy[valid]
            dst = prev_xy[idx[valid]]
            R, t = best_fit_2d(src, dst)
            best_fitness = float(np.median(dist[valid]))
            best_inliers = inliers
        yaw = math.atan2(R[1, 0], R[0, 0])
        return float(t[0]), float(t[1]), wrap_angle(yaw), best_fitness, best_inliers

    def _publish_pose(self, stamp, lidar_h, visual_h, imu_h, w_lidar, debug):
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self.frame_id
        odom.child_frame_id = self.child_frame_id
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = self.z
        q = quaternion_from_euler(0.0, 0.0, self.yaw)
        odom.pose.pose.orientation.x = q[0]
        odom.pose.pose.orientation.y = q[1]
        odom.pose.pose.orientation.z = q[2]
        odom.pose.pose.orientation.w = q[3]
        self.pub_odom.publish(odom)

        pose_stamped = PoseStamped()
        pose_stamped.header = odom.header
        pose_stamped.pose = odom.pose.pose
        self.path.header.stamp = stamp
        self.path.poses.append(pose_stamped)
        if self.max_path_length > 0 and len(self.path.poses) > self.max_path_length:
            self.path.poses = self.path.poses[-self.max_path_length:]
        self.pub_path.publish(self.path)

        if self.publish_tf:
            tf_msg = TransformStamped()
            tf_msg.header.stamp = stamp
            tf_msg.header.frame_id = self.frame_id
            tf_msg.child_frame_id = self.child_frame_id
            tf_msg.transform.translation.x = self.x
            tf_msg.transform.translation.y = self.y
            tf_msg.transform.translation.z = self.z
            tf_msg.transform.rotation = odom.pose.pose.orientation
            self.tf_broadcaster.sendTransform(tf_msg)

        self.count += 1
        text = f"stamp={stamp.to_sec():.6f} pose=({self.x:.3f},{self.y:.3f},{math.degrees(self.yaw):.2f}deg) {debug}"
        self.pub_debug.publish(String(data=text))
        if self.count == 1:
            rospy.loginfo("[Adaptive-W LVIO] first independent odometry at %.9f", stamp.to_sec())
        rospy.loginfo_throttle(self.log_period, "[Adaptive-W LVIO] %s", text)

    def _time_health(self, current: rospy.Time, stamp: Optional[rospy.Time]) -> float:
        if stamp is None or stamp == rospy.Time(0):
            return 0.0
        age = abs((current - stamp).to_sec())
        if age >= self.max_sensor_age:
            return 0.0
        return clamp(1.0 - age / self.max_sensor_age, 0.0, 1.0)


def main():
    rospy.init_node("adaptive_w_lvio_node", anonymous=False)
    AdaptiveWLVIO()
    rospy.spin()


if __name__ == "__main__":
    main()
