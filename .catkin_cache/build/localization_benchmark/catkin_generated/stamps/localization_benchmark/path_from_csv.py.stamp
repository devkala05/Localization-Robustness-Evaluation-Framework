#!/usr/bin/env python3
import csv
import os

import rospy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path


class CsvPathPublisher:
    def __init__(self):
        self.csv_path = rospy.get_param("~csv_path")
        self.topic = rospy.get_param("~topic", "/benchmark/path")
        self.frame_id = rospy.get_param("~frame_id", "camera_init")
        self.rate_hz = float(rospy.get_param("~rate", 1.0))
        self.path_msg = self.load_path()
        self.pub = rospy.Publisher(self.topic, Path, queue_size=1, latch=True)

    def load_path(self):
        path = Path()
        path.header.frame_id = self.frame_id
        if not os.path.isfile(self.csv_path):
            rospy.logwarn("[CsvPathPublisher] Missing CSV: %s", self.csv_path)
            return path
        try:
            with open(self.csv_path, "r", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                required = {"stamp", "x", "y", "z", "qx", "qy", "qz", "qw"}
                if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
                    rospy.logwarn_throttle(5.0, "[CsvPathPublisher] CSV not ready/empty: %s", self.csv_path)
                    return path
                for row in reader:
                    try:
                        pose = PoseStamped()
                        pose.header.frame_id = self.frame_id
                        pose.header.stamp = rospy.Time.from_sec(float(row["stamp"]))
                        pose.pose.position.x = float(row["x"])
                        pose.pose.position.y = float(row["y"])
                        pose.pose.position.z = float(row["z"])
                        pose.pose.orientation.x = float(row["qx"])
                        pose.pose.orientation.y = float(row["qy"])
                        pose.pose.orientation.z = float(row["qz"])
                        pose.pose.orientation.w = float(row["qw"])
                        path.poses.append(pose)
                    except Exception as exc:
                        rospy.logwarn_throttle(5.0, "[CsvPathPublisher] skipping bad row in %s: %s", self.csv_path, exc)
        except Exception as exc:
            rospy.logwarn_throttle(5.0, "[CsvPathPublisher] could not read %s: %s", self.csv_path, exc)
        return path

    def spin(self):
        rate = rospy.Rate(self.rate_hz)
        while not rospy.is_shutdown():
            self.path_msg.header.stamp = rospy.Time.now()
            self.pub.publish(self.path_msg)
            rate.sleep()


def main():
    rospy.init_node("path_from_csv", anonymous=True)
    CsvPathPublisher().spin()


if __name__ == "__main__":
    main()
