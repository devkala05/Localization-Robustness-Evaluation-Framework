#!/usr/bin/env python3
"""Republish FLOAM odometry under one stable E2O topic."""

import rospy
from nav_msgs.msg import Odometry


class OdometryAliasNode:
    def __init__(self):
        self.input_topic = rospy.get_param("~input_topic", "/odom")
        self.output_topic = rospy.get_param("~output_topic", "/floam/odometry")
        self.last_published_stamp = None
        self.pub = rospy.Publisher(self.output_topic, Odometry, queue_size=100)
        rospy.Subscriber(self.input_topic, Odometry, self.odom_cb, queue_size=100)
        rospy.loginfo("[FLOAM OdomAlias] %s -> %s", self.input_topic, self.output_topic)

    def odom_cb(self, msg):
        stamp = msg.header.stamp.to_sec()
        if stamp <= 0.0:
            rospy.logwarn_throttle(2.0, "[FLOAM OdomAlias] dropping zero timestamp")
            return
        if self.last_published_stamp is not None and stamp <= self.last_published_stamp:
            rospy.logwarn_throttle(2.0, "[FLOAM OdomAlias] dropping non-monotonic timestamp")
            return
        self.last_published_stamp = stamp
        self.pub.publish(msg)


def main():
    rospy.init_node("floam_odometry_alias", anonymous=False)
    OdometryAliasNode()
    rospy.spin()


if __name__ == "__main__":
    main()
