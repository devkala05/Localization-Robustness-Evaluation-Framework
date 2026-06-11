#!/usr/bin/env python3
import csv
import math
import os

import rospy
from nav_msgs.msg import Odometry

from custom_localization_msgs.msg import LocalizationOutput


def yaw_from_quat(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class LocalizationOutputRecorder:
    def __init__(self):
        self.algorithm = rospy.get_param("~algorithm", "fast_lio2")
        self.run_id = str(rospy.get_param("~run_id", "1"))
        self.source_topic = rospy.get_param("~source_topic", "/Odometry")
        self.output_topic = rospy.get_param("~custom_output_topic", "/mycar/localization/output")
        self.csv_path = rospy.get_param(
            "~csv_path",
            f"/data/results/{self.algorithm}/run_{self.run_id}/trajectory.csv",
        )
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        self.handle = open(self.csv_path, "w", newline="", encoding="utf-8", buffering=1)
        self.writer = csv.writer(self.handle)
        self.writer.writerow([
            "stamp", "x", "y", "z", "qx", "qy", "qz", "qw", "yaw",
            "vx", "vy", "vz", "algorithm", "run_id",
        ])
        self.handle.flush()
        self.count = 0
        self.pub = rospy.Publisher(self.output_topic, LocalizationOutput, queue_size=50)
        rospy.Subscriber(self.source_topic, Odometry, self.cb, queue_size=100)
        rospy.on_shutdown(self.close)
        rospy.loginfo("[LocalizationOutputRecorder] %s -> %s", self.source_topic, self.csv_path)

    def cb(self, msg):
        q = msg.pose.pose.orientation
        yaw = yaw_from_quat(q)
        t = msg.header.stamp.to_sec()
        self.writer.writerow([
            f"{t:.9f}",
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.pose.pose.position.z,
            q.x, q.y, q.z, q.w, yaw,
            msg.twist.twist.linear.x,
            msg.twist.twist.linear.y,
            msg.twist.twist.linear.z,
            self.algorithm,
            self.run_id,
        ])
        self.handle.flush()
        self.count += 1
        if self.count == 1:
            rospy.loginfo("[LocalizationOutputRecorder] first odometry received at %.9f", t)
        out = LocalizationOutput()
        out.header = msg.header
        out.algorithm = self.algorithm
        out.run_id = self.run_id
        out.source_topic = self.source_topic
        out.pose = msg.pose
        out.twist = msg.twist
        self.pub.publish(out)

    def close(self):
        if not self.handle.closed:
            self.handle.flush()
            self.handle.close()


def main():
    rospy.init_node("localization_output_recorder")
    LocalizationOutputRecorder()
    rospy.spin()


if __name__ == "__main__":
    main()
