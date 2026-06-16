#!/usr/bin/env python3
"""
bag_player.py  (orbslam3_urbannav)
===================================
Controlled rosbag playback for ORB-SLAM3 UrbanNav modes.

Usage (rosrun):
    rosrun orbslam3_urbannav bag_player.py \
        _bag_path:=/data/UrbanNav-HK_TST-20210517_sensors.bag \
        _rate:=1.0 \
        _start_delay:=3.0
"""

import os
import sys
import time
import subprocess
import argparse
import rospy

MONO_TOPICS = [
    "/zed2/camera/right/image_raw",        # ZED2 right → wrapper → /camera/image_raw
    "/zed2/camera/right/camera_info",      # camera_info for intrinsic reference (optional)
]

STEREO_TOPICS = [
    "/zed2/camera/left/image_raw",
    "/zed2/camera/left/camera_info",
    "/zed2/camera/right/image_raw",
    "/zed2/camera/right/camera_info",
]


def play_bag(bag_path: str,
             rate: float = 1.0,
             start_delay: float = 3.0,
             loop: bool = False,
             start_offset: float = 0.0,
             use_sim_time: bool = True,
             mode: str = "mono"):

    if not os.path.isfile(bag_path):
        rospy.logerr(f"[BagPlayer] Bag not found: {bag_path}")
        sys.exit(1)

    rospy.loginfo(f"[BagPlayer] Waiting {start_delay:.1f}s for wrapper to initialise …")
    time.sleep(start_delay)

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

    topics = STEREO_TOPICS if mode == "stereo" else MONO_TOPICS
    cmd += ["--topics"] + topics

    rospy.loginfo("[BagPlayer] Running: %s", " ".join(cmd))
    rospy.loginfo(
        "[BagPlayer] Playing topics:\n" +
        "".join(f"  {t}\n" for t in topics)
    )

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        rospy.logerr(f"[BagPlayer] rosbag play exited with code {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        rospy.loginfo("[BagPlayer] Interrupted.")


def main():
    rospy.init_node("bag_player", anonymous=True)
    bag_path     = rospy.get_param("~bag_path",     "/data/UrbanNav-HK_TST-20210517_sensors.bag")
    rate         = float(rospy.get_param("~rate",          1.0))
    start_delay  = float(rospy.get_param("~start_delay",   3.0))
    loop         = rospy.get_param("~loop",          False)
    start_offset = float(rospy.get_param("~start_offset",  0.0))
    use_sim_time = rospy.get_param("~use_sim_time",  True)
    mode         = rospy.get_param("~mode",          "mono")
    play_bag(bag_path, rate, start_delay, loop, start_offset, use_sim_time, mode)


if __name__ == "__main__":
    if "--bag" in sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument("--bag",          required=True)
        parser.add_argument("--rate",         type=float, default=1.0)
        parser.add_argument("--start-delay",  type=float, default=3.0)
        parser.add_argument("--loop",         action="store_true")
        parser.add_argument("--start-offset", type=float, default=0.0)
        parser.add_argument("--no-sim-time",  action="store_true")
        parser.add_argument("--mode",         choices=["mono", "stereo"], default="mono")
        args = parser.parse_args()
        play_bag(args.bag, args.rate, args.start_delay,
                 args.loop, args.start_offset, not args.no_sim_time, args.mode)
    else:
        main()
