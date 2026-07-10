#!/usr/bin/env python3
"""Broadcast TF from a FLOAM odometry topic for standalone RViz use."""

import rospy
import tf2_ros
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry


class OdometryTfBroadcaster:
    def __init__(self):
        self.input_topic = rospy.get_param("~input_topic", "/floam/odometry")
        self.parent_frame = rospy.get_param("~parent_frame", "")
        self.child_frame = rospy.get_param("~child_frame", "")
        self.br = tf2_ros.TransformBroadcaster()
        rospy.Subscriber(self.input_topic, Odometry, self.odom_cb, queue_size=100)
        rospy.loginfo("[FLOAM TF] broadcasting odometry TF from %s", self.input_topic)

    def odom_cb(self, msg):
        transform = TransformStamped()
        transform.header.stamp = msg.header.stamp
        transform.header.frame_id = self.parent_frame or msg.header.frame_id
        transform.child_frame_id = self.child_frame or msg.child_frame_id
        transform.transform.translation.x = msg.pose.pose.position.x
        transform.transform.translation.y = msg.pose.pose.position.y
        transform.transform.translation.z = msg.pose.pose.position.z
        transform.transform.rotation = msg.pose.pose.orientation
        self.br.sendTransform(transform)


def main():
    rospy.init_node("floam_odometry_tf_broadcaster", anonymous=False)
    OdometryTfBroadcaster()
    rospy.spin()


if __name__ == "__main__":
    main()
