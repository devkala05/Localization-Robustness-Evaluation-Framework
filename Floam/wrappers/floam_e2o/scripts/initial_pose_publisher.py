#!/usr/bin/env python3
"""Publish an initial pose for FLOAM relocalization.

ALIVE FLOAM waits for /initialpose when relocalization is enabled. This node
lets automated bag runs provide that pose without RViz.
"""

import math

import rospy
import tf.transformations as tft
from geometry_msgs.msg import PoseWithCovarianceStamped


def main():
    rospy.init_node("floam_initial_pose_publisher", anonymous=False)
    frame_id = rospy.get_param("~frame_id", "map")
    x = float(rospy.get_param("~x", rospy.get_param("/initial_pose/x", 0.0)))
    y = float(rospy.get_param("~y", rospy.get_param("/initial_pose/y", 0.0)))
    z = float(rospy.get_param("~z", rospy.get_param("/initial_pose/z", 0.0)))
    roll = float(rospy.get_param("~roll", rospy.get_param("/initial_pose/roll", 0.0)))
    pitch = float(rospy.get_param("~pitch", rospy.get_param("/initial_pose/pitch", 0.0)))
    yaw = float(rospy.get_param("~yaw", rospy.get_param("/initial_pose/yaw", 0.0)))
    delay = max(0.0, float(rospy.get_param("~publish_delay_sec", 3.0)))
    repeat_count = max(1, int(rospy.get_param("~repeat_count", 5)))
    repeat_period = max(0.1, float(rospy.get_param("~repeat_period_sec", 1.0)))

    pub = rospy.Publisher("/initialpose", PoseWithCovarianceStamped, queue_size=1, latch=True)
    rospy.sleep(delay)

    msg = PoseWithCovarianceStamped()
    msg.header.frame_id = frame_id
    msg.pose.pose.position.x = x
    msg.pose.pose.position.y = y
    msg.pose.pose.position.z = z
    qx, qy, qz, qw = tft.quaternion_from_euler(roll, pitch, yaw)
    msg.pose.pose.orientation.x = qx
    msg.pose.pose.orientation.y = qy
    msg.pose.pose.orientation.z = qz
    msg.pose.pose.orientation.w = qw

    covariance = [0.0] * 36
    covariance[0] = 0.25
    covariance[7] = 0.25
    covariance[14] = 0.25
    covariance[21] = math.radians(5.0) ** 2
    covariance[28] = math.radians(5.0) ** 2
    covariance[35] = math.radians(10.0) ** 2
    msg.pose.covariance = covariance

    for index in range(repeat_count):
        if rospy.is_shutdown():
            return
        msg.header.stamp = rospy.Time.now()
        pub.publish(msg)
        rospy.loginfo(
            "[FLOAM InitialPose] published %d/%d x=%.3f y=%.3f yaw=%.3f",
            index + 1,
            repeat_count,
            x,
            y,
            yaw,
        )
        rospy.sleep(repeat_period)


if __name__ == "__main__":
    main()
