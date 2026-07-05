#!/usr/bin/env python3
"""Continuity-preserving loose coupling for a metric estimator and ORB-SLAM3.

The node deliberately does not alter either estimator. It supervises their
independent odometry streams, estimates the relative SE(3) transform from
synchronized samples, checks agreement/scale, selects a healthy source with
hysteresis, and aligns every source switch to the last published fused pose.
"""
import collections
import csv
import json
import math
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional, Tuple

import numpy as np
import rospy
import tf2_ros
from geometry_msgs.msg import PoseStamped, TransformStamped, Twist
from nav_msgs.msg import Odometry, Path
from std_msgs.msg import Bool, String

# Catkin runs this file through a relay in the devel-space bin directory.
# Prefer the source directory over the relay when importing sibling modules.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fusion_math import (
    apply_camera_to_base_similarity,
    estimate_camera_to_base_similarity,
    interpolate_transform,
    invert_transform,
    matrix_to_pose,
    pose_to_matrix,
    rotation_angle,
)

FAST = "fast_livo2"
LVISAM = "lvisam"
ORB = "orbslam3"
FAILED = "none"

CSV_ALIAS = {FAST: "fastlivo2", LVISAM: "lvisam", ORB: "orbslam3"}

# Health "reasons" that indicate a specific failed sensor category, as opposed to
# generic pose-quality degradation (jitter, discontinuity, stale output, ...).
# Only these reasons drive the sensor-aware fallback selection below; any other
# reason falls through to the mode's default fallback order.
LIDAR_OR_IMU_DOWN = {"lidar_unavailable", "imu_unavailable"}
CAMERA_DOWN = {"camera_unavailable"}
METRIC_RESTART_REASONS = {
    "position_discontinuity",
    "orientation_discontinuity",
    "unrealistic_velocity",
    "unrealistic_acceleration",
    "unrealistic_angular_velocity",
}
# These indicate missing/invalid data rather than a recovered estimator whose
# native map frame needs rebasing. Do not force-use a source in these states.
RECOVERY_BLOCKING_REASONS = {
    "no_pose_received",
    "stale_pose",
    "delayed_pose_timestamp",
    "future_pose_timestamp",
    "timestamp_regression",
    "frozen_or_repeated_output",
    "non_finite_or_invalid_pose",
    "process_not_present",
}


def as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


@dataclass
class SourceData:
    name: str
    latest_msg: Optional[Odometry] = None
    latest_T: Optional[np.ndarray] = None
    latest_stamp: Optional[float] = None
    buffer: Deque[Tuple[float, np.ndarray]] = field(default_factory=lambda: collections.deque(maxlen=300))
    health: dict = field(default_factory=lambda: {"healthy": False, "score": 0.0, "reasons": ["no_health_status"]})
    healthy_since: Optional[float] = None
    unhealthy_since: Optional[float] = None

    def update_health(self, status: dict, now: float) -> None:
        previous = bool(self.health.get("healthy", False))
        current = bool(status.get("healthy", False))
        self.health = status
        if current:
            if not previous or self.healthy_since is None:
                self.healthy_since = now
            self.unhealthy_since = None
        else:
            if previous or self.unhealthy_since is None:
                self.unhealthy_since = now
            self.healthy_since = None

    def stable_healthy(self, now: float, duration: float) -> bool:
        return bool(self.health.get("healthy", False)) and self.healthy_since is not None and now - self.healthy_since >= duration


class LocalizationFusion:
    def __init__(self) -> None:
        cfg = rospy.get_param("~fusion", {})
        self.lock = threading.RLock()
        self.primary = str(cfg.get("primary_source", FAST)).strip().lower()
        if self.primary not in (FAST, LVISAM, ORB):
            raise rospy.ROSInitException("primary_source must be fast_livo2, lvisam, or orbslam3")
        default_metric = FAST if self.primary == ORB else self.primary
        self.metric_source = str(cfg.get("metric_source", default_metric)).strip().lower()
        if self.metric_source not in (FAST, LVISAM):
            raise rospy.ROSInitException("metric_source must be fast_livo2 or lvisam")
        if self.primary != ORB and self.primary != self.metric_source:
            raise rospy.ROSInitException("non-ORB primary_source must match metric_source")
        self.secondary = ORB if self.primary == self.metric_source else self.metric_source
        _tertiary_cfg = str(cfg.get("tertiary_source", "")).strip().lower()
        self.tertiary_source = _tertiary_cfg
        self.enable_tertiary = (
            bool(_tertiary_cfg) and
            _tertiary_cfg in (FAST, LVISAM) and
            _tertiary_cfg != self.metric_source and
            _tertiary_cfg != ORB
        )
        # Fusion 1 is FAST-LIVO2 primary; Fusion 2 is LVI-SAM primary.
        # A tertiary source can be monitored/launched independently, but it
        # must not redefine the fusion topology.
        self.mode = "fusion1" if self.metric_source == FAST else "fusion2"
        self.map_frame = str(cfg.get("map_frame", "map"))
        self.odom_frame = str(cfg.get("odom_frame", "odom"))
        self.base_frame = str(cfg.get("base_frame", "base_link"))
        self.tf_mode = str(cfg.get("tf_mode", "direct")).strip().lower()
        if self.tf_mode not in ("direct", "map_to_odom", "none"):
            raise rospy.ROSInitException("tf_mode must be direct, map_to_odom, or none")
        self.publish_tf = as_bool(cfg.get("publish_tf", True)) and self.tf_mode != "none"
        self.tf_stamp_mode = str(cfg.get("tf_stamp_mode", "current")).strip().lower()
        if self.tf_stamp_mode not in ("current", "source"):
            raise rospy.ROSInitException("tf_stamp_mode must be current or source")
        self.publish_rate_hz = float(cfg.get("publish_rate_hz", 30.0))
        self.localization_start_delay = float(cfg.get("localization_start_delay_sec", 8.0))
        self.sync_slop = float(cfg.get("sync_slop_sec", 0.05))
        self.alignment_window = int(cfg.get("alignment_window", 40))
        self.min_alignment_pairs = int(cfg.get("min_alignment_pairs", 8))
        self.failure_hold = float(cfg.get("failure_hold_sec", 0.35))
        self.recovery_stabilization = float(cfg.get("recovery_stabilization_sec", 3.0))
        self.primary_recovery = float(cfg.get("primary_recovery_sec", 5.0))
        self.minimum_dwell = float(cfg.get("minimum_source_dwell_sec", 3.0))
        self.blend_duration = float(cfg.get("blend_duration_sec", 1.0))
        self.weighted_fusion_enabled = as_bool(cfg.get("weighted_fusion_enabled", False))
        self.weight_rise_time = float(cfg.get("weight_rise_time_sec", 6.0))
        self.weight_fall_time = float(cfg.get("weight_fall_time_sec", 1.0))
        self.lidar_recovery_override = float(cfg.get("lidar_recovery_override_sec", 8.0))
        self.metric_nominal_weight = float(cfg.get("metric_nominal_weight", 0.9))
        self.lvisam_recovery_weight = float(cfg.get("lvisam_recovery_weight", 0.9))
        self.orb_nominal_weight = float(cfg.get("orb_nominal_weight", 0.1))
        self.orb_backup_weight = float(cfg.get("orb_backup_weight", 1.0))
        self.max_disagreement_m = float(cfg.get("max_disagreement_m", 4.0))
        self.max_disagreement_rad = math.radians(float(cfg.get("max_disagreement_deg", 35.0)))
        self.recovery_disagreement_m = float(cfg.get("recovery_disagreement_m", 2.0))
        self.recovery_disagreement_rad = math.radians(float(cfg.get("recovery_disagreement_deg", 20.0)))
        self.require_recovery_consistency = as_bool(cfg.get("require_recovery_consistency", False))
        self.scale_ratio_min = float(cfg.get("orb_scale_ratio_min", 1.0))
        self.scale_ratio_max = float(cfg.get("orb_scale_ratio_max", 1.0))
        self.max_alignment_rmse = float(cfg.get("max_alignment_rmse_m", 1.5))
        self.max_alignment_orientation_rmse = math.radians(float(cfg.get("max_alignment_orientation_rmse_deg", 20.0)))
        self.orb_fixed_scale = float(cfg.get("orb_fixed_scale", 1.0))
        self.allow_orb_without_validated_scale = as_bool(cfg.get("allow_orb_without_validated_scale", False))
        self.max_output_gap = float(cfg.get("max_output_gap_sec", 1.0))
        self.max_path_poses = int(cfg.get("max_path_poses", 100000))
        self.event_log_path = str(cfg.get("event_log_path", "/data/output/fusion_events.csv"))
        self.output_dir = str(cfg.get("output_dir") or os.path.dirname(self.event_log_path) or "/data/output/current_run")
        self.fused_csv_path = os.path.join(self.output_dir, "fused.csv")
        self.stop_navigation_on_failure = as_bool(cfg.get("stop_navigation_on_failure", True))
        extrinsic = cfg.get("orb_camera_to_base", {})
        self.orb_camera_to_base = np.eye(4, dtype=float)
        self.orb_camera_to_base[:3, :3] = np.asarray(extrinsic.get("rotation", np.eye(3)), dtype=float).reshape(3, 3)
        self.orb_camera_to_base[:3, 3] = np.asarray(extrinsic.get("translation", [0.0, 0.0, 0.0]), dtype=float).reshape(3)
        if not np.all(np.isfinite(self.orb_camera_to_base)):
            raise rospy.ROSInitException("orb_camera_to_base contains non-finite values")

        topics = cfg.get("topics", {})
        default_metric_topic = "/fast_livo2/odometry" if self.metric_source == FAST else "/lvisam/odometry"
        self.metric_topic = str(topics.get(f"{self.metric_source}_odom", default_metric_topic))
        self.orb_topic = str(topics.get("orbslam3_odom", "/orbslam3/camera_odometry"))
        self.output_odom_topic = str(topics.get("output_odom", "/fused_localization/odometry"))
        self.output_pose_topic = str(topics.get("output_pose", "/fused_localization/pose"))
        self.output_path_topic = str(topics.get("output_path", "/fused_localization/path"))
        self.continuous_odom_topic = str(topics.get("continuous_odom", self.output_odom_topic))
        self.continuous_pose_topic = str(topics.get("continuous_pose", self.output_pose_topic))
        self.continuous_path_topic = str(topics.get("continuous_path", self.output_path_topic))
        self.metric_odom_topic = str(topics.get("metric_odom", "/fused_localization/metric_odometry"))
        self.metric_pose_topic = str(topics.get("metric_pose", "/fused_localization/metric_pose"))
        self.metric_path_topic = str(topics.get("metric_path", "/fused_localization/metric_path"))
        self.status_topic = str(topics.get("status", "/fused_localization/status"))
        self.active_topic = str(topics.get("active_source", "/fused_localization/active_source"))
        self.event_topic = str(topics.get("events", "/fused_localization/events"))
        self.nav_ok_topic = str(topics.get("navigation_ok", "/fused_localization/navigation_ok"))

        self.sources: Dict[str, SourceData] = {
            self.metric_source: SourceData(self.metric_source),
            ORB: SourceData(ORB),
        }
        # source_to_output is a rigid transform applied after source-specific scale.
        self.source_to_output: Dict[str, np.ndarray] = {
            self.metric_source: np.eye(4),
            ORB: np.eye(4),
        }
        self.source_scale: Dict[str, float] = {
            self.metric_source: 1.0,
            ORB: self.orb_fixed_scale if self.orb_fixed_scale > 0.0 else 1.0,
        }
        if self.enable_tertiary:
            self.sources[self.tertiary_source] = SourceData(self.tertiary_source)
            self.source_to_output[self.tertiary_source] = np.eye(4)
            self.source_scale[self.tertiary_source] = 1.0
        configured_monitor_sources = cfg.get("monitor_sources", [])
        self.monitor_sources = []
        for item in configured_monitor_sources:
            name = str(item).strip().lower()
            if name in (FAST, LVISAM) and name not in self.sources:
                self.sources[name] = SourceData(name)
                self.monitor_sources.append(name)
        default_orb_alignment_source = self.tertiary_source if self.enable_tertiary else self.metric_source
        self.orb_alignment_source = str(
            cfg.get("orb_alignment_source", default_orb_alignment_source)
        ).strip().lower()
        if self.orb_alignment_source not in self.sources or self.orb_alignment_source == ORB:
            raise rospy.ROSInitException("orb_alignment_source must be a configured metric estimator")
        self.raw_csv_writers: Dict[str, csv.writer] = {}
        self.raw_csv_handles: Dict[str, object] = {}
        self.fused_csv_writer = None
        self.fused_csv_handle = None
        self.last_blend_alpha = 1.0
        self.weighted_sources = [self.metric_source]
        if self.enable_tertiary:
            self.weighted_sources.append(self.tertiary_source)
        self.weighted_sources.append(ORB)
        self.fusion_weights: Dict[str, float] = {
            source: 0.0 for source in self.weighted_sources
        }
        self.target_fusion_weights: Dict[str, float] = dict(self.fusion_weights)
        self.last_weight_update_wall: Optional[float] = None
        self.weighted_last_stamp: Optional[float] = None
        self.weighted_active_label = FAILED
        self.weighted_state = "WAITING_FOR_LOCALIZATION"
        self.force_reanchor: Dict[str, bool] = {source: False for source in self.weighted_sources}
        self.recovery_override_until: Dict[str, float] = {source: 0.0 for source in self.weighted_sources}
        # True only while a source has a currently/recently unavailable required
        # sensor. Gates metric_restart_recovery_status so a bare pose glitch
        # (discontinuity/unrealistic kinematics) with no real sensor outage is
        # never mistaken for "sensor came back, re-anchor me".
        self.sensor_outage_active: Dict[str, bool] = {source: False for source in self.weighted_sources}
        self.synchronized_pairs: Deque[Tuple[np.ndarray, np.ndarray]] = collections.deque(maxlen=self.alignment_window)
        self.recovery_pairs: Deque[Tuple[np.ndarray, np.ndarray]] = collections.deque(maxlen=self.alignment_window)
        self.cross_fast_from_orb: Optional[np.ndarray] = None
        self.orb_metric_scale: Optional[float] = self.orb_fixed_scale if self.orb_fixed_scale > 0.0 else None
        self.recovery_cross_fast_from_orb: Optional[np.ndarray] = None
        self.recovery_orb_metric_scale: Optional[float] = None
        self.disagreement = {"position_m": None, "orientation_rad": None, "scale_ratio": None, "valid": False}
        self.recovery_disagreement = {"position_m": None, "orientation_rad": None, "scale_ratio": None, "valid": False}
        self.alignment_quality = {"position_rmse_m": None, "orientation_rmse_rad": None}
        self.recovery_alignment_quality = {"position_rmse_m": None, "orientation_rmse_rad": None}
        self.last_pair_key: Optional[Tuple[float, float]] = None
        self.last_metric_fault_reset_reason: Optional[str] = None

        self.active_source = FAILED
        self.state = "WAITING_FOR_LOCALIZATION"
        self.bag_start_wall: Optional[float] = None
        self.last_switch_wall = 0.0
        self.switch_count = 0
        self.switch_start_wall: Optional[float] = None
        self.switch_anchor_T: Optional[np.ndarray] = None
        self.pending_switch_event: Optional[dict] = None
        self.last_output_T: Optional[np.ndarray] = None
        self.last_output_stamp: Optional[float] = None
        self.last_output_wall: Optional[float] = None
        _stamps: Dict[str, Optional[float]] = {self.metric_source: None, ORB: None}
        if self.enable_tertiary:
            _stamps[self.tertiary_source] = None
        _stamps["weighted"] = None
        self.last_output_source_stamp: Dict[str, Optional[float]] = _stamps
        self.last_twist = Twist()
        self.path = Path()
        self.path.header.frame_id = self.map_frame
        self.metric_path = Path()
        self.metric_path.header.frame_id = self.map_frame
        self.aligned_source_paths: Dict[str, Path] = {}
        self.last_aligned_source_stamp: Dict[str, Optional[float]] = {}
        for source in self.weighted_source_order():
            path = Path()
            path.header.frame_id = self.map_frame
            self.aligned_source_paths[source] = path
            self.last_aligned_source_stamp[source] = None
        self.last_metric_output_T: Optional[np.ndarray] = None
        self.last_metric_output_stamp: Optional[float] = None

        self.odom_pub = rospy.Publisher(self.output_odom_topic, Odometry, queue_size=100)
        self.pose_pub = rospy.Publisher(self.output_pose_topic, PoseStamped, queue_size=100)
        self.path_pub = rospy.Publisher(self.output_path_topic, Path, queue_size=5, latch=True)
        self.continuous_odom_pub = None if self.continuous_odom_topic == self.output_odom_topic else rospy.Publisher(self.continuous_odom_topic, Odometry, queue_size=100)
        self.continuous_pose_pub = None if self.continuous_pose_topic == self.output_pose_topic else rospy.Publisher(self.continuous_pose_topic, PoseStamped, queue_size=100)
        self.continuous_path_pub = None if self.continuous_path_topic == self.output_path_topic else rospy.Publisher(self.continuous_path_topic, Path, queue_size=5, latch=True)
        self.metric_odom_pub = rospy.Publisher(self.metric_odom_topic, Odometry, queue_size=100)
        self.metric_pose_pub = rospy.Publisher(self.metric_pose_topic, PoseStamped, queue_size=100)
        self.metric_path_pub = rospy.Publisher(self.metric_path_topic, Path, queue_size=5, latch=True)
        self.aligned_source_path_pubs = {
            FAST: rospy.Publisher("/fused_localization/aligned_fast_livo2_path", Path, queue_size=5, latch=True),
            LVISAM: rospy.Publisher("/fused_localization/aligned_lvisam_path", Path, queue_size=5, latch=True),
            ORB: rospy.Publisher("/fused_localization/aligned_orbslam3_path", Path, queue_size=5, latch=True),
        }
        self.status_pub = rospy.Publisher(self.status_topic, String, queue_size=10, latch=True)
        self.active_pub = rospy.Publisher(self.active_topic, String, queue_size=10, latch=True)
        self.event_pub = rospy.Publisher(self.event_topic, String, queue_size=50, latch=True)
        self.nav_ok_pub = rospy.Publisher(self.nav_ok_topic, Bool, queue_size=10, latch=True)

        self.tf_broadcaster = tf2_ros.TransformBroadcaster() if self.publish_tf else None
        self.static_broadcaster = tf2_ros.StaticTransformBroadcaster() if self.publish_tf and self.tf_mode == "direct" else None
        self.tf_buffer = tf2_ros.Buffer(cache_time=rospy.Duration(20.0))
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer) if self.publish_tf and self.tf_mode == "map_to_odom" else None
        if self.static_broadcaster is not None:
            static = TransformStamped()
            static.header.stamp = rospy.Time.now()
            static.header.frame_id = self.map_frame
            static.child_frame_id = self.odom_frame
            static.transform.rotation.w = 1.0
            self.static_broadcaster.sendTransform(static)

        rospy.Subscriber(self.metric_topic, Odometry, lambda msg: self.odom_cb(self.metric_source, msg), queue_size=200)
        rospy.Subscriber(self.orb_topic, Odometry, lambda msg: self.odom_cb(ORB, msg), queue_size=200)
        rospy.Subscriber(f"/localization_health/{self.metric_source}", String,
                         lambda msg: self.health_cb(self.metric_source, msg), queue_size=20)
        rospy.Subscriber("/localization_health/orbslam3", String, lambda msg: self.health_cb(ORB, msg), queue_size=20)
        if self.enable_tertiary:
            _default_tertiary_topic = "/lvisam/odometry" if self.tertiary_source == LVISAM else "/fast_livo2/odometry"
            self.tertiary_topic = str(topics.get(f"{self.tertiary_source}_odom", _default_tertiary_topic))
            _ts = self.tertiary_source
            rospy.Subscriber(self.tertiary_topic, Odometry, lambda msg, s=_ts: self.odom_cb(s, msg), queue_size=200)
            rospy.Subscriber(f"/localization_health/{self.tertiary_source}", String,
                             lambda msg, s=_ts: self.health_cb(s, msg), queue_size=20)
        else:
            self.tertiary_topic = ""
        for source in self.monitor_sources:
            _default_topic = "/lvisam/odometry" if source == LVISAM else "/fast_livo2/odometry"
            topic = str(topics.get(f"{source}_odom", _default_topic))
            rospy.Subscriber(topic, Odometry, lambda msg, s=source: self.odom_cb(s, msg), queue_size=200)
            rospy.Subscriber(f"/localization_health/{source}", String,
                             lambda msg, s=source: self.health_cb(s, msg), queue_size=20)
        rospy.Timer(rospy.Duration(1.0 / max(self.publish_rate_hz, 1.0)), self.timer_cb)
        self.prepare_event_log()
        self.prepare_trajectory_csvs()
        rospy.on_shutdown(self.close_trajectory_csvs)
        self.publish_event("startup", FAILED, FAILED, "fusion_node_started", 0.0)
        rospy.loginfo("[Fusion] primary=%s metric=%s metric_topic=%s orb=%s tf_mode=%s tf_stamp=%s orb_ref=%s tertiary=%s",
                      self.primary, self.metric_source, self.metric_topic, self.orb_topic, self.tf_mode,
                      self.tf_stamp_mode, self.orb_alignment_source,
                      self.tertiary_source if self.enable_tertiary else "disabled")

    def prepare_event_log(self) -> None:
        if not self.event_log_path:
            return
        try:
            os.makedirs(os.path.dirname(self.event_log_path), exist_ok=True)
            if not os.path.exists(self.event_log_path):
                with open(self.event_log_path, "w", newline="", encoding="utf-8") as handle:
                    csv.writer(handle).writerow(["ros_time", "wall_time", "event", "from_source", "to_source", "reason", "pose_jump_m", "orientation_jump_deg"])
        except OSError as exc:
            rospy.logwarn("[Fusion] cannot prepare event log %s: %s", self.event_log_path, exc)
            self.event_log_path = ""

    def prepare_trajectory_csvs(self) -> None:
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            for name in self.sources:
                alias = CSV_ALIAS.get(name, name)
                path = os.path.join(self.output_dir, f"{alias}.csv")
                handle = open(path, "w", newline="", encoding="utf-8")
                writer = csv.writer(handle)
                writer.writerow(["timestamp_s", "x_m", "y_m", "z_m", "qx", "qy", "qz", "qw"])
                self.raw_csv_handles[name] = handle
                self.raw_csv_writers[name] = writer
            self.fused_csv_handle = open(self.fused_csv_path, "w", newline="", encoding="utf-8")
            self.fused_csv_writer = csv.writer(self.fused_csv_handle)
            self.fused_csv_writer.writerow([
                "timestamp_s", "x_m", "y_m", "z_m", "qx", "qy", "qz", "qw",
                "active_source", "state", "blend_alpha", "switch_count",
                "lidar_ok", "imu_ok", "camera_ok",
                "fast_livo2_healthy", "lvisam_healthy", "orbslam3_healthy",
            ])
        except OSError as exc:
            rospy.logwarn("[Fusion] cannot prepare trajectory CSVs in %s: %s", self.output_dir, exc)

    def write_raw_csv_row(self, source: str, msg: Odometry) -> None:
        writer = self.raw_csv_writers.get(source)
        if writer is None:
            return
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        writer.writerow([msg.header.stamp.to_sec(), p.x, p.y, p.z, q.x, q.y, q.z, q.w])
        self.raw_csv_handles[source].flush()

    def sensor_status(self, sensor: str) -> Optional[bool]:
        """Best-effort sensor-category health, read off whichever running
        estimator's health report already tracks that sensor (they all share
        the same underlying sensor monitor, so any reporter agrees)."""
        for data in self.sources.values():
            available = data.health.get("sensor_available") or {}
            if sensor in available:
                return bool(available[sensor])
        return None

    def health_snapshot_row(self) -> list:
        healthy = {name: bool(self.sources[name].health.get("healthy", False)) for name in self.sources}
        return [
            self.sensor_status("lidar"),
            self.sensor_status("imu"),
            self.sensor_status("camera"),
            healthy.get(FAST),
            healthy.get(LVISAM),
            healthy.get(ORB),
        ]

    def close_trajectory_csvs(self) -> None:
        for handle in self.raw_csv_handles.values():
            try:
                handle.close()
            except Exception:
                pass
        if self.fused_csv_handle is not None:
            try:
                self.fused_csv_handle.close()
            except Exception:
                pass

    def append_event_log(self, row) -> None:
        if not self.event_log_path:
            return
        try:
            with open(self.event_log_path, "a", newline="", encoding="utf-8") as handle:
                csv.writer(handle).writerow(row)
        except OSError as exc:
            rospy.logwarn_throttle(5.0, "[Fusion] event log write failed: %s", exc)

    def publish_event(self, event: str, old: str, new: str, reason: str, jump: float,
                      orientation_jump_deg: float = 0.0) -> None:
        payload = {
            "ros_time": rospy.Time.now().to_sec(),
            "wall_time": time.time(),
            "event": event,
            "from_source": old,
            "to_source": new,
            "reason": reason,
            "pose_jump_m": jump,
            "orientation_jump_deg": orientation_jump_deg,
        }
        text = json.dumps(payload, sort_keys=True)
        self.event_pub.publish(String(data=text))
        self.append_event_log([payload[k] for k in ("ros_time", "wall_time", "event", "from_source", "to_source", "reason", "pose_jump_m", "orientation_jump_deg")])
        rospy.logwarn("[FusionEvent] %s", text)

    def is_metric_recovery_source(self, source: str) -> bool:
        return source in (self.metric_source, self.tertiary_source)

    def metric_restart_recovery_status(self, source: str, status: dict) -> bool:
        if not self.is_metric_recovery_source(source):
            return False
        if not getattr(self, "sensor_outage_active", {}).get(source, False):
            # No required sensor has actually been unavailable recently, so a
            # discontinuity/unrealistic-kinematics reason here is a genuine
            # estimator fault (corrupted pose), not a sensor-recovery restart.
            # Let the normal unhealthy/failover path handle it instead of
            # force-reanchoring the fused output onto a bad pose.
            return False
        reasons = set(status.get("reasons", []))
        if not reasons or reasons & RECOVERY_BLOCKING_REASONS:
            return False
        sensor_available = status.get("sensor_available") or {}
        for reason in reasons - METRIC_RESTART_REASONS:
            if reason.endswith("_unavailable"):
                sensor_name = reason[:-len("_unavailable")]
                if not bool(sensor_available.get(sensor_name, False)):
                    return False
        return all(bool(value) for value in sensor_available.values()) if sensor_available else True

    def recovery_override_active(self, source: str) -> bool:
        until = getattr(self, "recovery_override_until", {}).get(source, 0.0)
        if time.monotonic() > until:
            return False
        data = self.sources.get(source)
        if data is None or data.latest_msg is None or data.latest_T is None:
            return False
        return self.metric_restart_recovery_status(source, data.health)

    def health_cb(self, source: str, msg: String) -> None:
        try:
            status = json.loads(msg.data)
        except Exception as exc:
            rospy.logwarn_throttle(2.0, "[Fusion] invalid %s health JSON: %s", source, exc)
            return
        with self.lock:
            data = self.sources[source]
            was_healthy = bool(data.health.get("healthy", False))
            data.update_health(status, time.monotonic())
            is_healthy = bool(data.health.get("healthy", False))
            if not hasattr(self, "force_reanchor"):
                self.force_reanchor = {}
            if not hasattr(self, "recovery_override_until"):
                self.recovery_override_until = {}
            if not hasattr(self, "sensor_outage_active"):
                self.sensor_outage_active = {}
            reasons_now = set(status.get("reasons", []))
            if any(reason.endswith("_unavailable") for reason in reasons_now):
                self.sensor_outage_active[source] = True
            if self.metric_restart_recovery_status(source, status):
                if not self.recovery_override_active(source):
                    self.force_reanchor[source] = True
                self.recovery_override_until[source] = (
                    time.monotonic() + getattr(self, "lidar_recovery_override", 8.0)
                )
                # This outage episode has now been consumed as a legitimate
                # reentry trigger; a later bare discontinuity with no fresh
                # sensor loss must not be treated as another restart.
                self.sensor_outage_active[source] = False
                return
            if not is_healthy:
                self.force_reanchor[source] = True
            elif not was_healthy and is_healthy:
                self.force_reanchor[source] = True

    def odom_cb(self, source: str, msg: Odometry) -> None:
        try:
            T = pose_to_matrix(msg.pose.pose)
        except Exception as exc:
            rospy.logwarn_throttle(2.0, "[Fusion] rejected invalid %s odometry: %s", source, exc)
            return
        stamp = msg.header.stamp.to_sec()
        if stamp <= 0.0:
            rospy.logwarn_throttle(2.0, "[Fusion] rejected zero timestamp from %s", source)
            return
        with self.lock:
            data = self.sources[source]
            if data.latest_stamp is not None and stamp <= data.latest_stamp:
                rospy.logwarn_throttle(2.0, "[Fusion] rejected out-of-order %s stamp %.9f <= %.9f", source, stamp, data.latest_stamp)
                return
            data.latest_msg = msg
            data.latest_T = T
            data.latest_stamp = stamp
            data.buffer.append((stamp, T))
            self.write_raw_csv_row(source, msg)
            self.update_cross_alignment(source)

    def nearest_sample(self, data: SourceData, stamp: float) -> Optional[Tuple[float, np.ndarray]]:
        if not data.buffer:
            return None
        candidate = min(data.buffer, key=lambda item: abs(item[0] - stamp))
        return candidate if abs(candidate[0] - stamp) <= self.sync_slop else None

    def metric_source_pose(self, source: str, source_T: np.ndarray) -> np.ndarray:
        if source == self.metric_source:
            return source_T.copy()
        if self.enable_tertiary and source == self.tertiary_source:
            return source_T.copy()
        if self.cross_fast_from_orb is not None and self.orb_metric_scale is not None:
            return apply_camera_to_base_similarity(
                self.cross_fast_from_orb, self.orb_metric_scale,
                self.orb_camera_to_base, source_T
            )
        # This branch is disabled by default. It exists only for a user-supplied
        # explicit unit-scale override, and continuity alignment is still applied.
        fallback_alignment = np.eye(4)
        return apply_camera_to_base_similarity(
            fallback_alignment, self.source_scale[ORB], self.orb_camera_to_base, source_T
        )

    def update_cross_alignment(self, source: str) -> None:
        if source not in (self.orb_alignment_source, ORB):
            return
        current = self.sources[source]
        other_name = ORB if source == self.orb_alignment_source else self.orb_alignment_source
        other = self.sources[other_name]
        if current.latest_stamp is None or current.latest_T is None:
            return
        match = self.nearest_sample(other, current.latest_stamp)
        if match is None:
            return
        if source == self.orb_alignment_source:
            reference_stamp, orb_stamp = current.latest_stamp, match[0]
            T_reference, T_orb = current.latest_T.copy(), match[1].copy()
        else:
            reference_stamp, orb_stamp = match[0], current.latest_stamp
            T_reference, T_orb = match[1].copy(), current.latest_T.copy()
        pair_key = (reference_stamp, orb_stamp)
        if self.last_pair_key == pair_key:
            return
        self.last_pair_key = pair_key
        # Never learn scale/alignment from an estimator already declared unhealthy.
        if not all(bool(self.sources[name].health.get("healthy", False)) for name in (self.orb_alignment_source, ORB)):
            return
        # Keep the accepted ORB alignment fixed while ORB is the active
        # fallback. A separate recovery candidate is still learned from fresh
        # post-failure overlap and used only to decide whether primary recovery
        # is geometrically consistent.
        if self.active_source == ORB:
            self.update_recovery_alignment(T_reference, T_orb)
            self.update_disagreement(T_reference, T_orb)
            return
        self.synchronized_pairs.append((T_reference, T_orb))
        try:
            estimate = self.estimate_alignment(self.synchronized_pairs, "primary")
        except ValueError as exc:
            rospy.logwarn_throttle(2.0, "[Fusion] camera/base alignment not ready: %s", exc)
            estimate = None
        if estimate is not None:
            alignment, scale, position_rmse, orientation_rmse = estimate
            self.cross_fast_from_orb = alignment
            self.orb_metric_scale = scale
            self.source_scale[ORB] = scale
            self.alignment_quality = {
                "position_rmse_m": position_rmse,
                "orientation_rmse_rad": orientation_rmse,
            }
        self.update_disagreement(T_reference, T_orb)

    def update_disagreement(self, T_metric: np.ndarray, T_orb: np.ndarray) -> None:
        if self.cross_fast_from_orb is None or self.orb_metric_scale is None:
            self.disagreement = {"position_m": None, "orientation_rad": None, "scale_ratio": None, "valid": False}
            return
        aligned_orb = self.metric_source_pose(ORB, T_orb)
        delta = invert_transform(T_metric) @ aligned_orb
        self.disagreement = {
            "position_m": float(np.linalg.norm(delta[:3, 3])),
            "orientation_rad": rotation_angle(delta[:3, :3]),
            "scale_ratio": float(self.orb_metric_scale),
            "valid": True,
        }

    def estimate_alignment(self, pairs, label: str):
        minimum = 1 if self.orb_fixed_scale > 0.0 else self.min_alignment_pairs
        if len(pairs) < minimum:
            return None
        alignment, scale, position_rmse, orientation_rmse = estimate_camera_to_base_similarity(
            list(pairs), self.orb_camera_to_base, self.orb_fixed_scale
        )
        scale_ok = self.scale_ratio_min <= scale <= self.scale_ratio_max
        quality_ok = (position_rmse <= self.max_alignment_rmse and
                      orientation_rmse <= self.max_alignment_orientation_rmse)
        if not scale_ok or not quality_ok:
            rospy.logwarn_throttle(2.0,
                "[Fusion] rejected %s ORB alignment scale=%.3f pos_rmse=%.3f rot_rmse=%.1fdeg",
                label, scale, position_rmse, math.degrees(orientation_rmse))
            return None
        return alignment, scale, position_rmse, orientation_rmse

    def update_recovery_alignment(self, T_metric: np.ndarray, T_orb: np.ndarray) -> None:
        self.recovery_pairs.append((T_metric, T_orb))
        try:
            estimate = self.estimate_alignment(self.recovery_pairs, "recovery")
        except ValueError as exc:
            rospy.logwarn_throttle(2.0, "[Fusion] recovery alignment not ready: %s", exc)
            return
        if estimate is None:
            self.recovery_cross_fast_from_orb = None
            self.recovery_orb_metric_scale = None
            self.recovery_disagreement = {"position_m": None, "orientation_rad": None,
                                          "scale_ratio": None, "valid": False}
            return
        alignment, scale, position_rmse, orientation_rmse = estimate
        self.recovery_cross_fast_from_orb = alignment
        self.recovery_orb_metric_scale = scale
        self.recovery_alignment_quality = {
            "position_rmse_m": position_rmse,
            "orientation_rmse_rad": orientation_rmse,
        }
        aligned_orb = apply_camera_to_base_similarity(
            alignment, scale, self.orb_camera_to_base, T_orb
        )
        delta = invert_transform(T_metric) @ aligned_orb
        self.recovery_disagreement = {
            "position_m": float(np.linalg.norm(delta[:3, 3])),
            "orientation_rad": rotation_angle(delta[:3, :3]),
            "scale_ratio": float(scale),
            "valid": True,
        }

    def reset_recovery_alignment(self) -> None:
        self.recovery_pairs.clear()
        self.recovery_cross_fast_from_orb = None
        self.recovery_orb_metric_scale = None
        self.recovery_disagreement = {"position_m": None, "orientation_rad": None,
                                      "scale_ratio": None, "valid": False}
        self.recovery_alignment_quality = {"position_rmse_m": None, "orientation_rmse_rad": None}

    def clear_overlap_buffers(self, reason: str) -> None:
        if not self.synchronized_pairs and not self.recovery_pairs:
            return
        self.synchronized_pairs.clear()
        self.last_pair_key = None
        self.reset_recovery_alignment()
        self.publish_event("alignment_overlap_reset", self.metric_source, ORB, reason, 0.0)

    def invalidate_orb_alignment(self, reason: str) -> None:
        """Require fresh healthy overlap after ORB tracking/map continuity is lost."""
        if self.cross_fast_from_orb is None and self.orb_fixed_scale <= 0.0:
            return
        self.synchronized_pairs.clear()
        self.last_pair_key = None
        self.reset_recovery_alignment()
        self.cross_fast_from_orb = None
        self.orb_metric_scale = self.orb_fixed_scale if self.orb_fixed_scale > 0.0 else None
        self.source_scale[ORB] = self.orb_metric_scale if self.orb_metric_scale is not None else 1.0
        self.alignment_quality = {"position_rmse_m": None, "orientation_rmse_rad": None}
        self.disagreement = {"position_m": None, "orientation_rad": None,
                             "scale_ratio": None, "valid": False}
        self.publish_event("alignment_invalidated", ORB, ORB, reason, 0.0)

    def source_usable(self, source: str, now: float, stable_duration: float) -> bool:
        if not self.sources[source].stable_healthy(now, stable_duration):
            return False
        if source == ORB and not self.allow_orb_without_validated_scale:
            return self.orb_metric_scale is not None and self.cross_fast_from_orb is not None
        return True

    def consistency_ok(self, recovery: bool = False) -> bool:
        disagreement = self.recovery_disagreement if recovery else self.disagreement
        if not disagreement.get("valid"):
            return False
        max_pos = self.recovery_disagreement_m if recovery else self.max_disagreement_m
        max_ang = self.recovery_disagreement_rad if recovery else self.max_disagreement_rad
        scale = disagreement.get("scale_ratio")
        scale_ok = scale is None or self.scale_ratio_min <= scale <= self.scale_ratio_max
        return (disagreement["position_m"] <= max_pos and
                disagreement["orientation_rad"] <= max_ang and scale_ok)

    def primary_recovery_allowed(self, active_source: Optional[str] = None) -> Tuple[bool, str]:
        recovery_consistent = self.consistency_ok(recovery=True)
        if recovery_consistent:
            return True, "primary_recovered_and_consistent"
        if not self.require_recovery_consistency:
            return True, "primary_recovered_continuity_aligned"
        # The example fail-safe path requires fresh FAST/ORB overlap before
        # returning from ORB after a LiDAR/IMU outage. For metric-to-metric
        # camera recovery (LVI-SAM -> FAST-LIVO2), there is no ORB similarity
        # to validate, so the continuity transform is the safety mechanism.
        if active_source not in (None, ORB) and not self.recovery_disagreement.get("valid"):
            return True, "primary_recovered_without_recovery_overlap"
        return False, ""

    def source_failure_persisted(self, source: str, now: float) -> bool:
        data = self.sources[source]
        return (not bool(data.health.get("healthy", False)) and data.unhealthy_since is not None and
                now - data.unhealthy_since >= self.failure_hold)

    def source_label(self, source: str) -> str:
        if source == self.metric_source:
            return f"PRIMARY_{self.metric_source.upper()}"
        if self.enable_tertiary and source == self.tertiary_source:
            return f"BACKUP_{self.tertiary_source.upper()}"
        if source == ORB:
            return "BACKUP_ORB_SLAM3"
        return f"ACTIVE_{source.upper()}"

    def choose_initial_source(self, now: float) -> Optional[str]:
        order = [self.metric_source]
        if self.primary in order:
            order = [self.primary] + [s for s in order if s != self.primary]
        for source in order:
            if self.source_usable(source, now, self.recovery_stabilization):
                return source
        return None

    def declare_failed(self, reason: str) -> None:
        old = self.active_source
        self.active_source = FAILED
        self.state = "FAILED_ALL_UNHEALTHY"
        self.nav_ok_pub.publish(Bool(data=False))
        self.publish_event("failure", old, FAILED, reason, 0.0)

    def evaluate_fusion1(self, now: float) -> None:
        """FAST-LIVO2 primary; hard LiDAR/IMU loss can use ORB fallback."""
        active = self.active_source
        metric, tertiary = self.metric_source, self.tertiary_source
        dwell_ok = now - self.last_switch_wall >= self.minimum_dwell

        if active == metric:
            if self.source_failure_persisted(metric, now):
                reasons = set(self.sources[metric].health.get("reasons", []))
                reason_text = ",".join(sorted(reasons)) or "unhealthy"
                hard_sensor_failure = bool(reasons & LIDAR_OR_IMU_DOWN)
                if reasons & LIDAR_OR_IMU_DOWN and self.source_usable(ORB, now, self.recovery_stabilization):
                    self.switch_to(ORB, f"{metric}_unhealthy_sensor_fallback:{reason_text}")
                    return
                if self.enable_tertiary and reasons & CAMERA_DOWN and self.source_usable(tertiary, now, self.recovery_stabilization):
                    self.switch_to(tertiary, f"{metric}_unhealthy_camera_fallback:{reason_text}")
                    return
                if self.enable_tertiary and hard_sensor_failure and self.source_usable(tertiary, now, self.recovery_stabilization):
                    self.switch_to(tertiary, f"{metric}_unhealthy_fallback:{reason_text}")
                    return
                self.state = f"PRIMARY_{metric.upper()}_UNHEALTHY_NO_FALLBACK"
                self.nav_ok_pub.publish(Bool(data=False))
                return
            self.state = self.source_label(metric)

        elif active == tertiary:
            if dwell_ok and self.source_usable(metric, now, self.primary_recovery):
                recovery_allowed, reason = self.primary_recovery_allowed(active)
                if recovery_allowed:
                    self.switch_to(metric, reason)
                    return
            if self.source_failure_persisted(tertiary, now):
                reasons = ",".join(self.sources[tertiary].health.get("reasons", ["unhealthy"]))
                if self.source_usable(ORB, now, self.recovery_stabilization):
                    self.switch_to(ORB, f"{tertiary}_unhealthy_fallback:{reasons}")
                    return
                self.state = f"BACKUP_{tertiary.upper()}_UNHEALTHY_NO_FALLBACK"
                self.nav_ok_pub.publish(Bool(data=False))
                return
            self.state = self.source_label(tertiary)

        else:  # active == ORB
            if dwell_ok:
                if self.source_usable(metric, now, self.primary_recovery):
                    recovery_allowed, reason = self.primary_recovery_allowed(active)
                    if recovery_allowed:
                        self.switch_to(metric, reason)
                        return
                elif self.enable_tertiary and self.source_usable(tertiary, now, self.recovery_stabilization):
                    self.switch_to(tertiary, "orb_active_lidar_imu_recovered_camera_still_down")
                    return
            if self.source_failure_persisted(ORB, now):
                self.declare_failed("orb_unhealthy_no_fallback")
                return
            self.state = self.source_label(ORB)

        if active == ORB and all(bool(self.sources[s].health.get("healthy", False)) for s in (metric, ORB)) and not self.consistency_ok():
            self.state += "_DEGRADED_DISAGREEMENT"

    def evaluate_fusion2(self, now: float) -> None:
        """LVI-SAM primary; LiDAR/IMU loss -> ORB-SLAM3; ORB loss -> fusion fails."""
        active = self.active_source
        metric = self.metric_source
        dwell_ok = now - self.last_switch_wall >= self.minimum_dwell

        if active == metric:
            if self.source_failure_persisted(metric, now):
                reasons = ",".join(self.sources[metric].health.get("reasons", ["unhealthy"]))
                if self.source_usable(ORB, now, self.recovery_stabilization):
                    self.switch_to(ORB, f"{metric}_unhealthy_fallback:{reasons}")
                    return
                self.state = f"PRIMARY_{metric.upper()}_UNHEALTHY_NO_ORB_FALLBACK"
                self.nav_ok_pub.publish(Bool(data=False))
                return
            self.state = self.source_label(metric)
        else:  # active == ORB
            if dwell_ok and self.source_usable(metric, now, self.primary_recovery):
                recovery_allowed, reason = self.primary_recovery_allowed(active)
                if recovery_allowed:
                    self.switch_to(metric, reason)
                    return
            if self.source_failure_persisted(ORB, now):
                self.declare_failed("orb_unhealthy_no_lvisam_fallback")
                return
            self.state = self.source_label(ORB)

        if active == ORB and all(bool(self.sources[s].health.get("healthy", False)) for s in (metric, ORB)) and not self.consistency_ok():
            self.state += "_DEGRADED_DISAGREEMENT"

    def evaluate_state_machine(self, now: float) -> None:
        ros_now = rospy.Time.now().to_sec()
        if ros_now <= 0.0:
            self.state = "WAITING_FOR_BAG_CLOCK"
            self.nav_ok_pub.publish(Bool(data=False))
            return
        if self.bag_start_wall is None:
            self.bag_start_wall = now
            self.publish_event("bag_clock_started", FAILED, FAILED, "waiting_for_localization_start_delay", 0.0)
        elapsed_since_bag_start = now - self.bag_start_wall
        if elapsed_since_bag_start < self.localization_start_delay:
            self.state = "WAITING_FOR_LOCALIZATION_START_DELAY"
            self.nav_ok_pub.publish(Bool(data=False))
            return

        orb = self.sources[ORB]
        orb_reasons = set(orb.health.get("reasons", []))
        alignment_breaking_reasons = {
            "camera_unavailable",
            "process_not_present",
            "tracking_lost",
            "timestamp_regression",
            "non_finite_or_invalid_pose",
        }
        if (self.cross_fast_from_orb is not None and
                not bool(orb.health.get("healthy", False)) and
                orb.unhealthy_since is not None and
                now - orb.unhealthy_since >= self.failure_hold and
                bool(orb_reasons & alignment_breaking_reasons)):
            reasons = ",".join(sorted(orb_reasons)) or "unhealthy"
            self.invalidate_orb_alignment(f"orb_unhealthy:{reasons}")

        metric = self.sources[self.metric_source]
        alignment_reference = self.sources[self.orb_alignment_source]
        metric_reasons = set(metric.health.get("reasons", []))
        alignment_reference_reasons = set(alignment_reference.health.get("reasons", []))
        metric_overlap_breaking_reasons = {
            "lidar_unavailable",
            "imu_unavailable",
            "camera_unavailable",
            "timestamp_regression",
            "frozen_or_repeated_output",
            "stale_pose",
            "delayed_pose_timestamp",
            "pose_rate_too_low",
            "non_finite_or_invalid_pose",
            "position_discontinuity",
            "orientation_discontinuity",
            "process_not_present",
        }
        reference_reset_reason = ",".join(sorted(alignment_reference_reasons & metric_overlap_breaking_reasons))
        reset_reason = ",".join(sorted(metric_reasons & metric_overlap_breaking_reasons))
        reset_source = self.orb_alignment_source if reference_reset_reason else self.metric_source
        reset_reasons = reference_reset_reason or reset_reason
        reset_data = self.sources[reset_source]
        if (reset_reasons and not bool(reset_data.health.get("healthy", False)) and
                reset_data.unhealthy_since is not None and
                now - reset_data.unhealthy_since >= self.failure_hold and
                f"{reset_source}:{reset_reasons}" != self.last_metric_fault_reset_reason):
            self.last_metric_fault_reset_reason = f"{reset_source}:{reset_reasons}"
            self.clear_overlap_buffers(f"{reset_source}_unhealthy:{reset_reasons}")
        elif bool(metric.health.get("healthy", False)) and bool(alignment_reference.health.get("healthy", False)):
            self.last_metric_fault_reset_reason = None

        if self.active_source == FAILED:
            selected = self.choose_initial_source(now)
            if selected:
                self.switch_to(selected, "initial_healthy_source")
            else:
                self.state = "WAITING_FOR_LOCALIZATION"
            return

        if self.mode == "fusion1":
            self.evaluate_fusion1(now)
        else:
            self.evaluate_fusion2(now)

    def switch_to(self, new_source: str, reason: str) -> None:
        data = self.sources[new_source]
        if data.latest_T is None:
            return
        old = self.active_source
        before = self.last_output_T.copy() if self.last_output_T is not None else None
        if new_source == ORB and self.orb_metric_scale is not None:
            self.source_scale[ORB] = self.orb_metric_scale
        if (new_source == self.metric_source and self.recovery_cross_fast_from_orb is not None and
                self.recovery_orb_metric_scale is not None):
            self.cross_fast_from_orb = self.recovery_cross_fast_from_orb
            self.orb_metric_scale = self.recovery_orb_metric_scale
            self.source_scale[ORB] = self.recovery_orb_metric_scale
            self.alignment_quality = dict(self.recovery_alignment_quality)
            self.synchronized_pairs = collections.deque(self.recovery_pairs, maxlen=self.alignment_window)
            self.reset_recovery_alignment()
        native_metric_pose = self.metric_source_pose(new_source, data.latest_T)
        if before is None:
            self.source_to_output[new_source] = np.eye(4)
            after = native_metric_pose
        else:
            # This transform makes the first pose from the new source exactly equal
            # to the last fused pose, preserving position and orientation continuity.
            self.source_to_output[new_source] = before @ invert_transform(native_metric_pose)
            after = self.source_to_output[new_source] @ native_metric_pose
        jump = 0.0 if before is None else float(np.linalg.norm(after[:3, 3] - before[:3, 3]))
        self.active_source = new_source
        self.last_switch_wall = time.monotonic()
        self.switch_start_wall = self.last_switch_wall
        self.switch_anchor_T = before
        self.last_output_source_stamp[new_source] = None
        self.switch_count += 1
        self.state = self.source_label(new_source)
        self.pending_switch_event = ({"old": old, "new": new_source, "reason": reason}
                                     if before is not None else None)
        self.publish_event("switch", old, new_source, reason, jump)

    def transformed_active_pose(self, now: float) -> Optional[Tuple[Odometry, np.ndarray]]:
        if self.active_source == FAILED:
            return None
        data = self.sources[self.active_source]
        if data.latest_msg is None or data.latest_T is None or data.latest_stamp is None:
            return None
        if self.last_output_source_stamp[self.active_source] is not None and data.latest_stamp <= self.last_output_source_stamp[self.active_source]:
            return None
        if (getattr(self, "force_reanchor", {}).get(self.active_source, False) and
                bool(data.health.get("healthy", False))):
            # Only fold a pending reanchor into the live output once this
            # source is actually reporting healthy again -- reanchoring while
            # it is still unhealthy would bake a corrupted/jumping pose
            # straight into the fused output instead of letting the normal
            # failure_hold_sec failover reject it.
            self.align_source_for_reentry(self.active_source, "health_recovery_active")
        T_target = self.source_to_output[self.active_source] @ self.metric_source_pose(
            self.active_source, data.latest_T
        )
        T_out = T_target
        self.last_blend_alpha = 1.0
        if self.switch_anchor_T is not None and self.switch_start_wall is not None and self.blend_duration > 0.0:
            alpha = (now - self.switch_start_wall) / self.blend_duration
            if alpha < 1.0:
                # alpha is the new source's weight (0 at the switch instant, 1 once
                # settled); the outgoing source's contribution is (1 - alpha).
                T_out = interpolate_transform(self.switch_anchor_T, T_target, alpha)
                self.last_blend_alpha = max(0.0, alpha)
            else:
                self.switch_anchor_T = None
                self.switch_start_wall = None
        return data.latest_msg, T_out

    def transformed_source_pose(self, source: str) -> Optional[Tuple[Odometry, np.ndarray]]:
        data = self.sources.get(source)
        if data is None or data.latest_msg is None or data.latest_T is None:
            return None
        if getattr(self, "force_reanchor", {}).get(source, False):
            self.align_source_for_reentry(source, "health_recovery")
        return data.latest_msg, self.source_to_output[source] @ self.metric_source_pose(source, data.latest_T)

    def source_fusion_ready(self, source: str) -> bool:
        data = self.sources.get(source)
        if data is None or data.latest_msg is None or data.latest_T is None:
            return False
        if not bool(data.health.get("healthy", False)):
            return False
        if source == ORB:
            return self.orb_metric_scale is not None and self.cross_fast_from_orb is not None
        return True

    def weighted_source_order(self) -> list:
        sources = list(getattr(self, "weighted_sources", []))
        if not sources:
            sources = [self.metric_source]
            if self.enable_tertiary:
                sources.append(self.tertiary_source)
            sources.append(ORB)
        return [source for source in sources if source in self.sources]

    def source_output_consistent(self, source: str) -> bool:
        if getattr(self, "force_reanchor", {}).get(source, False):
            self.align_source_for_reentry(source, "health_recovery")
            return True
        if self.last_output_T is None or self.fusion_weights.get(source, 0.0) <= 1.0e-4:
            return True
        pose = self.transformed_source_pose(source)
        if pose is None:
            return False
        delta = invert_transform(self.last_output_T) @ pose[1]
        position_delta = float(np.linalg.norm(delta[:3, 3]))
        rotation_delta = rotation_angle(delta[:3, :3])
        if position_delta <= self.max_disagreement_m and rotation_delta <= self.max_disagreement_rad:
            return True
        if source == ORB:
            self.align_source_for_reentry(source, "orb_loop_closure_reanchor")
            return True
        return False

    def align_source_for_reentry(self, source: str, reason: str = "weighted_fusion_reentry") -> None:
        if self.last_output_T is None:
            if source not in self.source_to_output:
                self.source_to_output[source] = np.eye(4)
            if not hasattr(self, "force_reanchor"):
                self.force_reanchor = {}
            self.force_reanchor[source] = False
            return
        data = self.sources.get(source)
        if data is None or data.latest_T is None:
            return
        native_metric_pose = self.metric_source_pose(source, data.latest_T)
        self.source_to_output[source] = self.last_output_T @ invert_transform(native_metric_pose)
        if not hasattr(self, "force_reanchor"):
            self.force_reanchor = {}
        self.force_reanchor[source] = False
        if hasattr(self, "aligned_source_paths") and source in self.aligned_source_paths:
            self.aligned_source_paths[source] = Path()
            self.aligned_source_paths[source].header.frame_id = self.map_frame
            self.last_aligned_source_stamp[source] = None
        self.publish_event("source_reanchored", source, source, reason, 0.0)

    def weighted_targets(self, now: float) -> Dict[str, float]:
        metric_ready = self.source_fusion_ready(self.metric_source) and self.source_output_consistent(self.metric_source)
        tertiary_ready = (
            self.enable_tertiary and
            self.source_fusion_ready(self.tertiary_source) and
            self.source_output_consistent(self.tertiary_source)
        )
        orb_ready = self.source_fusion_ready(ORB) and self.source_output_consistent(ORB)
        targets = {source: 0.0 for source in self.weighted_source_order()}
        if metric_ready:
            targets[self.metric_source] = self.metric_nominal_weight
            if orb_ready and self.disagreement.get("valid") and self.consistency_ok():
                targets[ORB] = self.orb_nominal_weight
        elif tertiary_ready:
            targets[self.tertiary_source] = self.lvisam_recovery_weight
        elif orb_ready:
            targets[ORB] = self.orb_backup_weight
        total = sum(targets.values())
        if total > 1.0e-9:
            targets = {name: value / total for name, value in targets.items()}
        return targets

    def update_fusion_weights(self, targets: Dict[str, float], now: float) -> None:
        if self.last_weight_update_wall is None:
            dt = 0.0
        else:
            dt = max(0.0, now - self.last_weight_update_wall)
        self.last_weight_update_wall = now
        for source, target in targets.items():
            current = self.fusion_weights.get(source, 0.0)
            if current <= 1.0e-6 and target > 1.0e-6:
                self.align_source_for_reentry(source)
            if dt <= 0.0:
                step = 1.0
            else:
                tau = self.weight_rise_time if target > current else self.weight_fall_time
                step = 1.0 if tau <= 1.0e-6 else clamp(dt / tau, 0.0, 1.0)
            self.fusion_weights[source] = current + (target - current) * step
        target_total = sum(max(0.0, value) for value in targets.values())
        total = sum(max(0.0, value) for value in self.fusion_weights.values())
        if target_total > 1.0e-9 and total > 1.0e-9:
            for source in list(self.fusion_weights):
                self.fusion_weights[source] = max(0.0, self.fusion_weights[source]) / total
        self.target_fusion_weights = dict(targets)

    def weighted_fused_pose(self, now: float) -> Optional[Tuple[Odometry, np.ndarray]]:
        if not self.weighted_fusion_enabled or self.mode != "fusion1":
            return None
        targets = self.weighted_targets(now)
        self.update_fusion_weights(targets, now)
        candidates = []
        for source in self.weighted_source_order():
            weight = self.fusion_weights.get(source, 0.0)
            if (weight <= 1.0e-4 or not self.source_fusion_ready(source) or
                    not self.source_output_consistent(source)):
                continue
            pose = self.transformed_source_pose(source)
            if pose is None:
                continue
            candidates.append((source, weight, pose[0], pose[1]))
        if not candidates:
            self.weighted_active_label = FAILED
            self.weighted_state = "WAITING_FOR_LOCALIZATION"
            return None
        candidates.sort(key=lambda item: item[1], reverse=True)
        dominant_source, dominant_weight, _dominant_msg, fused = candidates[0]
        total_weight = dominant_weight
        for _, other_weight, _, other_T in candidates[1:]:
            alpha = clamp(other_weight / (total_weight + other_weight), 0.0, 1.0)
            fused = interpolate_transform(fused, other_T, alpha)
            total_weight += other_weight
        msg = max((item[2] for item in candidates), key=lambda item: item.header.stamp.to_sec())
        stamp = max(item[2].header.stamp.to_sec() for item in candidates)
        if self.weighted_last_stamp is not None and stamp <= self.weighted_last_stamp:
            return None
        self.weighted_last_stamp = stamp
        self.last_blend_alpha = self.fusion_weights.get(ORB, 0.0)
        self.weighted_active_label = "weighted"
        self.weighted_state = self.weighted_state_label()
        return msg, fused

    def weighted_state_label(self) -> str:
        metric_w = self.fusion_weights.get(self.metric_source, 0.0)
        tertiary_w = self.fusion_weights.get(self.tertiary_source, 0.0) if self.enable_tertiary else 0.0
        orb_w = self.fusion_weights.get(ORB, 0.0)
        if metric_w > 0.05 and orb_w > 0.05:
            return "FUSED_FAST_LIVO2_ORB_SLAM3"
        if tertiary_w > 0.05 and orb_w > 0.05:
            return "FUSED_LVISAM_ORB_SLAM3_RECOVERY"
        if tertiary_w > metric_w and tertiary_w >= orb_w:
            return "FUSED_LVISAM_RECOVERY"
        if orb_w > metric_w and orb_w > tertiary_w:
            return "FUSED_ORB_SLAM3_BACKUP"
        if metric_w > 0.0:
            return "FUSED_FAST_LIVO2_PRIMARY"
        return "WAITING_FOR_LOCALIZATION"

    def publish_aligned_source_paths(self) -> None:
        if not hasattr(self, "aligned_source_path_pubs"):
            return
        for source in self.weighted_source_order():
            data = self.sources.get(source)
            if data is None or data.latest_msg is None or data.latest_T is None or data.latest_stamp is None:
                continue
            if self.last_aligned_source_stamp.get(source) is not None and data.latest_stamp <= self.last_aligned_source_stamp[source]:
                continue
            transformed = self.transformed_source_pose(source)
            if transformed is None:
                continue
            pose = PoseStamped()
            pose.header.stamp = data.latest_msg.header.stamp
            pose.header.frame_id = self.map_frame
            pose.pose = matrix_to_pose(transformed[1])
            path = self.aligned_source_paths[source]
            path.header.stamp = pose.header.stamp
            path.poses.append(pose)
            if len(path.poses) > self.max_path_poses:
                path.poses = path.poses[-self.max_path_poses:]
            self.last_aligned_source_stamp[source] = data.latest_stamp
            pub = self.aligned_source_path_pubs.get(source)
            if pub is not None:
                pub.publish(path)

    def compute_twist(self, T: np.ndarray, stamp: float) -> Twist:
        out = Twist()
        if self.last_output_T is None or self.last_output_stamp is None or stamp <= self.last_output_stamp:
            return out
        dt = stamp - self.last_output_stamp
        if dt <= 1.0e-4:
            return out
        velocity = (T[:3, 3] - self.last_output_T[:3, 3]) / dt
        delta = invert_transform(self.last_output_T) @ T
        angle = rotation_angle(delta[:3, :3])
        axis = np.array([delta[2, 1] - delta[1, 2], delta[0, 2] - delta[2, 0], delta[1, 0] - delta[0, 1]])
        norm = float(np.linalg.norm(axis))
        angular = (axis / norm) * (angle / dt) if norm > 1.0e-9 else np.zeros(3)
        out.linear.x, out.linear.y, out.linear.z = map(float, velocity)
        out.angular.x, out.angular.y, out.angular.z = map(float, angular)
        return out

    def compute_metric_twist(self, T: np.ndarray, stamp: float) -> Twist:
        out = Twist()
        if self.last_metric_output_T is None or self.last_metric_output_stamp is None or stamp <= self.last_metric_output_stamp:
            return out
        dt = stamp - self.last_metric_output_stamp
        if dt <= 1.0e-4:
            return out
        velocity = (T[:3, 3] - self.last_metric_output_T[:3, 3]) / dt
        delta = invert_transform(self.last_metric_output_T) @ T
        angle = rotation_angle(delta[:3, :3])
        axis = np.array([delta[2, 1] - delta[1, 2], delta[0, 2] - delta[2, 0], delta[1, 0] - delta[0, 1]])
        norm = float(np.linalg.norm(axis))
        angular = (axis / norm) * (angle / dt) if norm > 1.0e-9 else np.zeros(3)
        out.linear.x, out.linear.y, out.linear.z = map(float, velocity)
        out.angular.x, out.angular.y, out.angular.z = map(float, angular)
        return out

    def tf_publish_stamp(self, source_stamp: rospy.Time) -> rospy.Time:
        if self.tf_stamp_mode == "source":
            return source_stamp
        now = rospy.Time.now()
        if now.to_sec() <= 0.0 or now < source_stamp:
            return source_stamp
        return now

    def publish_tf_for_pose(self, T_map_base: np.ndarray, stamp: rospy.Time) -> None:
        if not self.publish_tf or self.tf_broadcaster is None:
            return
        tf_stamp = self.tf_publish_stamp(stamp)
        if self.tf_mode == "direct":
            msg = TransformStamped()
            msg.header.stamp = tf_stamp
            msg.header.frame_id = self.odom_frame
            msg.child_frame_id = self.base_frame
            msg.transform.translation.x, msg.transform.translation.y, msg.transform.translation.z = map(float, T_map_base[:3, 3])
            msg.transform.rotation = matrix_to_pose(T_map_base).orientation
            self.tf_broadcaster.sendTransform(msg)
        elif self.tf_mode == "map_to_odom":
            try:
                tf = self.tf_buffer.lookup_transform(self.odom_frame, self.base_frame, tf_stamp, rospy.Duration(0.05))
                odom_pose = PoseStamped()
                odom_pose.pose.position.x = tf.transform.translation.x
                odom_pose.pose.position.y = tf.transform.translation.y
                odom_pose.pose.position.z = tf.transform.translation.z
                odom_pose.pose.orientation = tf.transform.rotation
                T_odom_base = pose_to_matrix(odom_pose.pose)
                T_map_odom = T_map_base @ invert_transform(T_odom_base)
                msg = TransformStamped()
                msg.header.stamp = tf_stamp
                msg.header.frame_id = self.map_frame
                msg.child_frame_id = self.odom_frame
                msg.transform.translation.x, msg.transform.translation.y, msg.transform.translation.z = map(float, T_map_odom[:3, 3])
                msg.transform.rotation = matrix_to_pose(T_map_odom).orientation
                self.tf_broadcaster.sendTransform(msg)
            except Exception as exc:
                rospy.logwarn_throttle(2.0, "[Fusion] cannot publish map->odom: %s", exc)

    def publish_output(self, source_msg: Odometry, T: np.ndarray,
                       output_source: Optional[str] = None,
                       output_state: Optional[str] = None) -> None:
        output_source = output_source or self.active_source
        output_state = output_state or self.state
        stamp_value = source_msg.header.stamp.to_sec()
        if self.last_output_stamp is not None and stamp_value <= self.last_output_stamp:
            return
        if self.last_output_stamp is not None and stamp_value - self.last_output_stamp > self.max_output_gap:
            self.publish_event("output_gap", output_source, output_source,
                               f"gap_sec={stamp_value - self.last_output_stamp:.3f}", 0.0)
        pose = matrix_to_pose(T)
        if output_source != "weighted" and self.pending_switch_event is not None and self.last_output_T is not None:
            delta = invert_transform(self.last_output_T) @ T
            actual_jump = float(np.linalg.norm(T[:3, 3] - self.last_output_T[:3, 3]))
            actual_angle = math.degrees(rotation_angle(delta[:3, :3]))
            event = self.pending_switch_event
            self.publish_event("switch_applied", event["old"], event["new"],
                               event["reason"], actual_jump, actual_angle)
            self.pending_switch_event = None
        odom = Odometry()
        odom.header.stamp = source_msg.header.stamp
        # In direct mode map->odom is identity and the dynamic pose is odom->base,
        # so the Odometry message follows standard ROS semantics and uses odom.
        # Global PoseStamped/Path outputs always remain in map.
        odom.header.frame_id = self.odom_frame if self.tf_mode == "direct" else self.map_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose = pose
        odom.pose.covariance = list(source_msg.pose.covariance)
        if self.state.endswith("DEGRADED_DISAGREEMENT"):
            degraded = [float(value) * 10.0 for value in odom.pose.covariance]
            for index, floor in ((0, 25.0), (7, 25.0), (14, 25.0),
                                 (21, 0.5), (28, 0.5), (35, 0.5)):
                degraded[index] = max(abs(degraded[index]), floor)
            odom.pose.covariance = degraded
        odom.twist.twist = self.compute_twist(T, stamp_value)
        odom.twist.covariance = list(source_msg.twist.covariance)
        self.odom_pub.publish(odom)
        if self.continuous_odom_pub is not None:
            self.continuous_odom_pub.publish(odom)

        ps = PoseStamped()
        ps.header.stamp = odom.header.stamp
        ps.header.frame_id = self.map_frame
        ps.pose = pose
        self.pose_pub.publish(ps)
        if self.continuous_pose_pub is not None:
            self.continuous_pose_pub.publish(ps)
        self.path.header.stamp = odom.header.stamp
        self.path.poses.append(ps)
        if len(self.path.poses) > self.max_path_poses:
            self.path.poses = self.path.poses[-self.max_path_poses:]
        self.path_pub.publish(self.path)
        if self.continuous_path_pub is not None:
            self.continuous_path_pub.publish(self.path)
        self.publish_tf_for_pose(T, odom.header.stamp)

        self.last_output_T = T.copy()
        self.last_output_stamp = stamp_value
        self.last_output_wall = time.monotonic()
        self.last_output_source_stamp[output_source] = stamp_value
        self.write_fused_csv_row(stamp_value, pose, output_source, output_state)

    def write_fused_csv_row(self, stamp_value: float, pose,
                            output_source: Optional[str] = None,
                            output_state: Optional[str] = None) -> None:
        if self.fused_csv_writer is None:
            return
        self.fused_csv_writer.writerow([
            stamp_value, pose.position.x, pose.position.y, pose.position.z,
            pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w,
            output_source or self.active_source, output_state or self.state,
            round(self.last_blend_alpha, 4), self.switch_count,
            *self.health_snapshot_row(),
        ])
        self.fused_csv_handle.flush()

    def publish_metric_output(self, source_msg: Odometry, T: np.ndarray) -> None:
        stamp_value = source_msg.header.stamp.to_sec()
        if self.last_metric_output_stamp is not None and stamp_value <= self.last_metric_output_stamp:
            return
        pose = matrix_to_pose(T)
        odom = Odometry()
        odom.header.stamp = source_msg.header.stamp
        odom.header.frame_id = self.map_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose = pose
        odom.pose.covariance = list(source_msg.pose.covariance)
        if self.state.endswith("DEGRADED_DISAGREEMENT"):
            degraded = [float(value) * 10.0 for value in odom.pose.covariance]
            for index, floor in ((0, 25.0), (7, 25.0), (14, 25.0),
                                 (21, 0.5), (28, 0.5), (35, 0.5)):
                degraded[index] = max(abs(degraded[index]), floor)
            odom.pose.covariance = degraded
        odom.twist.twist = self.compute_metric_twist(T, stamp_value)
        odom.twist.covariance = list(source_msg.twist.covariance)
        self.metric_odom_pub.publish(odom)

        ps = PoseStamped()
        ps.header.stamp = odom.header.stamp
        ps.header.frame_id = self.map_frame
        ps.pose = pose
        self.metric_pose_pub.publish(ps)
        self.metric_path.header.stamp = odom.header.stamp
        self.metric_path.poses.append(ps)
        if len(self.metric_path.poses) > self.max_path_poses:
            self.metric_path.poses = self.metric_path.poses[-self.max_path_poses:]
        self.metric_path_pub.publish(self.metric_path)

        self.last_metric_output_T = T.copy()
        self.last_metric_output_stamp = stamp_value

    def status_payload(self) -> dict:
        weighted_mode = self.weighted_fusion_enabled and self.mode == "fusion1"
        weighted_valid = (
            weighted_mode and
            sum(self.fusion_weights.values()) > 1.0e-4 and
            self.weighted_active_label == "weighted"
        )
        status_state = self.weighted_state if weighted_valid else self.state
        status_active = "weighted" if weighted_mode else self.active_source
        return {
            "stamp": rospy.Time.now().to_sec(),
            "state": status_state,
            "valid": weighted_valid if weighted_mode else (
                self.active_source != FAILED and bool(self.sources[self.active_source].health.get("healthy", False))
            ),
            "active_source": status_active,
            "mode": self.mode,
            "primary_source": self.primary,
            "metric_source": self.metric_source,
            "fusion_strategy": "weighted" if self.weighted_fusion_enabled else "switch",
            "fusion_weights": {name: round(value, 4) for name, value in self.fusion_weights.items()},
            "target_fusion_weights": {name: round(value, 4) for name, value in self.target_fusion_weights.items()},
            "orb_alignment_source": self.orb_alignment_source,
            "tertiary_source": self.tertiary_source if self.enable_tertiary else None,
            "switch_count": self.switch_count,
            "blend_alpha": round(self.last_blend_alpha, 4),
            "tf_mode": self.tf_mode,
            "tf_stamp_mode": self.tf_stamp_mode,
            "frames": {"map": self.map_frame, "odom": self.odom_frame, "base": self.base_frame},
            "health": {name: data.health for name, data in self.sources.items()},
            "sensors": {
                "lidar": self.sensor_status("lidar"),
                "imu": self.sensor_status("imu"),
                "camera": self.sensor_status("camera"),
            },
            "orb_metric_scale_ready": self.orb_metric_scale is not None and self.cross_fast_from_orb is not None,
            "orb_metric_scale": self.orb_metric_scale,
            "alignment_quality": {
                "position_rmse_m": self.alignment_quality.get("position_rmse_m"),
                "orientation_rmse_deg": None if self.alignment_quality.get("orientation_rmse_rad") is None else math.degrees(self.alignment_quality["orientation_rmse_rad"]),
            },
            "recovery_alignment_quality": {
                "position_rmse_m": self.recovery_alignment_quality.get("position_rmse_m"),
                "orientation_rmse_deg": None if self.recovery_alignment_quality.get("orientation_rmse_rad") is None else math.degrees(self.recovery_alignment_quality["orientation_rmse_rad"]),
            },
            "disagreement": {
                "position_m": self.disagreement.get("position_m"),
                "orientation_deg": None if self.disagreement.get("orientation_rad") is None else math.degrees(self.disagreement["orientation_rad"]),
                f"scale_ratio_{self.orb_alignment_source}_over_orb": self.disagreement.get("scale_ratio"),
                "consistent": self.consistency_ok() if self.disagreement.get("valid") else False,
                "recovery_position_m": self.recovery_disagreement.get("position_m"),
                "recovery_orientation_deg": None if self.recovery_disagreement.get("orientation_rad") is None else math.degrees(self.recovery_disagreement["orientation_rad"]),
                "recovery_consistent": self.consistency_ok(recovery=True) if self.recovery_disagreement.get("valid") else False,
                "required_for_primary_recovery": self.require_recovery_consistency,
            },
        }

    def timer_cb(self, _event) -> None:
        with self.lock:
            now = time.monotonic()
            self.evaluate_state_machine(now)
            if self.state in (
                "WAITING_FOR_BAG_CLOCK",
                "WAITING_FOR_LOCALIZATION_START_DELAY",
                "WAITING_FOR_LOCALIZATION",
            ):
                self.publish_aligned_source_paths()
                if self.stop_navigation_on_failure:
                    self.nav_ok_pub.publish(Bool(data=False))
                else:
                    self.nav_ok_pub.publish(Bool(data=True))
                self.active_pub.publish(String(data=self.active_source))
                self.status_pub.publish(String(data=json.dumps(self.status_payload(), sort_keys=True)))
                return
            weighted_mode = self.weighted_fusion_enabled and self.mode == "fusion1"
            weighted = self.weighted_fused_pose(now) if weighted_mode else None
            if weighted_mode:
                if weighted is not None:
                    self.publish_output(weighted[0], weighted[1], "weighted", self.weighted_state)
                elif self.last_output_T is not None:
                    self.publish_tf_for_pose(self.last_output_T, rospy.Time.now())
            else:
                active = self.transformed_active_pose(now)
                if active is not None and bool(self.sources[self.active_source].health.get("healthy", False)):
                    self.publish_output(active[0], active[1])
                elif (self.active_source != FAILED and self.last_output_T is not None and
                      bool(self.sources[self.active_source].health.get("healthy", False))):
                    self.publish_tf_for_pose(self.last_output_T, rospy.Time.now())
            metric_data = self.sources[self.metric_source]
            if (metric_data.latest_msg is not None and metric_data.latest_T is not None and
                    bool(metric_data.health.get("healthy", False))):
                self.publish_metric_output(metric_data.latest_msg, metric_data.latest_T)
            self.publish_aligned_source_paths()
            degraded = self.state.endswith("DEGRADED_DISAGREEMENT")
            weighted_valid = weighted_mode and self.weighted_active_label == "weighted"
            navigation_ok = (
                (weighted_valid if weighted_mode else (
                    self.active_source != FAILED and
                    bool(self.sources[self.active_source].health.get("healthy", False))
                )) and
                not degraded
            )
            if self.stop_navigation_on_failure:
                self.nav_ok_pub.publish(Bool(data=navigation_ok))
            else:
                self.nav_ok_pub.publish(Bool(data=True))
            self.active_pub.publish(String(data="weighted" if weighted_mode else self.active_source))
            self.status_pub.publish(String(data=json.dumps(self.status_payload(), sort_keys=True)))


def main() -> None:
    rospy.init_node("e2o_localization_fusion")
    LocalizationFusion()
    rospy.spin()


if __name__ == "__main__":
    main()
