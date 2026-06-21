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


def as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


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
        self.map_frame = str(cfg.get("map_frame", "map"))
        self.odom_frame = str(cfg.get("odom_frame", "odom"))
        self.base_frame = str(cfg.get("base_frame", "base_link"))
        self.tf_mode = str(cfg.get("tf_mode", "direct")).strip().lower()
        if self.tf_mode not in ("direct", "map_to_odom", "none"):
            raise rospy.ROSInitException("tf_mode must be direct, map_to_odom, or none")
        self.publish_tf = as_bool(cfg.get("publish_tf", True)) and self.tf_mode != "none"
        self.publish_rate_hz = float(cfg.get("publish_rate_hz", 30.0))
        self.sync_slop = float(cfg.get("sync_slop_sec", 0.05))
        self.alignment_window = int(cfg.get("alignment_window", 40))
        self.min_alignment_pairs = int(cfg.get("min_alignment_pairs", 8))
        self.failure_hold = float(cfg.get("failure_hold_sec", 0.35))
        self.recovery_stabilization = float(cfg.get("recovery_stabilization_sec", 3.0))
        self.primary_recovery = float(cfg.get("primary_recovery_sec", 5.0))
        self.minimum_dwell = float(cfg.get("minimum_source_dwell_sec", 3.0))
        self.blend_duration = float(cfg.get("blend_duration_sec", 1.0))
        self.max_disagreement_m = float(cfg.get("max_disagreement_m", 4.0))
        self.max_disagreement_rad = math.radians(float(cfg.get("max_disagreement_deg", 35.0)))
        self.recovery_disagreement_m = float(cfg.get("recovery_disagreement_m", 2.0))
        self.recovery_disagreement_rad = math.radians(float(cfg.get("recovery_disagreement_deg", 20.0)))
        self.scale_ratio_min = float(cfg.get("orb_scale_ratio_min", 0.5))
        self.scale_ratio_max = float(cfg.get("orb_scale_ratio_max", 2.0))
        self.max_alignment_rmse = float(cfg.get("max_alignment_rmse_m", 1.5))
        self.max_alignment_orientation_rmse = math.radians(float(cfg.get("max_alignment_orientation_rmse_deg", 20.0)))
        self.orb_fixed_scale = float(cfg.get("orb_fixed_scale", 0.0))
        self.allow_orb_without_validated_scale = as_bool(cfg.get("allow_orb_without_validated_scale", False))
        self.max_output_gap = float(cfg.get("max_output_gap_sec", 1.0))
        self.max_path_poses = int(cfg.get("max_path_poses", 100000))
        self.event_log_path = str(cfg.get("event_log_path", "/data/output/fusion_events.csv"))
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
        self.synchronized_pairs: Deque[Tuple[np.ndarray, np.ndarray]] = collections.deque(maxlen=self.alignment_window)
        self.cross_fast_from_orb: Optional[np.ndarray] = None
        self.orb_metric_scale: Optional[float] = self.orb_fixed_scale if self.orb_fixed_scale > 0.0 else None
        self.disagreement = {"position_m": None, "orientation_rad": None, "scale_ratio": None, "valid": False}
        self.alignment_quality = {"position_rmse_m": None, "orientation_rmse_rad": None}
        self.last_pair_key: Optional[Tuple[float, float]] = None

        self.active_source = FAILED
        self.state = "WAITING_FOR_LOCALIZATION"
        self.last_switch_wall = 0.0
        self.switch_count = 0
        self.switch_start_wall: Optional[float] = None
        self.switch_anchor_T: Optional[np.ndarray] = None
        self.pending_switch_event: Optional[dict] = None
        self.last_output_T: Optional[np.ndarray] = None
        self.last_output_stamp: Optional[float] = None
        self.last_output_wall: Optional[float] = None
        self.last_output_source_stamp: Dict[str, Optional[float]] = {self.metric_source: None, ORB: None}
        self.last_twist = Twist()
        self.path = Path()
        self.path.header.frame_id = self.map_frame

        self.odom_pub = rospy.Publisher(self.output_odom_topic, Odometry, queue_size=100)
        self.pose_pub = rospy.Publisher(self.output_pose_topic, PoseStamped, queue_size=100)
        self.path_pub = rospy.Publisher(self.output_path_topic, Path, queue_size=5, latch=True)
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
        rospy.Timer(rospy.Duration(1.0 / max(self.publish_rate_hz, 1.0)), self.timer_cb)
        self.prepare_event_log()
        self.publish_event("startup", FAILED, FAILED, "fusion_node_started", 0.0)
        rospy.loginfo("[Fusion] primary=%s metric=%s metric_topic=%s orb=%s tf_mode=%s",
                      self.primary, self.metric_source, self.metric_topic, self.orb_topic, self.tf_mode)

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

    def health_cb(self, source: str, msg: String) -> None:
        try:
            status = json.loads(msg.data)
        except Exception as exc:
            rospy.logwarn_throttle(2.0, "[Fusion] invalid %s health JSON: %s", source, exc)
            return
        with self.lock:
            self.sources[source].update_health(status, time.monotonic())

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
            self.update_cross_alignment(source)

    def nearest_sample(self, data: SourceData, stamp: float) -> Optional[Tuple[float, np.ndarray]]:
        if not data.buffer:
            return None
        candidate = min(data.buffer, key=lambda item: abs(item[0] - stamp))
        return candidate if abs(candidate[0] - stamp) <= self.sync_slop else None

    def metric_source_pose(self, source: str, source_T: np.ndarray) -> np.ndarray:
        if source == self.metric_source:
            return source_T.copy()
        if self.cross_fast_from_orb is not None and self.orb_metric_scale is not None:
            return apply_camera_to_base_similarity(
                self.cross_fast_from_orb, self.orb_metric_scale,
                self.orb_camera_to_base, source_T
            )
        # This branch is disabled by default. It exists only for a user-supplied
        # fixed scale/explicit override, and continuity alignment is still applied.
        fallback_alignment = np.eye(4)
        return apply_camera_to_base_similarity(
            fallback_alignment, self.source_scale[ORB], self.orb_camera_to_base, source_T
        )

    def update_cross_alignment(self, source: str) -> None:
        current = self.sources[source]
        other_name = ORB if source == self.metric_source else self.metric_source
        other = self.sources[other_name]
        if current.latest_stamp is None or current.latest_T is None:
            return
        match = self.nearest_sample(other, current.latest_stamp)
        if match is None:
            return
        if source == self.metric_source:
            metric_stamp, orb_stamp = current.latest_stamp, match[0]
            T_metric, T_orb = current.latest_T.copy(), match[1].copy()
        else:
            metric_stamp, orb_stamp = match[0], current.latest_stamp
            T_metric, T_orb = match[1].copy(), current.latest_T.copy()
        pair_key = (metric_stamp, orb_stamp)
        if self.last_pair_key == pair_key:
            return
        self.last_pair_key = pair_key
        # Never learn scale/alignment from an estimator already declared unhealthy.
        if not all(bool(self.sources[name].health.get("healthy", False)) for name in (self.metric_source, ORB)):
            return
        # Keep the accepted monocular similarity fixed while ORB is the active
        # fallback. Re-estimating scale under the active trajectory would move
        # the output even without a source switch. Existing alignment is still
        # used below for recovery consistency checks.
        if self.active_source == ORB:
            self.update_disagreement(T_metric, T_orb)
            return
        self.synchronized_pairs.append((T_metric, T_orb))
        minimum = 1 if self.orb_fixed_scale > 0.0 else self.min_alignment_pairs
        if len(self.synchronized_pairs) >= minimum:
            try:
                alignment, scale, position_rmse, orientation_rmse = estimate_camera_to_base_similarity(
                    list(self.synchronized_pairs), self.orb_camera_to_base, self.orb_fixed_scale
                )
                scale_ok = self.scale_ratio_min <= scale <= self.scale_ratio_max
                quality_ok = (position_rmse <= self.max_alignment_rmse and
                              orientation_rmse <= self.max_alignment_orientation_rmse)
                self.alignment_quality = {
                    "position_rmse_m": position_rmse,
                    "orientation_rmse_rad": orientation_rmse,
                }
                if scale_ok and quality_ok:
                    self.cross_fast_from_orb = alignment
                    self.orb_metric_scale = scale
                    self.source_scale[ORB] = scale
                else:
                    rospy.logwarn_throttle(2.0,
                        "[Fusion] rejected ORB alignment scale=%.3f pos_rmse=%.3f rot_rmse=%.1fdeg",
                        scale, position_rmse, math.degrees(orientation_rmse))
            except ValueError as exc:
                rospy.logwarn_throttle(2.0, "[Fusion] camera/base alignment not ready: %s", exc)
        self.update_disagreement(T_metric, T_orb)

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

    def invalidate_orb_alignment(self, reason: str) -> None:
        """Require fresh healthy overlap after ORB tracking/map continuity is lost."""
        if self.cross_fast_from_orb is None and self.orb_fixed_scale <= 0.0:
            return
        self.synchronized_pairs.clear()
        self.last_pair_key = None
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
        if not self.disagreement.get("valid"):
            return False
        max_pos = self.recovery_disagreement_m if recovery else self.max_disagreement_m
        max_ang = self.recovery_disagreement_rad if recovery else self.max_disagreement_rad
        scale = self.disagreement.get("scale_ratio")
        scale_ok = scale is None or self.scale_ratio_min <= scale <= self.scale_ratio_max
        return (self.disagreement["position_m"] <= max_pos and
                self.disagreement["orientation_rad"] <= max_ang and scale_ok)

    def source_failure_persisted(self, source: str, now: float) -> bool:
        data = self.sources[source]
        return (not bool(data.health.get("healthy", False)) and data.unhealthy_since is not None and
                now - data.unhealthy_since >= self.failure_hold)

    def choose_initial_source(self, now: float) -> Optional[str]:
        if self.source_usable(self.primary, now, self.recovery_stabilization):
            return self.primary
        if self.source_usable(self.secondary, now, self.recovery_stabilization):
            return self.secondary
        return None

    def evaluate_state_machine(self, now: float) -> None:
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

        if self.active_source == FAILED:
            selected = self.choose_initial_source(now)
            if selected:
                self.switch_to(selected, "initial_healthy_source")
            else:
                self.state = "FAILED_BOTH_UNHEALTHY"
            return

        active = self.active_source
        backup = ORB if active == self.metric_source else self.metric_source
        if self.source_failure_persisted(active, now):
            if self.source_usable(backup, now, self.recovery_stabilization):
                reasons = ",".join(self.sources[active].health.get("reasons", ["unhealthy"]))
                self.switch_to(backup, f"active_unhealthy:{reasons}")
            else:
                old = self.active_source
                self.active_source = FAILED
                self.state = "FAILED_BOTH_UNHEALTHY"
                self.nav_ok_pub.publish(Bool(data=False))
                self.publish_event("failure", old, FAILED, "both_estimators_unhealthy", 0.0)
            return

        if active == self.secondary:
            primary_ready = self.source_usable(self.primary, now, self.primary_recovery)
            dwell_ok = now - self.last_switch_wall >= self.minimum_dwell
            if primary_ready and dwell_ok and self.consistency_ok(recovery=True):
                self.switch_to(self.primary, "primary_recovered_and_consistent")
                return

        if active == self.metric_source:
            self.state = f"PRIMARY_{self.metric_source.upper()}"
        else:
            self.state = "BACKUP_ORB_SLAM3"
        if all(bool(self.sources[s].health.get("healthy", False)) for s in (self.metric_source, ORB)) and not self.consistency_ok():
            self.state += "_DEGRADED_DISAGREEMENT"

    def switch_to(self, new_source: str, reason: str) -> None:
        data = self.sources[new_source]
        if data.latest_T is None:
            return
        old = self.active_source
        before = self.last_output_T.copy() if self.last_output_T is not None else None
        if new_source == ORB and self.orb_metric_scale is not None:
            self.source_scale[ORB] = self.orb_metric_scale
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
        self.state = f"PRIMARY_{self.metric_source.upper()}" if new_source == self.metric_source else "BACKUP_ORB_SLAM3"
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
        T_target = self.source_to_output[self.active_source] @ self.metric_source_pose(
            self.active_source, data.latest_T
        )
        T_out = T_target
        if self.switch_anchor_T is not None and self.switch_start_wall is not None and self.blend_duration > 0.0:
            alpha = (now - self.switch_start_wall) / self.blend_duration
            if alpha < 1.0:
                T_out = interpolate_transform(self.switch_anchor_T, T_target, alpha)
            else:
                self.switch_anchor_T = None
                self.switch_start_wall = None
        return data.latest_msg, T_out

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

    def publish_tf_for_pose(self, T_map_base: np.ndarray, stamp: rospy.Time) -> None:
        if not self.publish_tf or self.tf_broadcaster is None:
            return
        if self.tf_mode == "direct":
            msg = TransformStamped()
            msg.header.stamp = stamp
            msg.header.frame_id = self.odom_frame
            msg.child_frame_id = self.base_frame
            msg.transform.translation.x, msg.transform.translation.y, msg.transform.translation.z = map(float, T_map_base[:3, 3])
            msg.transform.rotation = matrix_to_pose(T_map_base).orientation
            self.tf_broadcaster.sendTransform(msg)
        elif self.tf_mode == "map_to_odom":
            try:
                tf = self.tf_buffer.lookup_transform(self.odom_frame, self.base_frame, stamp, rospy.Duration(0.05))
                odom_pose = PoseStamped()
                odom_pose.pose.position.x = tf.transform.translation.x
                odom_pose.pose.position.y = tf.transform.translation.y
                odom_pose.pose.position.z = tf.transform.translation.z
                odom_pose.pose.orientation = tf.transform.rotation
                T_odom_base = pose_to_matrix(odom_pose.pose)
                T_map_odom = T_map_base @ invert_transform(T_odom_base)
                msg = TransformStamped()
                msg.header.stamp = stamp
                msg.header.frame_id = self.map_frame
                msg.child_frame_id = self.odom_frame
                msg.transform.translation.x, msg.transform.translation.y, msg.transform.translation.z = map(float, T_map_odom[:3, 3])
                msg.transform.rotation = matrix_to_pose(T_map_odom).orientation
                self.tf_broadcaster.sendTransform(msg)
            except Exception as exc:
                rospy.logwarn_throttle(2.0, "[Fusion] cannot publish map->odom: %s", exc)

    def publish_output(self, source_msg: Odometry, T: np.ndarray) -> None:
        stamp_value = source_msg.header.stamp.to_sec()
        if self.last_output_stamp is not None and stamp_value <= self.last_output_stamp:
            return
        if self.last_output_stamp is not None and stamp_value - self.last_output_stamp > self.max_output_gap:
            self.publish_event("output_gap", self.active_source, self.active_source,
                               f"gap_sec={stamp_value - self.last_output_stamp:.3f}", 0.0)
        pose = matrix_to_pose(T)
        if self.pending_switch_event is not None and self.last_output_T is not None:
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

        ps = PoseStamped()
        ps.header.stamp = odom.header.stamp
        ps.header.frame_id = self.map_frame
        ps.pose = pose
        self.pose_pub.publish(ps)
        self.path.header.stamp = odom.header.stamp
        self.path.poses.append(ps)
        if len(self.path.poses) > self.max_path_poses:
            self.path.poses = self.path.poses[-self.max_path_poses:]
        self.path_pub.publish(self.path)
        self.publish_tf_for_pose(T, odom.header.stamp)

        self.last_output_T = T.copy()
        self.last_output_stamp = stamp_value
        self.last_output_wall = time.monotonic()
        self.last_output_source_stamp[self.active_source] = stamp_value

    def status_payload(self) -> dict:
        return {
            "stamp": rospy.Time.now().to_sec(),
            "state": self.state,
            "valid": self.active_source != FAILED and bool(self.sources[self.active_source].health.get("healthy", False)),
            "active_source": self.active_source,
            "primary_source": self.primary,
            "metric_source": self.metric_source,
            "switch_count": self.switch_count,
            "tf_mode": self.tf_mode,
            "frames": {"map": self.map_frame, "odom": self.odom_frame, "base": self.base_frame},
            "health": {name: data.health for name, data in self.sources.items()},
            "orb_metric_scale_ready": self.orb_metric_scale is not None and self.cross_fast_from_orb is not None,
            "orb_metric_scale": self.orb_metric_scale,
            "alignment_quality": {
                "position_rmse_m": self.alignment_quality.get("position_rmse_m"),
                "orientation_rmse_deg": None if self.alignment_quality.get("orientation_rmse_rad") is None else math.degrees(self.alignment_quality["orientation_rmse_rad"]),
            },
            "disagreement": {
                "position_m": self.disagreement.get("position_m"),
                "orientation_deg": None if self.disagreement.get("orientation_rad") is None else math.degrees(self.disagreement["orientation_rad"]),
                f"scale_ratio_{self.metric_source}_over_orb": self.disagreement.get("scale_ratio"),
                "consistent": self.consistency_ok() if self.disagreement.get("valid") else False,
            },
        }

    def timer_cb(self, _event) -> None:
        with self.lock:
            now = time.monotonic()
            self.evaluate_state_machine(now)
            active = self.transformed_active_pose(now)
            if active is not None and bool(self.sources[self.active_source].health.get("healthy", False)):
                self.publish_output(active[0], active[1])
            navigation_ok = self.active_source != FAILED and bool(self.sources[self.active_source].health.get("healthy", False))
            if self.stop_navigation_on_failure:
                self.nav_ok_pub.publish(Bool(data=navigation_ok))
            else:
                self.nav_ok_pub.publish(Bool(data=True))
            self.active_pub.publish(String(data=self.active_source))
            self.status_pub.publish(String(data=json.dumps(self.status_payload(), sort_keys=True)))


def main() -> None:
    rospy.init_node("e2o_localization_fusion")
    LocalizationFusion()
    rospy.spin()


if __name__ == "__main__":
    main()
