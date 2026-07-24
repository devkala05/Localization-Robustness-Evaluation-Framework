#!/usr/bin/env python3
"""Publish legitimate reference poses and a clearly labelled accumulated cloud."""
from __future__ import annotations

import bisect
import csv
import math
from pathlib import Path

import numpy as np
import rospy
import tf2_ros
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Odometry, Path as PathMessage
from sensor_msgs import point_cloud2
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import Header


def load_csv(path: Path):
    stamps, poses = [], []
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            values = [float(row[name]) for name in
                      ("timestamp_s", "x_m", "y_m", "z_m", "qx", "qy", "qz", "qw")]
            if all(math.isfinite(value) for value in values):
                stamps.append(values[0]); poses.append(values[1:])
    if not stamps or any(b <= a for a, b in zip(stamps, stamps[1:])):
        raise rospy.ROSInitException(f"empty or non-monotonic trajectory: {path}")
    return np.asarray(stamps), np.asarray(poses)


def rotation(q):
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def path_message(stamps, poses, frame):
    message = PathMessage(header=Header(frame_id=frame))
    for stamp, values in zip(stamps, poses):
        item = PoseStamped(header=Header(stamp=rospy.Time.from_sec(float(stamp)), frame_id=frame))
        item.pose.position.x, item.pose.position.y, item.pose.position.z = values[:3]
        item.pose.orientation.x, item.pose.orientation.y, item.pose.orientation.z, item.pose.orientation.w = values[3:]
        message.poses.append(item)
    return message


class ReferenceVisualizer:
    def __init__(self):
        self.frame = rospy.get_param("~reference_frame", "reference")
        # Keep the reference vehicle TF separate from an estimator's base_link;
        # otherwise both publishers claim the same child during overlays.
        self.vehicle_frame = rospy.get_param("~reference_vehicle_frame", "reference_base_link")
        self.stamps, self.poses = load_csv(Path(rospy.get_param("~ground_truth_csv")))
        self.path_pub = rospy.Publisher("/reference/path", PathMessage, queue_size=1, latch=True)
        self.pose_pub = rospy.Publisher("/reference/odometry", Odometry, queue_size=10)
        self.cloud_pub = rospy.Publisher("/reference/accumulated_lidar_unofficial", PointCloud2, queue_size=1, latch=True)
        self.tf = tf2_ros.TransformBroadcaster()
        self.path_pub.publish(path_message(self.stamps, self.poses, self.frame))
        estimate = str(rospy.get_param("~estimate_csv", ""))
        if estimate:
            est_stamps, est_poses = load_csv(Path(estimate))
            self.estimate_pub = rospy.Publisher("/estimate/path", PathMessage, queue_size=1, latch=True)
            self.estimate_pub.publish(path_message(est_stamps, est_poses, self.frame))
        transform = rospy.get_param("~base_to_lidar", [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1])
        self.t_base_lidar = np.eye(4)
        self.t_base_lidar[:3, 3] = transform[:3]
        self.t_base_lidar[:3, :3] = np.asarray(transform[3:]).reshape(3, 3)
        self.points = []
        self.last_pose_index = -1
        self.max_points = int(rospy.get_param("~max_accumulated_points", 600000))
        self.stride = max(1, int(rospy.get_param("~point_stride", 50)))
        rospy.Subscriber("/benchmark/points_raw", PointCloud2, self.cloud_cb, queue_size=2)
        rospy.Timer(rospy.Duration(0.02), self.timer_cb)

    def index(self, stamp):
        right = bisect.bisect_left(self.stamps, stamp)
        if right <= 0: return 0
        if right >= len(self.stamps): return len(self.stamps)-1
        return right if self.stamps[right]-stamp < stamp-self.stamps[right-1] else right-1

    def pose_matrix(self, index):
        out = np.eye(4); out[:3, :3] = rotation(self.poses[index, 3:]); out[:3, 3] = self.poses[index, :3]
        return out

    def timer_cb(self, _event):
        now = rospy.Time.now().to_sec()
        index = self.index(now)
        if index == self.last_pose_index:
            return
        self.last_pose_index = index
        values = self.poses[index]
        odom = Odometry(header=Header(stamp=rospy.Time.from_sec(float(self.stamps[index])), frame_id=self.frame), child_frame_id=self.vehicle_frame)
        odom.pose.pose.position.x, odom.pose.pose.position.y, odom.pose.pose.position.z = values[:3]
        odom.pose.pose.orientation.x, odom.pose.pose.orientation.y, odom.pose.pose.orientation.z, odom.pose.pose.orientation.w = values[3:]
        self.pose_pub.publish(odom)
        tf = TransformStamped(header=odom.header, child_frame_id=self.vehicle_frame)
        tf.transform.translation.x, tf.transform.translation.y, tf.transform.translation.z = values[:3]
        tf.transform.rotation = odom.pose.pose.orientation
        self.tf.sendTransform(tf)

    def cloud_cb(self, message):
        index = self.index(message.header.stamp.to_sec())
        transform = self.pose_matrix(index) @ self.t_base_lidar
        selected = []
        for number, point in enumerate(point_cloud2.read_points(message, field_names=("x", "y", "z"), skip_nans=True)):
            if number % self.stride == 0:
                selected.append(point)
        if not selected: return
        points = np.asarray(selected, dtype=float)
        mapped = (transform[:3, :3] @ points.T).T + transform[:3, 3]
        self.points.extend(mapped.tolist())
        if len(self.points) > self.max_points:
            self.points = self.points[-self.max_points:]
        header = Header(stamp=message.header.stamp, frame_id=self.frame)
        self.cloud_pub.publish(point_cloud2.create_cloud_xyz32(header, self.points))


rospy.init_node("reference_visualizer")
ReferenceVisualizer()
rospy.spin()
