#!/usr/bin/env python3
"""Republish ORB-SLAM3 RGB-D outputs in ROS/body axes without scaling.

The upstream RGB-D node publishes the current camera pose and optimized
keyframe path in camera optical axes. This wrapper keeps raw native topics for
recording, and publishes the main ORB topics with only a fixed optical-to-body
axis remap so forward motion appears in the same X/Y ground-plane convention as
the LiDAR-based estimators. It does not use ground truth, normalize starts, or
fit scale. ORB-SLAM3 loop closure can rewrite the map frame; those map-frame
corrections are re-anchored internally so live odometry remains continuous.
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

GENERIC_OPTICAL_TO_BODY = np.array([
    [0.0, 0.0, 1.0, 0.0],
    [-1.0, 0.0, 0.0, 0.0],
    [0.0, -1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0],
], dtype=float)

# E2O calibrated camera optical -> base_link rotation. This removes the small
# XY heading bias left by the generic ROS optical-axis remap.
E2O_OPTICAL_TO_BODY_ROTATION = np.array([
    [-0.18256836, 0.11110754, 0.97689503],
    [-0.98306216, -0.00440978, -0.18321936],
    [-0.01604916, -0.99379861, 0.11003070],
], dtype=float)

OPTICAL_TO_BODY = np.eye(4, dtype=float)
OPTICAL_TO_BODY[:3, :3] = E2O_OPTICAL_TO_BODY_ROTATION


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


def optical_pose_to_body_axes(
    pose: Pose,
    yaw_offset_deg: float = 0.0,
    optical_to_body_rotation: np.ndarray = E2O_OPTICAL_TO_BODY_ROTATION,
) -> Pose:
    camera_transform = pose_to_matrix(pose)
    return matrix_to_pose(remap_optical_world_to_car_pose(
        camera_transform, optical_to_body_rotation, yaw_offset_deg,
    ))


def remap_optical_world_to_car_pose(
    camera_transform: np.ndarray,
    optical_to_body_rotation: np.ndarray,
    yaw_offset_deg: float = 0.0,
) -> np.ndarray:
    """Convert ORB optical/world axes to ROS car axes without tilting base_link.

    ORB's RGB-D pose is a camera-optical pose. For plotting/evaluation we remap
    positions from optical axes to car-style axes. The vehicle attitude must not
    be the fixed optical->body rotation itself, otherwise base_link starts with
    optical Z as vehicle front and RViz shows the car pitched up. Conjugating the
    rotation preserves ORB's relative attitude while making an identity ORB pose
    publish as an identity car-body pose.
    """
    axis_rotation = yaw_rotation(yaw_offset_deg)[:3, :3] @ np.asarray(optical_to_body_rotation, dtype=float).reshape(3, 3)
    out = np.eye(4)
    out[:3, 3] = axis_rotation @ camera_transform[:3, 3]
    out[:3, :3] = axis_rotation @ camera_transform[:3, :3] @ np.asarray(optical_to_body_rotation, dtype=float).reshape(3, 3).T
    return out


def valid_rotation(matrix: np.ndarray) -> bool:
    R = np.asarray(matrix, dtype=float).reshape(3, 3)
    return (np.all(np.isfinite(R)) and
            np.allclose(R.T @ R, np.eye(3), atol=1.0e-3) and
            abs(float(np.linalg.det(R)) - 1.0) < 1.0e-3)


def invert_transform(transform: np.ndarray) -> np.ndarray:
    out = np.eye(4)
    out[:3, :3] = transform[:3, :3].T
    out[:3, 3] = -(out[:3, :3] @ transform[:3, 3])
    return out


def rotation_angle(transform_a: np.ndarray, transform_b: np.ndarray) -> float:
    delta = transform_a[:3, :3].T @ transform_b[:3, :3]
    value = (float(np.trace(delta)) - 1.0) * 0.5
    return math.acos(max(-1.0, min(1.0, value)))


def continuity_correction(last_published: np.ndarray, native_after_jump: np.ndarray) -> np.ndarray:
    return last_published @ invert_transform(native_after_jump)


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
        self.body_yaw_offset_deg = float(rospy.get_param("~body_yaw_offset_deg", 0.0))
        optical_to_body = rospy.get_param(
            "~optical_to_body_rotation",
            E2O_OPTICAL_TO_BODY_ROTATION.reshape(-1).tolist(),
        )
        self.optical_to_body_rotation = np.asarray(optical_to_body, dtype=float).reshape(3, 3)
        if not valid_rotation(self.optical_to_body_rotation):
            raise rospy.ROSInitException("~optical_to_body_rotation must be a proper finite 3x3 rotation")
        self.tracking_timeout = float(rospy.get_param("~tracking_timeout_sec", 2.0))
        self.max_path_poses = int(rospy.get_param("~max_path_poses", 50000))
        self.path_publish_period = float(rospy.get_param("~path_publish_period_sec", 0.5))
        self.max_step_m = float(rospy.get_param("~max_step_m", 1.25))
        self.max_gap_step_m = float(rospy.get_param("~max_gap_step_m", 3.0))
        self.max_speed_mps = float(rospy.get_param("~max_speed_mps", 12.0))
        self.max_yaw_step_deg = float(rospy.get_param("~max_yaw_step_deg", 45.0))
        self.max_backtrack_m = float(rospy.get_param("~max_backtrack_m", 0.75))
        self.reanchor_on_loop_closure = str(
            rospy.get_param("~reanchor_on_loop_closure", True)
        ).strip().lower() in ("1", "true", "yes", "on")
        self.max_reanchor_step_m = float(rospy.get_param("~max_reanchor_step_m", 80.0))
        self.max_reanchor_rotation_deg = float(rospy.get_param("~max_reanchor_rotation_deg", 90.0))
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
        self.last_path_publish_wall = 0.0
        self.last_receipt_wall = None
        self.last_stamp = None
        self.last_body_transform = None
        self.world_correction = np.eye(4)
        self.recent_velocities = deque(maxlen=max(2, self.velocity_window))
        self.received = 0
        self.rejected = 0
        self.reanchors = 0

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

            body_transform = remap_optical_world_to_car_pose(
                pose_to_matrix(msg.pose), self.optical_to_body_rotation, self.body_yaw_offset_deg
            )
            corrected_body_transform = self.world_correction @ body_transform
            unstable_reason = self.unstable_body_pose(corrected_body_transform, stamp)
            if unstable_reason:
                if self.reanchor_for_loop_closure(body_transform, stamp, unstable_reason):
                    corrected_body_transform = self.world_correction @ body_transform
                    self.recent_velocities.clear()
                    self.status_pub.publish(String(data="TRACKING"))
                else:
                    self.reject(unstable_reason)
                    return
            if self.unstable_body_pose(corrected_body_transform, stamp, update_history=True):
                self.reject("UNSTABLE_POSE")
                return

            body_odom = copy.deepcopy(raw_odom)
            body_odom.child_frame_id = self.body_frame
            body_odom.pose.pose = matrix_to_pose(corrected_body_transform)

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
            self.last_body_transform = corrected_body_transform.copy()
            self.last_receipt_wall = now
            self.status_pub.publish(String(data="TRACKING"))

    def unstable_body_pose(self, transform: np.ndarray, stamp, update_history: bool = False) -> str:
        if self.last_body_transform is None or self.last_stamp is None:
            return ""
        dt = (stamp - self.last_stamp).to_sec()
        if dt <= 1.0e-4:
            return "OUT_OF_ORDER"
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
            return "UNSTABLE_POSE"
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
                    return "UNSTABLE_BACKTRACK"
        if update_history:
            self.recent_velocities.append(delta / dt)
        return ""

    def reanchor_for_loop_closure(self, native_body_transform: np.ndarray, stamp, reason: str) -> bool:
        if not self.reanchor_on_loop_closure or reason not in ("UNSTABLE_POSE", "UNSTABLE_BACKTRACK"):
            return False
        if self.last_body_transform is None or self.last_stamp is None:
            return False
        dt = (stamp - self.last_stamp).to_sec()
        if dt <= 1.0e-4:
            return False
        corrected_before = self.world_correction @ native_body_transform
        step = float(np.linalg.norm(corrected_before[:3, 3] - self.last_body_transform[:3, 3]))
        angle_deg = math.degrees(rotation_angle(self.last_body_transform, corrected_before))
        if step > self.max_reanchor_step_m or angle_deg > self.max_reanchor_rotation_deg:
            return False
        self.world_correction = continuity_correction(self.last_body_transform, native_body_transform)
        self.reanchors += 1
        rospy.logwarn(
            "[ORBWrapper] re-anchored ORB map correction #%d step=%.3fm rot=%.1fdeg",
            self.reanchors, step, angle_deg,
        )
        return True

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
            body_transforms.append(self.world_correction @ remap_optical_world_to_car_pose(
                pose_to_matrix(source.pose), self.optical_to_body_rotation, self.body_yaw_offset_deg
            ))
            source_poses.append(source)
        if not body_transforms:
            self.optimized_path_pub.publish(out)
            return
        for source, body_transform in zip(source_poses, body_transforms):
            pose = PoseStamped()
            pose.header = copy.deepcopy(source.header)
            pose.header.frame_id = self.world_frame
            pose.pose = matrix_to_pose(body_transform)
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
            body_rotation = yaw_rotation(self.body_yaw_offset_deg)[:3, :3] @ self.optical_to_body_rotation
            body_points_np = (body_rotation @ np.asarray(points, dtype=float).T).T
            body_points_np = (self.world_correction[:3, :3] @ body_points_np.T).T + self.world_correction[:3, 3]
            body_points = body_points_np.tolist()
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
