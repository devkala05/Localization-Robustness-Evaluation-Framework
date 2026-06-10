#!/usr/bin/env python3
"""
bag_player.py
=============
Controlled rosbag playback node for the FAST-LIVO2 pipeline.

Features
────────
  - Plays only the three sensor streams needed by the wrapper
    (LiDAR, IMU, right camera — no GPS, ground-truth, or other topics)
  - Configurable playback rate and start offset
  - Waits for a startup delay to allow all nodes to initialise
  - Publishes /clock when using simulated time
  - Exits cleanly on rosbag completion (triggering downstream shutdown)

Usage
─────
  rosrun fast_livo2_wrapper bag_player.py \
      _bag_path:=/data/your_bag.bag \
      _rate:=1.0 \
      _start_delay:=5.0

  python3 bag_player.py \
      --bag /data/your_bag.bag --rate 0.5 --start-delay 3.0
"""

import os
import sys
import time
import subprocess
import argparse

try:
    import rospy
    _HAS_ROS = True
except ImportError:
    _HAS_ROS = False


# Topics forwarded from the bag to the ROS network.
# Only sensor streams — all other topics are filtered out.
SENSOR_TOPICS = [
    "/velodyne_points",             # Centre Velodyne LiDAR
    "/imu/data",                    # Xsens IMU
    "/zed2/camera/right/image_raw", # ZED2 right camera
]


def play_bag(
    bag_path:     str,
    rate:         float = 1.0,
    start_delay:  float = 5.0,
    start_offset: float = 0.0,
    loop:         bool  = False,
    use_sim_time: bool  = True,
    extra_topics: list  = None,
):
    """
    Launch ``rosbag play`` as a subprocess and block until it completes.

    Args:
        bag_path:     Absolute path to the .bag file.
        rate:         Playback speed multiplier (1.0 = real-time).
        start_delay:  Seconds to wait before starting playback.
        start_offset: Seconds to skip from the start of the bag.
        loop:         Loop the bag indefinitely.
        use_sim_time: Publish /clock (required with use_sim_time:=true).
        extra_topics: Additional topics to include beyond SENSOR_TOPICS.
    """
    if not os.path.isfile(bag_path):
        msg = f"[BagPlayer] Bag file not found: {bag_path}"
        if _HAS_ROS:
            rospy.logerr(msg)
        else:
            print(msg, file=sys.stderr)
        sys.exit(1)

    if start_delay > 0:
        _log(f"[BagPlayer] Waiting {start_delay:.1f}s for pipeline to initialise …")
        time.sleep(start_delay)

    topics = SENSOR_TOPICS[:]
    if extra_topics:
        topics += extra_topics

    cmd = [
        "rosbag", "play",
        bag_path,
        "--rate",  str(rate),
        "--start", str(start_offset),
    ]
    if use_sim_time:
        cmd.append("--clock")
    if loop:
        cmd.append("--loop")
    cmd += ["--topics"] + topics

    _log("[BagPlayer] Command: " + " ".join(cmd))
    _log("[BagPlayer] Playing topics:\n" + "".join(f"  {t}\n" for t in topics))

    try:
        ret = subprocess.run(cmd)
    except KeyboardInterrupt:
        _log("[BagPlayer] Interrupted by user.")
        return

    if ret.returncode != 0:
        _log(f"[BagPlayer] rosbag play exited with code {ret.returncode}", level="error")
        sys.exit(ret.returncode)

    _log("[BagPlayer] Bag playback complete.")


def _log(msg: str, level: str = "info"):
    if _HAS_ROS:
        {"info": rospy.loginfo, "warn": rospy.logwarn, "error": rospy.logerr}[level](msg)
    else:
        print(msg, file=sys.stderr if level == "error" else sys.stdout)


# ─── ROS node entry ───────────────────────────────────────────────────────────

def main_rosnode():
    rospy.init_node("bag_player", anonymous=True)

    bag_path     = rospy.get_param("~bag_path",     "/data/UrbanNav-HK-TST-20210517_sensors.bag")
    rate         = float(rospy.get_param("~rate",          1.0))
    start_delay  = float(rospy.get_param("~start_delay",   5.0))
    start_offset = float(rospy.get_param("~start_offset",  0.0))
    loop         = rospy.get_param("~loop",          False)
    use_sim_time = rospy.get_param("~use_sim_time",  True)

    play_bag(
        bag_path=bag_path,
        rate=rate,
        start_delay=start_delay,
        start_offset=start_offset,
        loop=loop,
        use_sim_time=use_sim_time,
    )


# ─── CLI entry ────────────────────────────────────────────────────────────────

def main_cli():
    parser = argparse.ArgumentParser(
        description="Play sensor topics from a rosbag into the FAST-LIVO2 pipeline."
    )
    parser.add_argument("--bag",          required=True,  help="Path to .bag file")
    parser.add_argument("--rate",         type=float, default=1.0,
                        help="Playback speed (default 1.0)")
    parser.add_argument("--start-delay",  type=float, default=5.0,
                        help="Seconds to wait before playing (default 5.0)")
    parser.add_argument("--start-offset", type=float, default=0.0,
                        help="Skip first N seconds of bag (default 0)")
    parser.add_argument("--loop",         action="store_true",
                        help="Loop the bag indefinitely")
    parser.add_argument("--no-sim-time",  action="store_true",
                        help="Disable /clock publishing")
    args = parser.parse_args()

    play_bag(
        bag_path=args.bag,
        rate=args.rate,
        start_delay=args.start_delay,
        start_offset=args.start_offset,
        loop=args.loop,
        use_sim_time=not args.no_sim_time,
    )


if __name__ == "__main__":
    if "--bag" in sys.argv:
        main_cli()
    elif _HAS_ROS:
        main_rosnode()
    else:
        main_cli()
