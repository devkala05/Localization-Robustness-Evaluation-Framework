#!/usr/bin/env python3
import argparse
import csv
import math

import rospy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Publish a GT CSV as nav_msgs/Path.")
    parser.add_argument("--csv", default="/ws/gt_one_full_loop_gps_enu.csv")
    parser.add_argument("--topic", default="/gt_path")
    parser.add_argument("--frame-id", default="")
    parser.add_argument("--rate", type=float, default=1.0)
    parser.add_argument(
        "--stride",
        type=int,
        default=10,
        help="Publish every Nth CSV pose to keep RViz responsive.",
    )
    return parser.parse_args()


def f(row, key, default=0.0):
    try:
        value = float(row.get(key, default))
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def load_path(csv_path, frame_id, stride):
    path = Path()
    with open(csv_path, newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader):
            if stride > 1 and index % stride != 0:
                continue
            if not frame_id:
                frame_id = row.get("frame_id") or "map"
            pose = PoseStamped()
            pose.header.frame_id = frame_id
            stamp_ns = int(row["timestamp_ns"])
            pose.header.stamp = rospy.Time(stamp_ns // 1000000000, stamp_ns % 1000000000)
            pose.pose.position.x = f(row, "x_m")
            pose.pose.position.y = f(row, "y_m")
            pose.pose.position.z = f(row, "z_m")
            pose.pose.orientation.x = f(row, "qx")
            pose.pose.orientation.y = f(row, "qy")
            pose.pose.orientation.z = f(row, "qz")
            pose.pose.orientation.w = f(row, "qw", 1.0)
            path.poses.append(pose)
    path.header.frame_id = frame_id or "map"
    return path


def main():
    args = parse_args()
    rospy.init_node("gt_path_publisher", anonymous=False)
    publisher = rospy.Publisher(args.topic, Path, queue_size=1, latch=True)
    path = load_path(args.csv, args.frame_id, max(1, args.stride))
    rate = rospy.Rate(args.rate)
    rospy.loginfo("Loaded %d GT poses from %s", len(path.poses), args.csv)
    while not rospy.is_shutdown():
        path.header.stamp = rospy.Time.now()
        for pose in path.poses:
            pose.header.stamp = path.header.stamp
        publisher.publish(path)
        rate.sleep()


if __name__ == "__main__":
    main()
