#!/usr/bin/env python3
"""Record one odometry topic to an E2O-style trajectory CSV."""

import csv
import os
import threading

import rospy
from nav_msgs.msg import Odometry


class TrajectoryRecorder:
    def __init__(self):
        self.lock = threading.Lock()
        self.topic = rospy.get_param("~topic", "/floam/odometry")
        self.output_dir = rospy.get_param("~output_dir", "/data/output/current_floam_run")
        self.name = rospy.get_param("~name", "floam")
        os.makedirs(self.output_dir, exist_ok=True)
        self.path = os.path.join(self.output_dir, f"{self.name}_trajectory.csv")
        self.handle = open(self.path, "w", newline="", encoding="utf-8")
        self.writer = csv.writer(self.handle)
        self.writer.writerow(["timestamp_s", "x_m", "y_m", "z_m", "qx", "qy", "qz", "qw", "frame_id", "child_frame_id"])
        rospy.Subscriber(self.topic, Odometry, self.odom_cb, queue_size=500)
        rospy.on_shutdown(self.close)
        rospy.loginfo("[FLOAM Recorder] %s -> %s", self.topic, self.path)

    def odom_cb(self, msg):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        with self.lock:
            self.writer.writerow([
                msg.header.stamp.to_sec(),
                p.x,
                p.y,
                p.z,
                q.x,
                q.y,
                q.z,
                q.w,
                msg.header.frame_id,
                msg.child_frame_id,
            ])
            self.handle.flush()

    def close(self):
        with self.lock:
            if not self.handle.closed:
                self.handle.close()


def main():
    rospy.init_node("floam_trajectory_recorder", anonymous=False)
    TrajectoryRecorder()
    rospy.spin()


if __name__ == "__main__":
    main()
