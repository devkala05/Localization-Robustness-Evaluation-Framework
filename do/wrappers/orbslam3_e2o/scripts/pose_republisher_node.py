#!/usr/bin/env python3
"""Normalize the native ORB-SLAM3 monocular camera pose for external fusion.

The upstream ROS example is patched only to expose its already-computed Twc pose.
This node preserves the estimator timestamp, rejects malformed/jumping poses,
and publishes the independent trajectory in E2O body axes. Metric scale remains
the responsibility of the external fusion node.
"""
import copy
import math
import threading
import time

import numpy as np
import rospy
import transforms3d
from geometry_msgs.msg import Pose, PoseStamped
from nav_msgs.msg import Odometry, Path
from sensor_msgs import point_cloud2
from sensor_msgs.msg import PointCloud, PointCloud2
from std_msgs.msg import String

# Supplied E2O calibration: p_camera = R_camera_body * p_body + t_camera_body.
# The body is lidar103 until a measured IMU/lidar transform becomes available.
E2O_CAMERA_T_BODY = np.array([
    [-0.18256836, -0.98306216, -0.01604916, 0.07383026],
    [0.11110754, -0.00440978, -0.99379861, -0.5358112],
    [0.97689503, -0.18321936, 0.1100307, -0.31010858],
    [0.0, 0.0, 0.0, 1.0],
], dtype=float)

# Visualization-only world basis: ORB optical x/right, y/down, z/forward to
# ROS x/forward, y/left, z/up. No translation or monocular scale is applied.
ORB_WORLD_T_GRID = np.array([
    [0.0, 0.0, 1.0, 0.0],
    [-1.0, 0.0, 0.0, 0.0],
    [0.0, -1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0],
], dtype=float)


def as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def pose_to_matrix(pose: Pose) -> np.ndarray:
    values = [pose.position.x, pose.position.y, pose.position.z,
              pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w]
    if not np.all(np.isfinite(values)):
        raise ValueError("non-finite pose")
    q = np.asarray([pose.orientation.w, pose.orientation.x, pose.orientation.y, pose.orientation.z], dtype=float)
    norm = float(np.linalg.norm(q))
    if norm < 1.0e-12:
        raise ValueError("zero quaternion")
    q /= norm
    T = np.eye(4)
    T[:3, :3] = transforms3d.quaternions.quat2mat(q)
    T[:3, 3] = values[:3]
    return T


def matrix_to_pose(T: np.ndarray) -> Pose:
    q = transforms3d.quaternions.mat2quat(T[:3, :3])  # wxyz
    out = Pose()
    out.position.x, out.position.y, out.position.z = map(float, T[:3, 3])
    out.orientation.w, out.orientation.x, out.orientation.y, out.orientation.z = map(float, q)
    return out


def invert_rigid(T: np.ndarray) -> np.ndarray:
    out = np.eye(4)
    out[:3, :3] = T[:3, :3].T
    out[:3, 3] = -(out[:3, :3] @ T[:3, 3])
    return out


def camera_pose_to_body(T_world_camera: np.ndarray) -> np.ndarray:
    """Convert the ORB optical-camera pose to the calibrated E2O body pose."""
    return T_world_camera @ E2O_CAMERA_T_BODY


def rotation_angle(R: np.ndarray) -> float:
    value = min(1.0, max(-1.0, (float(np.trace(R)) - 1.0) * 0.5))
    return math.acos(value)


class PoseRepublisher:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.input_topic = str(rospy.get_param("~input_topic", "/orb_slam3/camera_pose"))
        self.output_odom_topic = str(rospy.get_param("~output_odom_topic", "/orbslam3/camera_odometry"))
        self.output_path_topic = str(rospy.get_param("~output_path_topic", "/orbslam3/camera_path"))
        self.status_topic = str(rospy.get_param("~status_topic", "/orbslam3/tracking_status"))
        self.input_map_topic = str(rospy.get_param("~input_map_topic", "/orb_slam3/map_points"))
        self.output_map_topic = str(rospy.get_param("~output_map_topic", "/orbslam3/map_points"))
        self.raw_odom_topic = str(rospy.get_param("~raw_odom_topic", "/orbslam3/raw_camera_odometry"))
        self.raw_path_topic = str(rospy.get_param("~raw_path_topic", "/orbslam3/raw_camera_path"))
        self.raw_map_topic = str(rospy.get_param("~raw_map_topic", "/orbslam3/raw_map_points"))
        self.grid_odom_topic = str(rospy.get_param("~grid_odom_topic", "/orbslam3/raw_grid_odometry"))
        self.grid_path_topic = str(rospy.get_param("~grid_path_topic", "/orbslam3/raw_grid_path"))
        self.grid_map_topic = str(rospy.get_param("~grid_map_topic", "/orbslam3/raw_grid_map_points"))
        self.input_keyframe_path_topic = str(
            rospy.get_param("~input_keyframe_path_topic", "/orb_slam3/keyframe_path")
        )
        self.grid_keyframe_path_topic = str(
            rospy.get_param("~grid_keyframe_path_topic", "/orbslam3/corrected_grid_keyframe_path")
        )
        self.world_frame = str(rospy.get_param("~world_frame_id", "orbslam3_map"))
        self.body_frame = str(rospy.get_param("~body_frame_id", "base_link"))
        self.use_camera_to_body_extrinsic = as_bool(
            rospy.get_param("~use_camera_to_body_extrinsic", True)
        )
        self.normalize_to_start = as_bool(rospy.get_param("~normalize_to_start", True))
        self.fixed_pose_scale = float(rospy.get_param("~fixed_pose_scale", 1.0))
        self.max_jump = float(rospy.get_param("~max_interframe_translation", 5.0))
        self.max_speed = float(rospy.get_param("~max_speed_mps", 45.0))
        self.max_angular_speed = math.radians(float(rospy.get_param("~max_angular_speed_deg_s", 360.0)))
        self.tracking_timeout = float(rospy.get_param("~tracking_timeout_sec", 2.0))
        self.max_path_poses = int(rospy.get_param("~max_path_poses", 50000))
        self.reanchor_on_discontinuity = as_bool(
            rospy.get_param("~reanchor_on_discontinuity", True)
        )
        self.map_voxel_size = float(rospy.get_param("~map_voxel_size", 0.08))
        self.max_map_points = int(rospy.get_param("~max_map_points", 200000))
        self.map_publish_period = float(rospy.get_param("~map_publish_period_sec", 0.5))
        self.path_publish_period = float(rospy.get_param("~path_publish_period_sec", 0.5))

        self.odom_pub = rospy.Publisher(self.output_odom_topic, Odometry, queue_size=100)
        self.path_pub = rospy.Publisher(self.output_path_topic, Path, queue_size=5, latch=True)
        self.status_pub = rospy.Publisher(self.status_topic, String, queue_size=10, latch=True)
        self.map_pub = rospy.Publisher(self.output_map_topic, PointCloud2, queue_size=2)
        self.raw_odom_pub = rospy.Publisher(self.raw_odom_topic, Odometry, queue_size=100)
        self.raw_path_pub = rospy.Publisher(self.raw_path_topic, Path, queue_size=5, latch=True)
        self.raw_map_pub = rospy.Publisher(self.raw_map_topic, PointCloud2, queue_size=2)
        self.grid_odom_pub = rospy.Publisher(self.grid_odom_topic, Odometry, queue_size=100)
        self.grid_path_pub = rospy.Publisher(self.grid_path_topic, Path, queue_size=5, latch=True)
        self.grid_map_pub = rospy.Publisher(self.grid_map_topic, PointCloud2, queue_size=2)
        self.grid_keyframe_path_pub = rospy.Publisher(
            self.grid_keyframe_path_topic, Path, queue_size=2, latch=True
        )
        self.path = Path()
        self.path.header.frame_id = self.world_frame
        self.raw_path = Path()
        self.raw_path.header.frame_id = "orbslam3_map"
        self.grid_path = Path()
        self.grid_path.header.frame_id = "orbslam3_grid"
        self.origin_inverse = None
        self.continuity = np.eye(4)
        self.accumulated_map = {}
        self.last_map_publish_wall = 0.0
        self.last_path_publish_wall = 0.0
        self.last_raw_path_publish_wall = 0.0
        self.last_T = None
        self.last_stamp = None
        self.last_receipt_wall = None
        self.received = 0
        self.rejected = 0

        rospy.Subscriber(self.input_topic, PoseStamped, self.pose_cb, queue_size=100)
        rospy.Subscriber(self.input_map_topic, PointCloud, self.map_cb, queue_size=2)
        rospy.Subscriber(self.input_keyframe_path_topic, Path, self.keyframe_path_cb, queue_size=2)
        rospy.Timer(rospy.Duration(0.5), self.watchdog_cb)
        rospy.loginfo("[ORBWrapper] camera pose=%s -> odom=%s; scale remains external",
                      self.input_topic, self.output_odom_topic)

    def pose_cb(self, msg: PoseStamped) -> None:
        with self.lock:
            self.received += 1
            stamp = msg.header.stamp
            if stamp == rospy.Time(0):
                self.reject("ZERO_TIMESTAMP")
                return
            try:
                T = pose_to_matrix(msg.pose)
            except ValueError:
                self.reject("INVALID_POSE")
                return
            self.publish_raw_pose(msg)
            if self.use_camera_to_body_extrinsic:
                T = camera_pose_to_body(T)
            if self.origin_inverse is None and self.normalize_to_start:
                self.origin_inverse = invert_rigid(T)
            if self.origin_inverse is not None:
                T = self.origin_inverse @ T
            T[:3, 3] *= self.fixed_pose_scale
            T = self.continuity @ T

            if self.last_stamp is not None:
                dt = (stamp - self.last_stamp).to_sec()
                if dt <= 0.0:
                    self.reject("OUT_OF_ORDER")
                    return
                delta = invert_rigid(self.last_T) @ T
                jump = float(np.linalg.norm(T[:3, 3] - self.last_T[:3, 3]))
                angular_speed = rotation_angle(delta[:3, :3]) / dt
                if jump > self.max_jump or jump / dt > self.max_speed or angular_speed > self.max_angular_speed:
                    if not self.reanchor_on_discontinuity:
                        self.reject("DISCONTINUITY")
                        return
                    # ORB loop closure/relocalization can correct its map frame in
                    # one update. Preserve the published trajectory continuously
                    # instead of rejecting every subsequent corrected pose.
                    raw_T = invert_rigid(self.continuity) @ T
                    self.continuity = self.last_T @ invert_rigid(raw_T)
                    T = self.continuity @ raw_T
                    self.accumulated_map.clear()
                    rospy.logwarn("[ORBWrapper] map-frame correction re-anchored continuously")

            odom = Odometry()
            odom.header.stamp = stamp
            odom.header.frame_id = self.world_frame
            odom.child_frame_id = self.body_frame
            odom.pose.pose = matrix_to_pose(T)
            # Monocular translation scale is unobservable. Large covariance flags
            # that this stream must not be consumed as metric odometry directly.
            odom.pose.covariance = [0.0] * 36
            for index, value in ((0, 1.0), (7, 1.0), (14, 1.0), (21, 0.05), (28, 0.05), (35, 0.05)):
                odom.pose.covariance[index] = value
            self.odom_pub.publish(odom)

            pose = PoseStamped()
            pose.header = odom.header
            pose.pose = odom.pose.pose
            self.path.header.stamp = stamp
            self.path.poses.append(pose)
            if len(self.path.poses) > self.max_path_poses:
                self.path.poses = self.path.poses[-self.max_path_poses:]
            now = time.monotonic()
            if now - self.last_path_publish_wall >= self.path_publish_period:
                self.last_path_publish_wall = now
                self.path_pub.publish(self.path)

            self.last_T = T
            self.last_stamp = stamp
            self.last_receipt_wall = time.monotonic()
            self.status_pub.publish(String(data="TRACKING"))

    def publish_raw_pose(self, msg: PoseStamped) -> None:
        """Publish native Twc exactly as ORB-SLAM3 produced it."""
        odom = Odometry()
        odom.header = copy.deepcopy(msg.header)
        odom.header.frame_id = "orbslam3_map"
        odom.child_frame_id = "camera_color_optical_frame"
        odom.pose.pose = msg.pose
        self.raw_odom_pub.publish(odom)
        pose = PoseStamped()
        pose.header = copy.deepcopy(odom.header)
        pose.pose = msg.pose
        self.raw_path.header.stamp = msg.header.stamp
        self.raw_path.poses.append(pose)
        if len(self.raw_path.poses) > self.max_path_poses:
            self.raw_path.poses = self.raw_path.poses[-self.max_path_poses:]

        grid_T = ORB_WORLD_T_GRID @ pose_to_matrix(msg.pose)
        grid_odom = Odometry()
        grid_odom.header = copy.deepcopy(msg.header)
        grid_odom.header.frame_id = "orbslam3_grid"
        grid_odom.child_frame_id = "camera_color_optical_frame"
        grid_odom.pose.pose = matrix_to_pose(grid_T)
        self.grid_odom_pub.publish(grid_odom)
        grid_pose = PoseStamped()
        grid_pose.header = copy.deepcopy(grid_odom.header)
        grid_pose.pose = grid_odom.pose.pose
        self.grid_path.header.stamp = msg.header.stamp
        self.grid_path.poses.append(grid_pose)
        if len(self.grid_path.poses) > self.max_path_poses:
            self.grid_path.poses = self.grid_path.poses[-self.max_path_poses:]
        now = time.monotonic()
        if now - self.last_raw_path_publish_wall >= self.path_publish_period:
            self.last_raw_path_publish_wall = now
            self.raw_path_pub.publish(self.raw_path)
            self.grid_path_pub.publish(self.grid_path)

    def map_cb(self, msg: PointCloud) -> None:
        with self.lock:
            if not msg.points:
                return
            points = np.asarray([[point.x, point.y, point.z] for point in msg.points], dtype=float)
            points = points[np.all(np.isfinite(points), axis=1)]
            if not points.size:
                return
            raw_header = copy.deepcopy(msg.header)
            raw_header.frame_id = "orbslam3_map"
            self.raw_map_pub.publish(point_cloud2.create_cloud_xyz32(raw_header, points.tolist()))
            grid_points = (ORB_WORLD_T_GRID[:3, :3] @ points.T).T
            grid_header = copy.deepcopy(msg.header)
            grid_header.frame_id = "orbslam3_grid"
            self.grid_map_pub.publish(
                point_cloud2.create_cloud_xyz32(grid_header, grid_points.tolist())
            )
            if self.origin_inverse is None:
                return
            normalized = (self.origin_inverse[:3, :3] @ points.T).T + self.origin_inverse[:3, 3]
            normalized *= self.fixed_pose_scale
            normalized = (self.continuity[:3, :3] @ normalized.T).T + self.continuity[:3, 3]
            voxel = max(self.map_voxel_size, 1.0e-4)
            for point in normalized:
                key = tuple(np.floor(point / voxel).astype(np.int64))
                self.accumulated_map[key] = point
            if len(self.accumulated_map) > self.max_map_points:
                self.accumulated_map.clear()
                for point in normalized:
                    key = tuple(np.floor(point / voxel).astype(np.int64))
                    self.accumulated_map[key] = point
            now = time.monotonic()
            if now - self.last_map_publish_wall < self.map_publish_period:
                return
            self.last_map_publish_wall = now
            msg.header.frame_id = self.world_frame
            cloud = [point.tolist() for point in self.accumulated_map.values()]
            self.map_pub.publish(point_cloud2.create_cloud_xyz32(msg.header, cloud))

    def keyframe_path_cb(self, msg: Path) -> None:
        """Rotate ORB's currently optimized keyframe path onto the RViz grid."""
        output = Path()
        output.header = copy.deepcopy(msg.header)
        output.header.frame_id = "orbslam3_grid"
        for source in msg.poses:
            target = PoseStamped()
            target.header = copy.deepcopy(output.header)
            target.header.stamp = source.header.stamp
            target.pose = matrix_to_pose(ORB_WORLD_T_GRID @ pose_to_matrix(source.pose))
            output.poses.append(target)
        self.grid_keyframe_path_pub.publish(output)

    def reject(self, reason: str) -> None:
        self.rejected += 1
        self.status_pub.publish(String(data=reason))
        rospy.logwarn_throttle(2.0, "[ORBWrapper] rejected pose: %s", reason)

    def watchdog_cb(self, _event) -> None:
        with self.lock:
            if self.last_receipt_wall is None:
                status = "WAITING"
            elif time.monotonic() - self.last_receipt_wall > self.tracking_timeout:
                status = "LOST"
            else:
                status = "TRACKING"
            self.status_pub.publish(String(data=status))


def main() -> None:
    rospy.init_node("orbslam3_pose_republisher")
    PoseRepublisher()
    rospy.spin()


if __name__ == "__main__":
    main()
