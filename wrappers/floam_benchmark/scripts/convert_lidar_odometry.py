#!/usr/bin/env python3
"""Convert FLOAM's native LiDAR-frame motion into calibrated base motion."""

import numpy as np
import rospy
from nav_msgs.msg import Odometry
from tf.transformations import quaternion_from_matrix, quaternion_matrix


class LidarOdometryConverter:
    def __init__(self):
        values = np.asarray(rospy.get_param("~base_to_lidar"), dtype=float)
        if values.shape != (12,) or not np.all(np.isfinite(values)):
            raise rospy.ROSInitException("base_to_lidar must contain 12 finite values")
        self.base_from_lidar = np.eye(4)
        self.base_from_lidar[:3, 3] = values[:3]
        self.base_from_lidar[:3, :3] = values[3:].reshape(3, 3)
        self.lidar_from_base = np.linalg.inv(self.base_from_lidar)
        input_topic = rospy.get_param("~input_topic", "/odom")
        output_topic = rospy.get_param("~output_topic", "/floam/odometry")
        self.publisher = rospy.Publisher(output_topic, Odometry, queue_size=20)
        self.subscriber = rospy.Subscriber(input_topic, Odometry, self.callback, queue_size=20)

    def callback(self, message):
        q = message.pose.pose.orientation
        native = quaternion_matrix([q.x, q.y, q.z, q.w])
        p = message.pose.pose.position
        native[:3, 3] = (p.x, p.y, p.z)
        converted = self.base_from_lidar @ native @ self.lidar_from_base
        quaternion = quaternion_from_matrix(converted)
        output = Odometry()
        output.header = message.header
        output.header.frame_id = "map"
        output.child_frame_id = "base_link"
        output.pose = message.pose
        output.twist = message.twist
        output.pose.pose.position.x, output.pose.pose.position.y, output.pose.pose.position.z = converted[:3, 3]
        (output.pose.pose.orientation.x, output.pose.pose.orientation.y,
         output.pose.pose.orientation.z, output.pose.pose.orientation.w) = quaternion
        self.publisher.publish(output)


if __name__ == "__main__":
    rospy.init_node("floam_lidar_to_base_odometry")
    LidarOdometryConverter()
    rospy.spin()
