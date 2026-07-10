#!/usr/bin/env python3
"""Publish a nav_msgs/Path from a FLOAM odometry stream."""

import rospy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry, Path


class OdometryPathNode:
    def __init__(self):
        self.input_topic = rospy.get_param("~input_topic", "/floam/odometry")
        self.output_topic = rospy.get_param("~output_topic", "/floam/path")
        self.max_poses = rospy.get_param("~max_poses", 20000)
        self.path = Path()
        self.pub = rospy.Publisher(self.output_topic, Path, queue_size=1, latch=True)
        rospy.Subscriber(self.input_topic, Odometry, self.odom_cb, queue_size=100)
        rospy.loginfo("[FLOAM Path] %s -> %s", self.input_topic, self.output_topic)

    def odom_cb(self, msg):
        pose = PoseStamped()
        pose.header = msg.header
        pose.pose = msg.pose.pose

        self.path.header = msg.header
        self.path.poses.append(pose)
        if self.max_poses > 0 and len(self.path.poses) > self.max_poses:
            self.path.poses = self.path.poses[-self.max_poses:]
        self.pub.publish(self.path)


def main():
    rospy.init_node("floam_odometry_path_node", anonymous=False)
    OdometryPathNode()
    rospy.spin()


if __name__ == "__main__":
    main()
