#!/usr/bin/env python3
"""Republish native lvio_fusion path as benchmark odometry/path.

The upstream jypjypjypjyp/lvio_fusion node publishes a private nav_msgs/Path
(`/lvio_fusion_node/path`) in frame `world` and does not provide the benchmark's
standard odometry topic. This adapter only changes the output interface; it does
not estimate poses itself.
"""

import threading

import rospy
import tf2_ros
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Odometry, Path


class LVIOFusionOutputRepublisher:
    def __init__(self):
        self.input_path_topic = rospy.get_param("~input_path_topic", "/lvio_fusion_node/path")
        self.output_odom_topic = rospy.get_param("~output_odom_topic", "/adaptive_w_lvio/odometry/mapping")
        self.output_path_topic = rospy.get_param("~output_path_topic", "/adaptive_w_lvio/mapping/path")
        self.world_frame_id = rospy.get_param("~world_frame_id", "camera_init")
        self.child_frame_id = rospy.get_param("~child_frame_id", "body")
        self.normalize_to_start = bool(rospy.get_param("~normalize_to_start", True))
        self.publish_tf = bool(rospy.get_param("~publish_tf", False))

        self._lock = threading.Lock()
        self._origin = None
        self._last_stamp = None
        self._path = Path()
        self._path.header.frame_id = self.world_frame_id

        self._pub_odom = rospy.Publisher(self.output_odom_topic, Odometry, queue_size=50)
        self._pub_path = rospy.Publisher(self.output_path_topic, Path, queue_size=10)
        self._tf = tf2_ros.TransformBroadcaster() if self.publish_tf else None
        rospy.Subscriber(self.input_path_topic, Path, self._path_cb, queue_size=10)

        rospy.loginfo("[lvio_fusion_output_republisher] %s -> %s, %s",
                      self.input_path_topic, self.output_odom_topic, self.output_path_topic)

    def _normalize_pose(self, pose):
        # Keep orientation as native; translate the first pose to the benchmark origin.
        # This avoids changing lvio_fusion's own visual-inertial estimate while making
        # paths comparable to other wrappers that start at camera_init/body.
        p = PoseStamped()
        p.header = pose.header
        p.header.frame_id = self.world_frame_id
        p.pose = pose.pose
        if self.normalize_to_start:
            if self._origin is None:
                self._origin = (pose.pose.position.x, pose.pose.position.y, pose.pose.position.z)
            p.pose.position.x -= self._origin[0]
            p.pose.position.y -= self._origin[1]
            p.pose.position.z -= self._origin[2]
        return p

    def _path_cb(self, msg):
        if not msg.poses:
            return
        with self._lock:
            latest_native = msg.poses[-1]
            latest = self._normalize_pose(latest_native)
            stamp = latest.header.stamp if latest.header.stamp != rospy.Time(0) else rospy.Time.now()
            if self._last_stamp is not None and stamp < self._last_stamp:
                self._path.poses = []
                self._origin = None
                latest = self._normalize_pose(latest_native)
            self._last_stamp = stamp

            odom = Odometry()
            odom.header.stamp = stamp
            odom.header.frame_id = self.world_frame_id
            odom.child_frame_id = self.child_frame_id
            odom.pose.pose = latest.pose
            odom.pose.covariance[0] = 1e-2
            odom.pose.covariance[7] = 1e-2
            odom.pose.covariance[14] = 1e-2
            odom.pose.covariance[21] = 1e-1
            odom.pose.covariance[28] = 1e-1
            odom.pose.covariance[35] = 1e-1
            self._pub_odom.publish(odom)

            latest.header.stamp = stamp
            self._path.header.stamp = stamp
            self._path.poses.append(latest)
            if len(self._path.poses) > 200000:
                self._path.poses = self._path.poses[-200000:]
            self._pub_path.publish(self._path)

            if self._tf is not None:
                tf = TransformStamped()
                tf.header.stamp = stamp
                tf.header.frame_id = self.world_frame_id
                tf.child_frame_id = self.child_frame_id
                tf.transform.translation.x = latest.pose.position.x
                tf.transform.translation.y = latest.pose.position.y
                tf.transform.translation.z = latest.pose.position.z
                tf.transform.rotation = latest.pose.orientation
                self._tf.sendTransform(tf)


def main():
    rospy.init_node("lvio_fusion_output_republisher")
    LVIOFusionOutputRepublisher()
    rospy.spin()


if __name__ == "__main__":
    main()
