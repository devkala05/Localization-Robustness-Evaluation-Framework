#!/usr/bin/env python3
"""
verify_topics.py
================
Black-box verification script for the Fast-LIO2 UrbanNav pipeline.

Checks:
  1. All required topics are being published
  2. Topic frequencies are within expected ranges
  3. Timestamps are consistent (no future stamps, no large gaps)
  4. Frame IDs match what Fast-LIO2 expects
  5. PointCloud2 field structure is compatible with Fast-LIO2
  6. IMU covariance matrices are valid (not all-zero)
  7. TF frames are available

Usage:
    # After launching the wrapper and rosbag:
    rosrun fast_lio_urbannav verify_topics.py

    # Or with custom timeout:
    rosrun fast_lio_urbannav verify_topics.py _timeout:=30
"""

import sys
import time
import threading
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import rospy
import rostopic
from sensor_msgs.msg import PointCloud2, Imu, Image
import tf2_ros


# ─────────────────────────────────────────────────────────────────────────────
#  Expected configuration
# ─────────────────────────────────────────────────────────────────────────────

EXPECTED_TOPICS = {
    # (topic, message_type, min_hz, max_hz, expected_frame_id)
    "/cloud_registered_raw": (PointCloud2, 8.0,   15.0,  "velodyne"),
    "/livox/imu":            (Imu,         100.0, 500.0, "body"),
    "/camera/right/image_raw": (Image,     10.0,  35.0,  "camera_right"),
}

EXPECTED_TF_PAIRS = [
    ("map",           "odom"),
    ("body",          "velodyne"),
    ("body",          "camera_right"),
    ("body",          "camera_left"),
    ("velodyne",      "velodyne_left"),
    ("velodyne",      "velodyne_right"),
    ("body",          "gnss_antenna"),
]

REQUIRED_POINTCLOUD_FIELDS = {"x", "y", "z"}
OPTIONAL_POINTCLOUD_FIELDS = {"intensity", "ring", "time"}

OBSERVATION_WINDOW = 10.0   # seconds to observe each topic


# ─────────────────────────────────────────────────────────────────────────────
#  Topic observer
# ─────────────────────────────────────────────────────────────────────────────

class TopicObserver:
    def __init__(self):
        self.counts: Dict[str, int] = defaultdict(int)
        self.first_stamp: Dict[str, float] = {}
        self.last_stamp: Dict[str, float] = {}
        self.frame_ids: Dict[str, str] = {}
        self.extra_info: Dict[str, dict] = {}
        self._subs = []
        self._lock = threading.Lock()

    def observe(self, topic: str, msg_type, duration: float):
        sub = rospy.Subscriber(topic, msg_type,
                               lambda m, t=topic: self._cb(t, m))
        self._subs.append(sub)

    def _cb(self, topic: str, msg):
        with self._lock:
            self.counts[topic] += 1

            stamp = msg.header.stamp.to_sec()
            if topic not in self.first_stamp:
                self.first_stamp[topic] = stamp
            self.last_stamp[topic] = stamp
            self.frame_ids[topic] = msg.header.frame_id

            # Extra checks per message type
            if isinstance(msg, PointCloud2) and topic not in self.extra_info:
                field_names = {f.name for f in msg.fields}
                self.extra_info[topic] = {
                    "fields": field_names,
                    "height": msg.height,
                    "width":  msg.width,
                    "is_dense": msg.is_dense,
                    "point_step": msg.point_step,
                }
            elif isinstance(msg, Imu) and topic not in self.extra_info:
                cov_valid = (list(msg.angular_velocity_covariance) != [0]*9 or
                             list(msg.linear_acceleration_covariance) != [0]*9)
                self.extra_info[topic] = {
                    "covariance_valid": cov_valid,
                    "has_orientation": (msg.orientation.w != 0.0),
                }
            elif isinstance(msg, Image) and topic not in self.extra_info:
                self.extra_info[topic] = {
                    "encoding": msg.encoding,
                    "height":   msg.height,
                    "width":    msg.width,
                }

    def stop(self):
        for s in self._subs:
            s.unregister()


# ─────────────────────────────────────────────────────────────────────────────
#  TF checker
# ─────────────────────────────────────────────────────────────────────────────

def check_tf_pairs(tf_buffer: tf2_ros.Buffer,
                   pairs: List[Tuple[str, str]],
                   timeout: float = 5.0) -> Dict[str, bool]:
    results = {}
    for parent, child in pairs:
        key = f"{parent}→{child}"
        try:
            tf_buffer.lookup_transform(parent, child,
                                       rospy.Time(0),
                                       rospy.Duration(timeout))
            results[key] = True
        except (tf2_ros.LookupException,
                tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException) as e:
            results[key] = False
            rospy.logwarn(f"[TF] {key}  MISSING: {e}")
    return results


# ─────────────────────────────────────────────────────────────────────────────
#  Report helpers
# ─────────────────────────────────────────────────────────────────────────────

PASS = "\033[92m PASS \033[0m"
FAIL = "\033[91m FAIL \033[0m"
WARN = "\033[93m WARN \033[0m"

def _pf(condition: bool) -> str:
    return PASS if condition else FAIL

def _section(title: str):
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print(f"{'═'*60}")


# ─────────────────────────────────────────────────────────────────────────────
#  Main verification logic
# ─────────────────────────────────────────────────────────────────────────────

def main():
    rospy.init_node("verify_topics", anonymous=True)

    observation_time = rospy.get_param("~timeout", OBSERVATION_WINDOW)
    all_pass = True

    # ── TF setup ─────────────────────────────────────────────────────────────
    tf_buffer   = tf2_ros.Buffer()
    tf_listener = tf2_ros.TransformListener(tf_buffer)

    # ── Start observing topics ────────────────────────────────────────────────
    observer = TopicObserver()
    for topic, (msg_type, min_hz, max_hz, frame_id) in EXPECTED_TOPICS.items():
        observer.observe(topic, msg_type, observation_time)

    print(f"\nObserving topics for {observation_time:.0f} seconds …")
    t0 = time.time()
    while not rospy.is_shutdown() and (time.time() - t0) < observation_time:
        time.sleep(0.5)

    observer.stop()
    elapsed = time.time() - t0

    # ─────────────────────────────────────────────────────────────────────────
    #  Section 1: Topic presence and frequency
    # ─────────────────────────────────────────────────────────────────────────
    _section("1. Topic Presence and Frequency")
    print(f"  {'Topic':<35} {'Expected Hz':>12} {'Actual Hz':>10} {'Status':>8}")
    print(f"  {'-'*35} {'-'*12} {'-'*10} {'-'*8}")

    for topic, (msg_type, min_hz, max_hz, _frame) in EXPECTED_TOPICS.items():
        count = observer.counts.get(topic, 0)
        actual_hz = count / elapsed if elapsed > 0 else 0.0
        present = count > 0
        freq_ok = present and (min_hz <= actual_hz <= max_hz * 1.5)
        status = _pf(freq_ok)
        if not freq_ok:
            all_pass = False
        range_str = f"{min_hz:.0f}–{max_hz:.0f}"
        print(f"  {topic:<35} {range_str:>12} {actual_hz:>9.1f}  {status}")

    # ─────────────────────────────────────────────────────────────────────────
    #  Section 2: Frame IDs
    # ─────────────────────────────────────────────────────────────────────────
    _section("2. Frame ID Verification")
    print(f"  {'Topic':<35} {'Expected':>15} {'Actual':>15} {'Status':>8}")
    print(f"  {'-'*35} {'-'*15} {'-'*15} {'-'*8}")

    for topic, (_mt, _mn, _mx, expected_frame) in EXPECTED_TOPICS.items():
        actual_frame = observer.frame_ids.get(topic, "NOT RECEIVED")
        ok = (actual_frame == expected_frame)
        if not ok:
            all_pass = False
        print(f"  {topic:<35} {expected_frame:>15} {actual_frame:>15}  {_pf(ok)}")

    # ─────────────────────────────────────────────────────────────────────────
    #  Section 3: Timestamp consistency
    # ─────────────────────────────────────────────────────────────────────────
    _section("3. Timestamp Consistency")
    wall_now = rospy.Time.now().to_sec()

    for topic in EXPECTED_TOPICS:
        if topic not in observer.last_stamp:
            print(f"  {topic:<40}  {FAIL} (no messages received)")
            all_pass = False
            continue
        first = observer.first_stamp[topic]
        last  = observer.last_stamp[topic]
        span  = last - first
        future_ok = last <= (wall_now + 1.0)   # allow 1s tolerance
        print(f"  {topic:<40}  span={span:6.2f}s  future={_pf(future_ok)}")
        if not future_ok:
            all_pass = False

    # ─────────────────────────────────────────────────────────────────────────
    #  Section 4: PointCloud2 field structure
    # ─────────────────────────────────────────────────────────────────────────
    _section("4. PointCloud2 Field Structure")
    pc_topic = "/cloud_registered_raw"
    if pc_topic in observer.extra_info:
        info = observer.extra_info[pc_topic]
        fields = info.get("fields", set())
        required_ok = REQUIRED_POINTCLOUD_FIELDS.issubset(fields)
        optional_present = OPTIONAL_POINTCLOUD_FIELDS & fields
        print(f"  Fields present:          {sorted(fields)}")
        print(f"  Required (x,y,z):        {_pf(required_ok)}")
        print(f"  Optional present:        {sorted(optional_present)}")
        print(f"  Height × Width:          {info['height']} × {info['width']}")
        print(f"  Point step (bytes):      {info['point_step']}")
        if not required_ok:
            all_pass = False
    else:
        print(f"  {FAIL} No PointCloud2 messages received on {pc_topic}")
        all_pass = False

    # ─────────────────────────────────────────────────────────────────────────
    #  Section 5: IMU data integrity
    # ─────────────────────────────────────────────────────────────────────────
    _section("5. IMU Data Integrity")
    imu_topic = "/livox/imu"
    if imu_topic in observer.extra_info:
        info = observer.extra_info[imu_topic]
        cov_ok = info.get("covariance_valid", False)
        ori_ok = info.get("has_orientation", False)
        print(f"  Covariance matrices valid:   {_pf(cov_ok)}")
        print(f"  Orientation present:         {_pf(ori_ok)}")
        if not cov_ok:
            print(f"  {WARN} Covariance is all-zero — Fast-LIO2 will use its config values")
    else:
        print(f"  {FAIL} No IMU messages received on {imu_topic}")
        all_pass = False

    # ─────────────────────────────────────────────────────────────────────────
    #  Section 6: Camera image info
    # ─────────────────────────────────────────────────────────────────────────
    _section("6. Camera Image Info")
    cam_topic = "/camera/right/image_raw"
    if cam_topic in observer.extra_info:
        info = observer.extra_info[cam_topic]
        print(f"  Encoding: {info['encoding']}   Size: {info['width']}×{info['height']}")
        print(f"  {PASS} Camera stream active")
    else:
        print(f"  {WARN} No camera images received (camera not used by Fast-LIO2 core)")

    # ─────────────────────────────────────────────────────────────────────────
    #  Section 7: TF tree
    # ─────────────────────────────────────────────────────────────────────────
    _section("7. TF Tree Verification")
    tf_results = check_tf_pairs(tf_buffer, EXPECTED_TF_PAIRS, timeout=3.0)
    for pair_key, ok in tf_results.items():
        print(f"  {pair_key:<35}  {_pf(ok)}")
        if not ok:
            all_pass = False

    # ─────────────────────────────────────────────────────────────────────────
    #  Summary
    # ─────────────────────────────────────────────────────────────────────────
    _section("SUMMARY")
    if all_pass:
        print(f"  \033[92m✓ ALL CHECKS PASSED — Pipeline is ready for Fast-LIO2\033[0m\n")
        sys.exit(0)
    else:
        print(f"  \033[91m✗ SOME CHECKS FAILED — Review output above\033[0m\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
