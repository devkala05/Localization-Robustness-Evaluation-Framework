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


def angle_diff(a, b):
    return math.atan2(math.sin(a - b), math.cos(a - b))


def pose_tuple(msg):
    p = msg.pose.pose.position
    q = msg.pose.pose.orientation
    return {
        "stamp": msg.header.stamp.to_sec(),
        "x": p.x,
        "y": p.y,
        "z": p.z,
        "yaw": yaw_from_quat(q),
    }


class LocalizationOutputRecorder:
    def __init__(self):
        self.algorithm = rospy.get_param("~algorithm", "fast_lio2")
        self.run_id = str(rospy.get_param("~run_id", "1"))
        self.source_topic = rospy.get_param("~source_topic", "/Odometry")
        self.gt_odom_topic = rospy.get_param("~ground_truth_odom_topic", "/ground_truth_odometry")
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
        self.first_localization = None
        self.latest_gt = None
        self.start_delta_logged = False
        self.pub = rospy.Publisher(self.output_topic, LocalizationOutput, queue_size=50)
        rospy.Subscriber(self.source_topic, Odometry, self.cb, queue_size=100)
        if self.gt_odom_topic:
            rospy.Subscriber(self.gt_odom_topic, Odometry, self.gt_cb, queue_size=100)
        rospy.on_shutdown(self.close)
        rospy.loginfo(
            "[LocalizationOutputRecorder] source=%s gt=%s csv=%s",
            self.source_topic,
            self.gt_odom_topic or "disabled",
            self.csv_path,
        )

    def gt_cb(self, msg):
        self.latest_gt = pose_tuple(msg)
        self.log_start_delta()

    def log_start_delta(self):
        if self.start_delta_logged or self.first_localization is None or self.latest_gt is None:
            return
        local = self.first_localization
        gt = self.latest_gt
        dx = local["x"] - gt["x"]
        dy = local["y"] - gt["y"]
        dz = local["z"] - gt["z"]
        dyaw = angle_diff(local["yaw"], gt["yaw"])
        rospy.logwarn(
            "[LocalizationOutputRecorder] start_delta local_xyz=(%.3f, %.3f, %.3f) "
            "gt_xyz=(%.3f, %.3f, %.3f) dxyz=(%.3f, %.3f, %.3f) dist=%.3f m "
            "local_yaw=%.2f deg gt_yaw=%.2f deg dyaw=%.2f deg dt=%.3f s",
            local["x"], local["y"], local["z"],
            gt["x"], gt["y"], gt["z"],
            dx, dy, dz, math.sqrt(dx * dx + dy * dy + dz * dz),
            math.degrees(local["yaw"]), math.degrees(gt["yaw"]), math.degrees(dyaw),
            local["stamp"] - gt["stamp"],
        )
        self.start_delta_logged = True

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
            self.first_localization = pose_tuple(msg)
            rospy.loginfo("[LocalizationOutputRecorder] first odometry received at %.9f", t)
            self.log_start_delta()
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
