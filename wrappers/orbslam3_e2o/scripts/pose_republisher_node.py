#!/usr/bin/env python3
"""Republish ORB-SLAM3 RGB-D outputs in ROS/body axes without scaling.

The upstream RGB-D node publishes the current camera pose and optimized
keyframe path in camera optical axes. This wrapper keeps raw native topics for
recording, and publishes the main ORB topics with only a fixed optical-to-body
axis remap so forward motion appears in the same X/Y ground-plane convention as
the LiDAR-based estimators. It does not use ground truth, normalize starts,
fit scale, or continuity-correct ORB-SLAM3 poses.
"""
import copy
import math
import threading
import time
from collections import deque

import numpy as np
import rospy
from geometry_msgs.msg import Pose, PoseStamped
from nav_msgs.msg import Odometry, Path
from sensor_msgs import point_cloud2
from sensor_msgs.msg import PointCloud, PointCloud2
from std_msgs.msg import String

OPTICAL_TO_BODY = np.array([
    [0.0, 0.0, 1.0, 0.0],
    [-1.0, 0.0, 0.0, 0.0],
    [0.0, -1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0],
], dtype=float)


def yaw_rotation(degrees: float) -> np.ndarray:
    angle = math.radians(degrees)
    c = math.cos(angle)
    s = math.sin(angle)
    out = np.eye(4)
    out[:3, :3] = np.array([
        [c, -s, 0.0],
        [s, c, 0.0],
        [0.0, 0.0, 1.0],
    ], dtype=float)
    return out


def pose_values_finite(pose) -> bool:
    values = (
        pose.position.x, pose.position.y, pose.position.z,
        pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w,
    )
    return all(math.isfinite(value) for value in values)


def quaternion_valid(pose) -> bool:
    q = pose.orientation
    norm = math.sqrt(q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w)
    return math.isfinite(norm) and norm > 1.0e-12


def pose_to_matrix(pose: Pose) -> np.ndarray:
    q = pose.orientation
    x, y, z, w = np.asarray([q.x, q.y, q.z, q.w], dtype=float)
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    x, y, z, w = x / norm, y / norm, z / norm, w / norm
    out = np.eye(4)
    out[:3, :3] = np.array([
        [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
        [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
        [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
    ], dtype=float)
    out[:3, 3] = [pose.position.x, pose.position.y, pose.position.z]
    return out


def matrix_to_pose(transform: np.ndarray) -> Pose:
    m = transform[:3, :3]
    trace = float(np.trace(m))
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        qw = 0.25 * s
        qx = (m[2, 1] - m[1, 2]) / s
        qy = (m[0, 2] - m[2, 0]) / s
        qz = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
        qw = (m[2, 1] - m[1, 2]) / s
        qx = 0.25 * s
        qy = (m[0, 1] + m[1, 0]) / s
        qz = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
        qw = (m[0, 2] - m[2, 0]) / s
        qx = (m[0, 1] + m[1, 0]) / s
        qy = 0.25 * s
        qz = (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
        qw = (m[1, 0] - m[0, 1]) / s
        qx = (m[0, 2] + m[2, 0]) / s
        qy = (m[1, 2] + m[2, 1]) / s
        qz = 0.25 * s
    norm = math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw)
    pose = Pose()
    pose.position.x, pose.position.y, pose.position.z = map(float, transform[:3, 3])
    pose.orientation.x = float(qx / norm)
    pose.orientation.y = float(qy / norm)
    pose.orientation.z = float(qz / norm)
    pose.orientation.w = float(qw / norm)
    return pose


def optical_pose_to_body_axes(pose: Pose, yaw_offset_deg: float = 0.0) -> Pose:
    return matrix_to_pose(yaw_rotation(yaw_offset_deg) @ OPTICAL_TO_BODY @ pose_to_matrix(pose))


def apply_yaw_about_pivot(transform: np.ndarray, yaw_offset_deg: float, pivot: np.ndarray) -> np.ndarray:
    yaw = yaw_rotation(yaw_offset_deg)
    out = transform.copy()
    out[:3, :3] = yaw[:3, :3] @ out[:3, :3]
    out[:3, 3] = pivot + yaw[:3, :3] @ (out[:3, 3] - pivot)
    return out


def rotation_angle(transform_a: np.ndarray, transform_b: np.ndarray) -> float:
    delta = transform_a[:3, :3].T @ transform_b[:3, :3]
    value = (float(np.trace(delta)) - 1.0) * 0.5
    return math.acos(max(-1.0, min(1.0, value)))


class PoseRepublisher:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.input_topic = str(rospy.get_param("~input_topic", "/orb_slam3/camera_pose"))
        self.input_keyframe_path_topic = str(
            rospy.get_param("~input_keyframe_path_topic", "/orb_slam3/keyframe_path")
        )
        self.input_map_topic = str(rospy.get_param("~input_map_topic", "/orb_slam3/map_points"))
        self.output_odom_topic = str(rospy.get_param("~output_odom_topic", "/orbslam3/camera_odometry"))
        self.output_path_topic = str(rospy.get_param("~output_path_topic", "/orbslam3/camera_path"))
        self.optimized_path_topic = str(
            rospy.get_param("~optimized_path_topic", "/orbslam3/optimized_camera_path")
        )
        self.live_path_topic = str(rospy.get_param("~live_path_topic", "/orbslam3/live_camera_path"))
        self.output_map_topic = str(rospy.get_param("~output_map_topic", "/orbslam3/map_points"))
        self.raw_odom_topic = str(rospy.get_param("~raw_odom_topic", "/orbslam3/raw_camera_odometry"))
        self.raw_path_topic = str(rospy.get_param("~raw_path_topic", "/orbslam3/raw_camera_path"))
        self.raw_map_topic = str(rospy.get_param("~raw_map_topic", "/orbslam3/raw_map_points"))
        self.status_topic = str(rospy.get_param("~status_topic", "/orbslam3/tracking_status"))
        self.world_frame = str(rospy.get_param("~world_frame_id", "orbslam3_map"))
        self.camera_frame = str(rospy.get_param("~camera_frame_id", "camera_color_optical_frame"))
        self.body_frame = str(rospy.get_param("~body_frame_id", "base_link"))
        self.body_yaw_offset_deg = float(rospy.get_param("~body_yaw_offset_deg", 180.0))
        self.tracking_timeout = float(rospy.get_param("~tracking_timeout_sec", 2.0))
        self.max_path_poses = int(rospy.get_param("~max_path_poses", 50000))
        self.path_publish_period = float(rospy.get_param("~path_publish_period_sec", 0.5))
        self.max_step_m = float(rospy.get_param("~max_step_m", 1.25))
        self.max_gap_step_m = float(rospy.get_param("~max_gap_step_m", 3.0))
        self.max_speed_mps = float(rospy.get_param("~max_speed_mps", 12.0))
        self.max_yaw_step_deg = float(rospy.get_param("~max_yaw_step_deg", 45.0))
        self.max_backtrack_m = float(rospy.get_param("~max_backtrack_m", 0.75))
        self.velocity_window = int(rospy.get_param("~velocity_window", 6))
        self.min_backtrack_speed_mps = float(rospy.get_param("~min_backtrack_speed_mps", 0.3))

        self.odom_pub = rospy.Publisher(self.output_odom_topic, Odometry, queue_size=100)
        self.path_pub = rospy.Publisher(self.output_path_topic, Path, queue_size=5, latch=True)
        self.optimized_path_pub = rospy.Publisher(self.optimized_path_topic, Path, queue_size=5, latch=True)
        self.live_path_pub = rospy.Publisher(self.live_path_topic, Path, queue_size=5, latch=True)
        self.map_pub = rospy.Publisher(self.output_map_topic, PointCloud2, queue_size=2)
        self.raw_odom_pub = rospy.Publisher(self.raw_odom_topic, Odometry, queue_size=100)
        self.raw_path_pub = rospy.Publisher(self.raw_path_topic, Path, queue_size=5, latch=True)
        self.raw_map_pub = rospy.Publisher(self.raw_map_topic, PointCloud2, queue_size=2)
        self.status_pub = rospy.Publisher(self.status_topic, String, queue_size=10, latch=True)

        self.raw_path = Path()
        self.raw_path.header.frame_id = self.world_frame
        self.live_path = Path()
        self.live_path.header.frame_id = self.world_frame
        self.live_start_pivot = None
        self.last_path_publish_wall = 0.0
        self.last_receipt_wall = None
        self.last_stamp = None
        self.last_body_transform = None
        self.recent_velocities = deque(maxlen=max(2, self.velocity_window))
        self.received = 0
        self.rejected = 0

        rospy.Subscriber(self.input_topic, PoseStamped, self.pose_cb, queue_size=100)
        rospy.Subscriber(self.input_keyframe_path_topic, Path, self.keyframe_path_cb, queue_size=2)
        rospy.Subscriber(self.input_map_topic, PointCloud, self.map_cb, queue_size=2)
        rospy.Timer(rospy.Duration(0.5), self.watchdog_cb)
        rospy.loginfo("[ORBWrapper] RGB-D optical pose=%s -> body-axis odom=%s path=%s yaw_offset=%.1fdeg",
                      self.input_topic, self.output_odom_topic, self.output_path_topic,
                      self.body_yaw_offset_deg)

    def pose_cb(self, msg: PoseStamped) -> None:
        with self.lock:
            self.received += 1
            stamp = msg.header.stamp
            if stamp == rospy.Time(0):
                self.reject("ZERO_TIMESTAMP")
                return
            if self.last_stamp is not None and stamp <= self.last_stamp:
                self.reject("OUT_OF_ORDER")
                return
            if not pose_values_finite(msg.pose) or not quaternion_valid(msg.pose):
                self.reject("INVALID_POSE")
                return

            raw_odom = Odometry()
            raw_odom.header = copy.deepcopy(msg.header)
            raw_odom.header.frame_id = self.world_frame
            raw_odom.child_frame_id = self.camera_frame
            raw_odom.pose.pose = copy.deepcopy(msg.pose)
            raw_odom.pose.covariance = [0.0] * 36
            for index, value in ((0, 0.5), (7, 0.5), (14, 0.5), (21, 0.05), (28, 0.05), (35, 0.05)):
                raw_odom.pose.covariance[index] = value

            body_transform = OPTICAL_TO_BODY @ pose_to_matrix(msg.pose)
            if self.live_start_pivot is None:
                self.live_start_pivot = body_transform[:3, 3].copy()
            body_transform = apply_yaw_about_pivot(
                body_transform, self.body_yaw_offset_deg, self.live_start_pivot
            )
            if self.unstable_body_pose(body_transform, stamp):
                self.reject("UNSTABLE_POSE")
                return

            body_odom = copy.deepcopy(raw_odom)
            body_odom.child_frame_id = self.body_frame
            body_odom.pose.pose = matrix_to_pose(body_transform)

            self.odom_pub.publish(body_odom)
            self.raw_odom_pub.publish(raw_odom)

            pose = PoseStamped()
            pose.header = copy.deepcopy(raw_odom.header)
            pose.pose = copy.deepcopy(msg.pose)
            live_pose = PoseStamped()
            live_pose.header = copy.deepcopy(body_odom.header)
            live_pose.pose = copy.deepcopy(body_odom.pose.pose)
            self.raw_path.header.stamp = stamp
            self.raw_path.poses.append(pose)
            if len(self.raw_path.poses) > self.max_path_poses:
                self.raw_path.poses = self.raw_path.poses[-self.max_path_poses:]
            self.live_path.header.stamp = stamp
            self.live_path.poses.append(live_pose)
            if len(self.live_path.poses) > self.max_path_poses:
                self.live_path.poses = self.live_path.poses[-self.max_path_poses:]

            now = time.monotonic()
            if now - self.last_path_publish_wall >= self.path_publish_period:
                self.last_path_publish_wall = now
                self.raw_path_pub.publish(self.raw_path)
                self.path_pub.publish(self.live_path)
                self.live_path_pub.publish(self.live_path)

            self.last_stamp = stamp
            self.last_body_transform = body_transform.copy()
            self.last_receipt_wall = now
            self.status_pub.publish(String(data="TRACKING"))

    def unstable_body_pose(self, transform: np.ndarray, stamp) -> bool:
        if self.last_body_transform is None or self.last_stamp is None:
            return False
        dt = (stamp - self.last_stamp).to_sec()
        if dt <= 1.0e-4:
            return True
        delta = transform[:3, 3] - self.last_body_transform[:3, 3]
        step = float(np.linalg.norm(delta))
        speed = step / dt
        angle_deg = math.degrees(rotation_angle(self.last_body_transform, transform))
        step_limit = self.max_step_m if dt <= 0.5 else self.max_gap_step_m
        step_too_large = step > step_limit
        if step_too_large or speed > self.max_speed_mps or angle_deg > self.max_yaw_step_deg:
            rospy.logwarn_throttle(
                2.0,
                "[ORBWrapper] unstable pose step=%.3fm speed=%.2fm/s rot=%.1fdeg dt=%.3fs",
                step, speed, angle_deg, dt,
            )
            return True
        if self.recent_velocities:
            mean_velocity = np.mean(np.asarray(self.recent_velocities), axis=0)
            mean_speed = float(np.linalg.norm(mean_velocity))
            if mean_speed >= self.min_backtrack_speed_mps:
                backtrack = -float(np.dot(delta, mean_velocity / mean_speed))
                if backtrack > self.max_backtrack_m:
                    rospy.logwarn_throttle(
                        2.0,
                        "[ORBWrapper] unstable backtrack=%.3fm mean_speed=%.2fm/s",
                        backtrack, mean_speed,
                    )
                    return True
        self.recent_velocities.append(delta / dt)
        return False

    def keyframe_path_cb(self, msg: Path) -> None:
        """Publish ORB-SLAM3's optimized keyframe path in body axes around its start pose."""
        out = Path()
        out.header = copy.deepcopy(msg.header)
        out.header.frame_id = self.world_frame
        body_transforms = []
        source_poses = []
        for source in msg.poses:
            if not pose_values_finite(source.pose) or not quaternion_valid(source.pose):
                continue
            body_transforms.append(OPTICAL_TO_BODY @ pose_to_matrix(source.pose))
            source_poses.append(source)
        if not body_transforms:
            self.optimized_path_pub.publish(out)
            return
        pivot = body_transforms[0][:3, 3].copy()
        for source, body_transform in zip(source_poses, body_transforms):
            pose = PoseStamped()
            pose.header = copy.deepcopy(source.header)
            pose.header.frame_id = self.world_frame
            pose.pose = matrix_to_pose(
                apply_yaw_about_pivot(body_transform, self.body_yaw_offset_deg, pivot)
            )
            out.poses.append(pose)
        self.optimized_path_pub.publish(out)

    def map_cb(self, msg: PointCloud) -> None:
        """Publish ORB map points in body axes and raw optical axes."""
        with self.lock:
            if not msg.points:
                return
            points = [
                [point.x, point.y, point.z]
                for point in msg.points
                if math.isfinite(point.x) and math.isfinite(point.y) and math.isfinite(point.z)
            ]
            if not points:
                return
            raw_header = copy.deepcopy(msg.header)
            raw_header.frame_id = self.world_frame
            self.raw_map_pub.publish(point_cloud2.create_cloud_xyz32(raw_header, points))
            body_transform = yaw_rotation(self.body_yaw_offset_deg) @ OPTICAL_TO_BODY
            body_points = (body_transform[:3, :3] @ np.asarray(points, dtype=float).T).T.tolist()
            body_header = copy.deepcopy(msg.header)
            body_header.frame_id = self.world_frame
            self.map_pub.publish(point_cloud2.create_cloud_xyz32(body_header, body_points))

    def reject(self, reason: str) -> None:
        self.rejected += 1
        self.status_pub.publish(String(data=reason))
        rospy.logwarn_throttle(2.0, "[ORBWrapper] rejected native pose: %s", reason)

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
