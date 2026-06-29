#!/usr/bin/env python3
"""Republish native LVI-SAM mapping odometry under one benchmark topic."""
import rospy
from nav_msgs.msg import Odometry


class OdometryAliasNode:
    def __init__(self):
        self.input_topic = rospy.get_param("~input_topic", "/lvi_sam/lidar/mapping/odometry")
        self.output_topic = rospy.get_param("~output_topic", "/lvisam/odometry")
        self.pub = rospy.Publisher(self.output_topic, Odometry, queue_size=100)
        rospy.Subscriber(self.input_topic, Odometry, self.odom_cb, queue_size=100)
        rospy.loginfo("[LVISAM OdomAlias] %s -> %s", self.input_topic, self.output_topic)

    def odom_cb(self, msg):
        self.pub.publish(msg)


def main():
    rospy.init_node("lvisam_odometry_alias", anonymous=False)
    OdometryAliasNode()
    rospy.spin()


if __name__ == "__main__":
    main()
