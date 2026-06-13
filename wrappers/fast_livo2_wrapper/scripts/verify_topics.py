#!/usr/bin/env python3
"""
verify_topics.py
================
Diagnostic tool: verifies that all expected topics are publishing at
reasonable rates before and during FAST-LIVO2 execution.

Checks
──────
  Input streams (UrbanNav rosbag → wrapper):
    /velodyne_points                  ≥ 5 Hz   (VLP-16 at 10 Hz)
    /imu/data                         ≥ 50 Hz  (Xsens at 200 Hz)
    /zed2/camera/right/image_raw      ≥ 5 Hz   (ZED2 at ~10 Hz)

  Bridge outputs (wrapper → FAST-LIVO2):
    /livox/lidar                      ≥ 5 Hz
    /livox/imu                        ≥ 50 Hz
    /camera/right/image_raw           ≥ 5 Hz

  FAST-LIVO2 outputs (algorithm → downstream):
    /path                             ≥ 1 Hz   (full trajectory)
    /Odometry                         ≥ 5 Hz   (current pose + velocity)
    /cloud_registered                 ≥ 1 Hz   (map cloud in world frame)
    /cloud_registered_body            ≥ 1 Hz   (map cloud in body frame)

Usage:
  rosrun fast_livo2_wrapper verify_topics.py
  rosrun fast_livo2_wrapper verify_topics.py _timeout:=30.0 _sample_period:=2.0
"""

import time
import threading
import rospy

from sensor_msgs.msg import PointCloud2, Imu, Image
from nav_msgs.msg   import Odometry, Path


# ─── Expected topics and minimum acceptable rates ─────────────────────────────

CHECKS = [
    # (topic, message_type, min_hz, description)
    # ── UrbanNav bag → wrapper (input streams) ─────────────────────────────────
    ("/velodyne_points",              PointCloud2,  5.0,  "Bag  → LiDAR input (VLP-16 10 Hz)"),
    ("/imu/data",                     Imu,         50.0,  "Bag  → IMU input (Xsens 200 Hz)"),
    ("/zed2/camera/right/image_raw",  Image,        5.0,  "Bag  → Camera input (ZED2 ~10 Hz)"),
    # ── Wrapper → FAST-LIVO2 (bridge outputs) ─────────────────────────────────
    ("/livox/lidar",                  PointCloud2,  5.0,  "Bridge → FAST-LIVO2 LiDAR"),
    ("/livox/imu",                    Imu,         50.0,  "Bridge → FAST-LIVO2 IMU"),
    ("/camera/right/image_raw",       Image,        5.0,  "Bridge → FAST-LIVO2 camera"),
    # ── FAST-LIVO2 outputs ────────────────────────────────────────────────────
    ("/path",                         Path,         1.0,  "FAST-LIVO2 → trajectory path"),
    ("/Odometry",                     Odometry,     5.0,  "FAST-LIVO2 → odometry"),
    ("/cloud_registered",             PointCloud2,  1.0,  "FAST-LIVO2 → map cloud (world)"),
    ("/cloud_registered_body",        PointCloud2,  1.0,  "FAST-LIVO2 → map cloud (body)"),
]


class TopicMonitor:
    """Counts messages received on a single topic over a sliding window."""

    def __init__(self, topic: str, msg_type, window: float = 2.0):
        self.topic     = topic
        self.window    = window
        self._lock     = threading.Lock()
        self._times    = []
        self._total    = 0
        self._sub      = rospy.Subscriber(topic, msg_type, self._cb, queue_size=10)

    def _cb(self, _msg):
        now = time.monotonic()
        with self._lock:
            self._times.append(now)
            self._total += 1
            cutoff = now - self.window
            self._times = [t for t in self._times if t >= cutoff]

    def hz(self) -> float:
        now = time.monotonic()
        with self._lock:
            recent = [t for t in self._times if t >= now - self.window]
        if len(recent) < 2:
            return 0.0
        span = recent[-1] - recent[0]
        return (len(recent) - 1) / span if span > 0 else 0.0

    def total(self) -> int:
        with self._lock:
            return self._total


def run_verification(timeout: float = 20.0, sample_period: float = 2.0):
    """
    Monitor all topics for ``timeout`` seconds and print a summary table.
    Returns True if all checks pass, False otherwise.
    """
    monitors = {}
    for topic, msg_type, _min_hz, _desc in CHECKS:
        monitors[topic] = TopicMonitor(topic, msg_type, window=sample_period)

    rospy.loginfo("[Verify] Monitoring %d topics for %.0f s …", len(CHECKS), timeout)

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and not rospy.is_shutdown():
        time.sleep(sample_period)
        _print_table(CHECKS, monitors)

    return _final_report(CHECKS, monitors)


def _print_table(checks, monitors):
    header = (
        f"\n{'Topic':<45} {'Min Hz':>7} {'Actual Hz':>10} {'Total':>8} {'Status':>8}"
        "\n" + "─" * 84
    )
    lines = [header]
    for topic, _t, min_hz, desc in checks:
        mon    = monitors[topic]
        hz     = mon.hz()
        total  = mon.total()
        status = "✓ OK" if hz >= min_hz else ("⚠ LOW" if hz > 0 else "✗ NONE")
        lines.append(
            f"{topic:<45} {min_hz:>7.1f} {hz:>10.1f} {total:>8d} {status:>8}  [{desc}]"
        )
    rospy.loginfo("\n".join(lines))


def _final_report(checks, monitors) -> bool:
    all_ok = True
    rospy.loginfo("\n══════════════════════ FINAL VERIFICATION REPORT ══════════════════════")
    for topic, _t, min_hz, desc in checks:
        mon    = monitors[topic]
        hz     = mon.hz()
        total  = mon.total()
        passed = hz >= min_hz
        if not passed:
            all_ok = False
        mark = "PASS" if passed else "FAIL"
        rospy.loginfo(
            "  [%s] %-45s %6.1f Hz  (need %5.1f)  total=%d",
            mark, topic, hz, min_hz, total
        )
    rospy.loginfo("═══════════════════════════════════════════════════════════════════════")
    if all_ok:
        rospy.loginfo("[Verify] ALL CHECKS PASSED — pipeline is healthy.")
    else:
        rospy.logwarn("[Verify] SOME CHECKS FAILED — check the topics above.")
    return all_ok


def main():
    rospy.init_node("verify_topics", anonymous=True)
    timeout       = float(rospy.get_param("~timeout",       20.0))
    sample_period = float(rospy.get_param("~sample_period",  2.0))
    run_verification(timeout=timeout, sample_period=sample_period)


if __name__ == "__main__":
    main()
