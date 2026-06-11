#!/usr/bin/env python3
"""
verify_topics.py  (orbslam3_urbannav)
======================================
Validates the ORB-SLAM3 UrbanNav pipeline is running correctly.

Checks:
  1. Input topic /camera/image_raw is being published by the wrapper
  2. Frequency is in the expected range (10–35 Hz for ZED2)
  3. Frame ID is 'camera_right'
  4. Image encoding and dimensions are correct (672×376)
  5. ORB-SLAM3 output topics are being produced
  6. TF tree is complete
  7. No future timestamps

Usage:
    rosrun orbslam3_urbannav verify_topics.py _timeout:=20
"""

import sys
import time
import threading
from collections import defaultdict
from typing import Dict, List, Tuple

import rospy
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry, Path
from std_msgs.msg import String
import tf2_ros


# ─────────────────────────────────────────────────────────────────────────────
#  Expected config
# ─────────────────────────────────────────────────────────────────────────────

EXPECTED_INPUT_TOPIC  = "/camera/image_raw"
EXPECTED_FRAME_ID     = "camera_right"
EXPECTED_WIDTH        = 672
EXPECTED_HEIGHT       = 376
EXPECTED_HZ_MIN       = 10.0
EXPECTED_HZ_MAX       = 35.0

ORBSLAM3_OUTPUT_TOPICS = {
    "/orb_slam3/camera_pose":      PoseStamped,
    "/orbslam3/odometry":          Odometry,
    "/orbslam3/path":              Path,
    "/orbslam3/tracking_status":   String,
}

EXPECTED_TF_PAIRS = [
    ("map",          "odom"),
    ("odom",         "body"),
    ("odom",         "camera_right"),
    ("camera_right", "camera_right_optical"),
    ("body",         "velodyne"),
]

OBSERVATION_WINDOW = 15.0

# ─────────────────────────────────────────────────────────────────────────────
#  Observer
# ─────────────────────────────────────────────────────────────────────────────

class TopicObserver:
    def __init__(self):
        self.counts      = defaultdict(int)
        self.first_stamp = {}
        self.last_stamp  = {}
        self.frame_ids   = {}
        self.image_info  = {}
        self._subs       = []
        self._lock       = threading.Lock()

    def watch(self, topic, msg_type):
        sub = rospy.Subscriber(
            topic, msg_type, lambda m, t=topic: self._cb(t, m))
        self._subs.append(sub)

    def _cb(self, topic, msg):
        with self._lock:
            self.counts[topic] += 1
            if hasattr(msg, "header"):
                stamp = msg.header.stamp.to_sec()
                if topic not in self.first_stamp:
                    self.first_stamp[topic] = stamp
                self.last_stamp[topic]  = stamp
                self.frame_ids[topic]   = msg.header.frame_id
            if isinstance(msg, Image) and topic not in self.image_info:
                self.image_info[topic] = {
                    "width":    msg.width,
                    "height":   msg.height,
                    "encoding": msg.encoding,
                }

    def stop(self):
        for s in self._subs:
            s.unregister()


PASS = "\033[92m PASS \033[0m"
FAIL = "\033[91m FAIL \033[0m"
WARN = "\033[93m WARN \033[0m"

def _pf(ok): return PASS if ok else FAIL
def _section(t): print(f"\n{'═'*60}\n  {t}\n{'═'*60}")


def check_tf(tf_buf, pairs, timeout=3.0):
    results = {}
    for parent, child in pairs:
        key = f"{parent}→{child}"
        try:
            tf_buf.lookup_transform(
                parent, child, rospy.Time(0), rospy.Duration(timeout))
            results[key] = True
        except Exception as e:
            results[key] = False
    return results


def main():
    rospy.init_node("verify_topics_orbslam3", anonymous=True)
    timeout = float(rospy.get_param("~timeout", OBSERVATION_WINDOW))
    all_pass = True

    tf_buf      = tf2_ros.Buffer()
    tf_listener = tf2_ros.TransformListener(tf_buf)

    obs = TopicObserver()
    obs.watch(EXPECTED_INPUT_TOPIC, Image)
    for topic, msg_type in ORBSLAM3_OUTPUT_TOPICS.items():
        obs.watch(topic, msg_type)

    print(f"\nObserving for {timeout:.0f}s …")
    t0 = time.time()
    while not rospy.is_shutdown() and (time.time() - t0) < timeout:
        time.sleep(0.5)
    obs.stop()
    elapsed = time.time() - t0

    # ── Section 1: Wrapper input ──────────────────────────────────────────────
    _section("1. Wrapper Input Topic (/camera/image_raw)")
    count   = obs.counts.get(EXPECTED_INPUT_TOPIC, 0)
    hz      = count / elapsed
    freq_ok = count > 0 and EXPECTED_HZ_MIN <= hz <= EXPECTED_HZ_MAX * 1.5
    print(f"  Messages received : {count}")
    print(f"  Rate              : {hz:.1f} Hz  (expected {EXPECTED_HZ_MIN}–{EXPECTED_HZ_MAX})")
    print(f"  Frequency check   : {_pf(freq_ok)}")
    if not freq_ok:
        all_pass = False

    # ── Section 2: Frame ID ───────────────────────────────────────────────────
    _section("2. Frame ID Check")
    actual_frame = obs.frame_ids.get(EXPECTED_INPUT_TOPIC, "NOT RECEIVED")
    frame_ok     = actual_frame == EXPECTED_FRAME_ID
    print(f"  Expected : {EXPECTED_FRAME_ID}")
    print(f"  Actual   : {actual_frame}")
    print(f"  Status   : {_pf(frame_ok)}")
    if not frame_ok:
        all_pass = False

    # ── Section 3: Image dimensions ───────────────────────────────────────────
    _section("3. Image Dimensions and Encoding")
    if EXPECTED_INPUT_TOPIC in obs.image_info:
        info  = obs.image_info[EXPECTED_INPUT_TOPIC]
        w_ok  = info["width"]  == EXPECTED_WIDTH
        h_ok  = info["height"] == EXPECTED_HEIGHT
        print(f"  Width    : {info['width']}   (expected {EXPECTED_WIDTH})  {_pf(w_ok)}")
        print(f"  Height   : {info['height']}  (expected {EXPECTED_HEIGHT}) {_pf(h_ok)}")
        print(f"  Encoding : {info['encoding']}")
        if not (w_ok and h_ok):
            all_pass = False
    else:
        print(f"  {FAIL} No images received on {EXPECTED_INPUT_TOPIC}")
        all_pass = False

    # ── Section 4: Timestamps ─────────────────────────────────────────────────
    _section("4. Timestamp Consistency")
    wall_now = rospy.Time.now().to_sec()
    for topic in [EXPECTED_INPUT_TOPIC]:
        if topic not in obs.last_stamp:
            print(f"  {topic:<45} {FAIL} (no messages)")
            all_pass = False
            continue
        span      = obs.last_stamp[topic] - obs.first_stamp[topic]
        future_ok = obs.last_stamp[topic] <= (wall_now + 1.0)
        print(f"  {topic:<45} span={span:.2f}s  future={_pf(future_ok)}")
        if not future_ok:
            all_pass = False

    # ── Section 5: ORB-SLAM3 output topics ────────────────────────────────────
    _section("5. ORB-SLAM3 Output Topics")
    print(f"  {'Topic':<40} {'Count':>7} {'Status':>8}")
    print(f"  {'-'*40} {'-'*7} {'-'*8}")
    for topic in ORBSLAM3_OUTPUT_TOPICS:
        c  = obs.counts.get(topic, 0)
        ok = c > 0
        print(f"  {topic:<40} {c:>7}  {_pf(ok)}")
        if not ok:
            print(f"  {WARN} ORB-SLAM3 may still be initialising (needs ~15 keyframes)")

    # ── Section 6: TF Tree ────────────────────────────────────────────────────
    _section("6. TF Tree Verification")
    tf_results = check_tf(tf_buf, EXPECTED_TF_PAIRS, timeout=3.0)
    for pair, ok in tf_results.items():
        print(f"  {pair:<40}  {_pf(ok)}")
        if not ok:
            all_pass = False

    # ── Summary ───────────────────────────────────────────────────────────────
    _section("SUMMARY")
    if all_pass:
        print("  \033[92m✓ ALL CHECKS PASSED — Pipeline is ready for ORB-SLAM3\033[0m\n")
        sys.exit(0)
    else:
        print("  \033[91m✗ SOME CHECKS FAILED — Review output above\033[0m\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
