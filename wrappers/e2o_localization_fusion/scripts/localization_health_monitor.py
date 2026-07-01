#!/usr/bin/env python3
"""Independent health assessment for FAST-LIVO2, ORB-SLAM3, and E2O sensors.

Health is based on message freshness, timestamps, finite values, kinematics,
tracking state, required sensor availability, and process presence. A running
ROS node by itself is never considered proof of healthy localization.
"""
import collections
import json
import math
import os
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional

import numpy as np
import rosnode
import rospy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image, Imu, PointCloud2
from std_msgs.msg import String

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fusion_math import pose_to_matrix, rotation_angle


def as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


@dataclass
class SensorState:
    name: str
    timeout: float
    last_wall: Optional[float] = None
    last_stamp: Optional[float] = None
    count: int = 0
    stamp_regressions: int = 0
    duplicate_stamp_count: int = 0
    last_timestamp_issue_wall: Optional[float] = None

    def update(self, stamp: float) -> None:
        now = time.monotonic()
        if self.last_stamp is not None and stamp > 0.0:
            if stamp < self.last_stamp - 1.0e-6:
                self.stamp_regressions += 1
                self.last_timestamp_issue_wall = now
            elif abs(stamp - self.last_stamp) <= 1.0e-9:
                self.duplicate_stamp_count += 1
                self.last_timestamp_issue_wall = now
            else:
                self.duplicate_stamp_count = 0
        if stamp > 0.0:
            self.last_stamp = stamp
        self.last_wall = now
        self.count += 1

    def available(self, now: float) -> bool:
        return self.last_wall is not None and (now - self.last_wall) <= self.timeout

    def healthy(self, now: float, ros_now: float, max_duplicates: int, max_stamp_lag: float) -> bool:
        if not self.available(now) or self.duplicate_stamp_count > max_duplicates:
            return False
        if self.last_timestamp_issue_wall is not None and now - self.last_timestamp_issue_wall <= self.timeout:
            return False
        if self.last_stamp is not None and ros_now > 0.0:
            lag = ros_now - self.last_stamp
            if lag > max_stamp_lag or lag < -0.5:
                return False
        return True


@dataclass
class EstimatorState:
    name: str
    timeout: float
    min_rate_hz: float
    max_rate_window: float
    max_position_jump: float
    max_orientation_jump_rad: float
    max_velocity: float
    max_angular_velocity: float
    max_acceleration: float
    max_timestamp_lag: float
    process_patterns: List[str]
    required_sensors: List[str]
    tracking_required: bool = False
    arrival_times: Deque[float] = field(default_factory=lambda: collections.deque(maxlen=500))
    last_wall: Optional[float] = None
    last_stamp: Optional[float] = None
    last_T: Optional[np.ndarray] = None
    last_velocity: Optional[np.ndarray] = None
    last_valid: bool = False
    last_message_reasons: List[str] = field(default_factory=list)
    duplicate_stamp_count: int = 0
    stamp_regressions: int = 0
    total: int = 0
    rejected: int = 0
    tracking_state: str = "UNKNOWN"
    tracking_wall: Optional[float] = None

    def update_tracking(self, value: str) -> None:
        self.tracking_state = value.strip().upper()
        self.tracking_wall = time.monotonic()

    def update_odom(self, msg: Odometry) -> None:
        now = time.monotonic()
        stamp = msg.header.stamp.to_sec()
        reasons: List[str] = []
        self.total += 1
        try:
            T = pose_to_matrix(msg.pose.pose)
        except Exception as exc:
            self.rejected += 1
            self.last_valid = False
            self.last_message_reasons = ["non_finite_or_invalid_pose", str(exc)]
            self.last_wall = now
            return

        timestamp_advances = stamp > 0.0 and (
            self.last_stamp is None or stamp > self.last_stamp + 1.0e-9
        )
        if stamp <= 0.0:
            reasons.append("zero_timestamp")
        elif self.last_stamp is not None:
            if stamp < self.last_stamp - 1.0e-6:
                self.stamp_regressions += 1
                reasons.append("timestamp_regression")
            elif abs(stamp - self.last_stamp) <= 1.0e-9:
                self.duplicate_stamp_count += 1
                reasons.append("duplicate_timestamp")
            else:
                self.duplicate_stamp_count = 0

        velocity = None
        if timestamp_advances and self.last_T is not None and self.last_stamp is not None:
            dt = stamp - self.last_stamp
            delta = np.linalg.inv(self.last_T) @ T
            jump = float(np.linalg.norm(T[:3, 3] - self.last_T[:3, 3]))
            angle = rotation_angle(delta[:3, :3])
            velocity = (T[:3, 3] - self.last_T[:3, 3]) / dt
            speed = float(np.linalg.norm(velocity))
            angular_speed = angle / dt
            if jump > self.max_position_jump:
                reasons.append("position_discontinuity")
            if angle > self.max_orientation_jump_rad:
                reasons.append("orientation_discontinuity")
            if speed > self.max_velocity:
                reasons.append("unrealistic_velocity")
            if angular_speed > self.max_angular_velocity:
                reasons.append("unrealistic_angular_velocity")
            if self.last_velocity is not None:
                acceleration = float(np.linalg.norm(velocity - self.last_velocity) / dt)
                if acceleration > self.max_acceleration:
                    reasons.append("unrealistic_acceleration")

        # A repeated/regressed stamp must not move the kinematic baseline backward.
        # Forward-stamped discontinuities do become the new baseline so an injected
        # one-frame jump can recover after subsequent valid samples and stabilization.
        if timestamp_advances:
            self.last_T = T
            self.last_stamp = stamp
            if velocity is not None:
                self.last_velocity = velocity
        self.last_wall = now
        self.arrival_times.append(now)
        self.last_valid = not reasons
        self.last_message_reasons = reasons
        if reasons:
            self.rejected += 1

    def rate(self, now: float) -> float:
        while self.arrival_times and now - self.arrival_times[0] > self.max_rate_window:
            self.arrival_times.popleft()
        if len(self.arrival_times) < 2:
            return 0.0
        span = self.arrival_times[-1] - self.arrival_times[0]
        return (len(self.arrival_times) - 1) / span if span > 1.0e-6 else 0.0


class HealthMonitor:
    def __init__(self):
        cfg = rospy.get_param("~health", {})
        self.lock = threading.RLock()
        self.start_wall = time.monotonic()
        self.startup_grace = float(cfg.get("startup_grace_sec", 12.0))
        self.publish_rate = float(cfg.get("publish_rate_hz", 5.0))
        self.node_check_period = float(cfg.get("node_check_period_sec", 1.0))
        self.tracking_timeout = float(cfg.get("tracking_status_timeout_sec", 2.5))
        self.max_duplicate_stamps = int(cfg.get("max_duplicate_stamps", 3))
        self.max_sensor_duplicate_stamps = int(cfg.get("max_sensor_duplicate_stamps", 3))
        self.sensor_timestamp_lag = float(cfg.get("sensor_timestamp_lag_sec", 1.0))
        self.process_check_enabled = as_bool(cfg.get("process_check_enabled", True))
        self.last_node_check = 0.0
        self.nodes: List[str] = []

        sensor_cfg = cfg.get("sensors", {})
        self.sensors: Dict[str, SensorState] = {}
        sensor_types = {
            "lidar": (PointCloud2, "/livox/lidar"),
            "imu": (Imu, "/livox/imu"),
            "camera": (Image, "/camera/right/image_raw"),
        }
        for name, (msg_type, default_topic) in sensor_types.items():
            item = sensor_cfg.get(name, {})
            topic = item.get("topic", default_topic)
            state = SensorState(name=name, timeout=float(item.get("timeout_sec", 1.0)))
            self.sensors[name] = state
            rospy.Subscriber(topic, msg_type, lambda msg, n=name: self.sensor_cb(n, msg), queue_size=100)

        self.estimators: Dict[str, EstimatorState] = {}
        defaults = {
            "fast_livo2": {
                "odom_topic": "/fast_livo2/odometry",
                "process_patterns": ["laserMapping", "fastlivo_mapping"],
                "required_sensors": ["lidar", "imu", "camera"],
                "tracking_required": False,
            },
            "orbslam3": {
                "odom_topic": "/orbslam3/odometry/mapping",
                "process_patterns": ["orbslam3_rgbd", "RGBD"],
                "required_sensors": ["camera"],
                "tracking_required": True,
                "tracking_topic": "/orbslam3/tracking_status",
            },
            "lvisam": {
                "odom_topic": "/lvisam/odometry",
                "process_patterns": ["lvi_sam_mapOptmization"],
                "required_sensors": ["lidar", "imu", "camera"],
                "tracking_required": False,
            },
        }
        for name, base in defaults.items():
            item = dict(base)
            item.update(cfg.get(name, {}))
            state = EstimatorState(
                name=name,
                timeout=float(item.get("pose_timeout_sec", 1.0)),
                min_rate_hz=float(item.get("min_pose_rate_hz", 2.0)),
                max_rate_window=float(item.get("rate_window_sec", 3.0)),
                max_position_jump=float(item.get("max_position_jump_m", 3.0)),
                max_orientation_jump_rad=math.radians(float(item.get("max_orientation_jump_deg", 50.0))),
                max_velocity=float(item.get("max_velocity_mps", 35.0)),
                max_angular_velocity=math.radians(float(item.get("max_angular_velocity_deg_s", 300.0))),
                max_acceleration=float(item.get("max_acceleration_mps2", 20.0)),
                max_timestamp_lag=float(item.get("max_timestamp_lag_sec", 2.0)),
                process_patterns=list(item.get("process_patterns", [])),
                required_sensors=list(item.get("required_sensors", [])),
                tracking_required=as_bool(item.get("tracking_required", False)),
            )
            self.estimators[name] = state
            rospy.Subscriber(item["odom_topic"], Odometry, lambda msg, n=name: self.odom_cb(n, msg), queue_size=200)
            if state.tracking_required:
                rospy.Subscriber(item.get("tracking_topic", "/orbslam3/tracking_status"), String,
                                 lambda msg, n=name: self.tracking_cb(n, msg), queue_size=20)

        self.status_pubs = {
            name: rospy.Publisher(f"/localization_health/{name}", String, queue_size=10, latch=True)
            for name in self.estimators
        }
        self.summary_pub = rospy.Publisher("/localization_health/summary", String, queue_size=10, latch=True)
        self.diag_pub = rospy.Publisher("/localization_health/diagnostics", DiagnosticArray, queue_size=10)
        rospy.Timer(rospy.Duration(1.0 / max(self.publish_rate, 0.2)), self.timer_cb)
        rospy.loginfo("[HealthMonitor] monitoring configured estimators, lidar, IMU, and camera")

    def sensor_cb(self, name: str, msg) -> None:
        with self.lock:
            self.sensors[name].update(msg.header.stamp.to_sec())

    def odom_cb(self, name: str, msg: Odometry) -> None:
        with self.lock:
            self.estimators[name].update_odom(msg)

    def tracking_cb(self, name: str, msg: String) -> None:
        with self.lock:
            self.estimators[name].update_tracking(msg.data)

    def refresh_nodes(self, now: float) -> None:
        if not self.process_check_enabled or now - self.last_node_check < self.node_check_period:
            return
        try:
            self.nodes = rosnode.get_node_names()
        except Exception as exc:
            rospy.logwarn_throttle(5.0, "[HealthMonitor] rosnode query failed: %s", exc)
            self.nodes = []
        self.last_node_check = now

    def process_present(self, state: EstimatorState) -> bool:
        if not self.process_check_enabled:
            return True
        return any(any(re.search(pattern, node, flags=re.IGNORECASE) for pattern in state.process_patterns)
                   for node in self.nodes)

    def build_status(self, state: EstimatorState, now: float) -> dict:
        reasons: List[str] = []
        age = math.inf if state.last_wall is None else now - state.last_wall
        rate = state.rate(now)
        in_grace = now - self.start_wall < self.startup_grace
        if state.last_wall is None:
            reasons.append("no_pose_received")
        elif age > state.timeout:
            reasons.append("stale_pose")
        ros_now = rospy.Time.now().to_sec()
        if state.last_stamp is not None and ros_now > 0.0:
            stamp_lag = ros_now - state.last_stamp
            if stamp_lag > state.max_timestamp_lag:
                reasons.append("delayed_pose_timestamp")
            elif stamp_lag < -0.5:
                reasons.append("future_pose_timestamp")
        if state.last_message_reasons:
            reasons.extend(state.last_message_reasons)
        if state.duplicate_stamp_count > self.max_duplicate_stamps:
            reasons.append("frozen_or_repeated_output")
        if state.last_wall is not None and rate < state.min_rate_hz and not in_grace:
            reasons.append("pose_rate_too_low")
        if not self.process_present(state):
            reasons.append("process_not_present")
        for sensor_name in state.required_sensors:
            sensor = self.sensors.get(sensor_name)
            if sensor is None or not sensor.healthy(
                    now, ros_now, self.max_sensor_duplicate_stamps, self.sensor_timestamp_lag):
                reasons.append(f"{sensor_name}_unavailable")
        if state.tracking_required:
            tracking_age = math.inf if state.tracking_wall is None else now - state.tracking_wall
            if tracking_age > self.tracking_timeout:
                reasons.append("tracking_status_stale")
            elif state.tracking_state not in ("TRACKING", "OK", "HEALTHY"):
                reasons.append(f"tracking_{state.tracking_state.lower()}")

        # During startup, missing-rate and no-pose conditions remain visible but do
        # not assert healthy. This avoids false failover before algorithms initialize.
        reasons = sorted(set(reasons))
        healthy = not reasons
        score = max(0.0, 1.0 - 0.15 * len(reasons))
        return {
            "stamp": rospy.Time.now().to_sec(),
            "name": state.name,
            "healthy": healthy,
            "score": score,
            "startup_grace": in_grace,
            "reasons": reasons,
            "pose_age_sec": None if not math.isfinite(age) else age,
            "pose_rate_hz": rate,
            "last_pose_stamp": state.last_stamp,
            "pose_timestamp_lag_sec": None if state.last_stamp is None or ros_now <= 0.0 else ros_now - state.last_stamp,
            "tracking_state": state.tracking_state,
            "process_present": self.process_present(state),
            "total_messages": state.total,
            "rejected_messages": state.rejected,
            "stamp_regressions": state.stamp_regressions,
            "required_sensors": state.required_sensors,
            "sensor_available": {
                name: self.sensors[name].healthy(now, ros_now, self.max_sensor_duplicate_stamps, self.sensor_timestamp_lag)
                for name in state.required_sensors
            },
        }

    @staticmethod
    def diagnostic_from_status(status: dict) -> DiagnosticStatus:
        out = DiagnosticStatus()
        out.name = f"e2o_localization/{status['name']}"
        out.hardware_id = status["name"]
        out.level = DiagnosticStatus.OK if status["healthy"] else DiagnosticStatus.ERROR
        out.message = "healthy" if status["healthy"] else ",".join(status["reasons"])
        for key in ("score", "pose_age_sec", "pose_rate_hz", "tracking_state", "process_present"):
            out.values.append(KeyValue(key=key, value=str(status.get(key))))
        return out

    def timer_cb(self, _event) -> None:
        with self.lock:
            now = time.monotonic()
            self.refresh_nodes(now)
            statuses = {name: self.build_status(state, now) for name, state in self.estimators.items()}
            for name, status in statuses.items():
                self.status_pubs[name].publish(String(data=json.dumps(status, sort_keys=True)))
            ros_now = rospy.Time.now().to_sec()
            sensor_summary = {
                name: {
                    "available": state.healthy(now, ros_now, self.max_sensor_duplicate_stamps, self.sensor_timestamp_lag),
                    "receipt_age_sec": None if state.last_wall is None else now - state.last_wall,
                    "timestamp_lag_sec": None if state.last_stamp is None or ros_now <= 0.0 else ros_now - state.last_stamp,
                    "count": state.count,
                    "duplicate_stamp_count": state.duplicate_stamp_count,
                    "stamp_regressions": state.stamp_regressions,
                }
                for name, state in self.sensors.items()
            }
            summary = {"stamp": rospy.Time.now().to_sec(), "estimators": statuses, "sensors": sensor_summary}
            self.summary_pub.publish(String(data=json.dumps(summary, sort_keys=True)))
            diagnostics = DiagnosticArray()
            diagnostics.header.stamp = rospy.Time.now()
            diagnostics.status = [self.diagnostic_from_status(status) for status in statuses.values()]
            self.diag_pub.publish(diagnostics)


def main() -> None:
    rospy.init_node("localization_health_monitor")
    HealthMonitor()
    rospy.spin()


if __name__ == "__main__":
    main()
