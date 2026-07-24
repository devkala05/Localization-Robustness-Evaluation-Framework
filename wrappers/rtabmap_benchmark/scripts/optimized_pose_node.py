#!/usr/bin/env python3
"""Expose RTAB-Map's native online map-frame pose as Odometry.

RTAB-Map represents graph corrections with its map->odom transform while the
ICP front-end publishes odom->base.  Composing those two native outputs is the
documented online SLAM pose; no alignment, re-anchoring, or filtering occurs
here.
"""
import copy

import rospy
import tf2_geometry_msgs  # noqa: F401: registers geometry message converters
import tf2_ros
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry


class OptimizedPoseNode:
    def __init__(self):
        input_topic = rospy.get_param("~input_topic", "/rtabmap/icp_odometry")
        output_topic = rospy.get_param("~output_topic", "/rtabmap/odometry")
        self.map_frame = rospy.get_param("~map_frame", "rtabmap_map")
        self.last_stamp = None
        self.tf_buffer = tf2_ros.Buffer(cache_time=rospy.Duration(30.0))
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)
        self.publisher = rospy.Publisher(output_topic, Odometry, queue_size=100)
        rospy.Subscriber(input_topic, Odometry, self.odom_callback, queue_size=100)
        rospy.loginfo(
            "[RTABMap optimized pose] compose %s->odom TF with %s -> %s",
            self.map_frame, input_topic, output_topic)

    def odom_callback(self, message):
        stamp = message.header.stamp
        if stamp == rospy.Time(0):
            rospy.logwarn_throttle(2.0, "[RTABMap optimized pose] dropping zero timestamp")
            return
        if self.last_stamp is not None and stamp <= self.last_stamp:
            return
        try:
            map_from_odom = self.tf_buffer.lookup_transform(
                self.map_frame, message.header.frame_id, rospy.Time(0), rospy.Duration(0.0))
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException) as error:
            rospy.logwarn_throttle(
                2.0, "[RTABMap optimized pose] waiting for native map->odom TF: %s", error)
            return
        source_pose = PoseStamped()
        source_pose.header = copy.deepcopy(message.header)
        source_pose.pose = copy.deepcopy(message.pose.pose)
        optimized_pose = tf2_geometry_msgs.do_transform_pose(source_pose, map_from_odom)
        output = copy.deepcopy(message)
        output.header = copy.deepcopy(optimized_pose.header)
        output.header.stamp = stamp
        output.header.frame_id = self.map_frame
        output.pose.pose = copy.deepcopy(optimized_pose.pose)
        self.last_stamp = stamp
        self.publisher.publish(output)


def main():
    rospy.init_node("rtabmap_optimized_pose")
    OptimizedPoseNode()
    rospy.spin()


if __name__ == "__main__":
    main()
