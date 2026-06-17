#!/usr/bin/env python3
"""
RTAB-Map UrbanNav adapter.

FAST-LIO2 is used as the odometry frontend. This node converts its odometry
stream into the frame naming expected by RTAB-Map and also publishes a stable
benchmark odometry topic.

Input:
  /Odometry                 nav_msgs/Odometry from FAST-LIO2

Outputs:
  /rtabmap/input_odom       nav_msgs/Odometry for rtabmap_ros
  camera_init -> body       dynamic TF for RTAB-Map scan/RGB synchronization

Benchmark odometry is intentionally NOT published here. It is produced by
rtabmap_output_adapter_node.py from RTAB-Map's optimized mapPath so the benchmark
uses RTAB-Map output, not raw FAST-LIO2 odometry.
"""

import rospy
import tf2_ros
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from tf.transformations import (
    concatenate_matrices,
    quaternion_from_matrix,
    quaternion_matrix,
    translation_from_matrix,
    translation_matrix,
)


class RtabmapAdapter:
    def __init__(self):
        self.input_odom_topic = rospy.get_param("~input_odom_topic", "/Odometry")
        self.rtabmap_odom_topic = rospy.get_param("~rtabmap_odom_topic", "/rtabmap/input_odom")
        self.odom_frame_id = rospy.get_param("~odom_frame_id", "camera_init")
        self.map_frame_id = rospy.get_param("~map_frame_id", "map")
        self.base_frame_id = rospy.get_param("~base_frame_id", "body")
        self.publish_tf = bool(rospy.get_param("~publish_tf", True))
        self.apply_rtabmap_tf = bool(rospy.get_param("~apply_rtabmap_tf", True))
        self.max_path_length = int(rospy.get_param("~max_path_length", 200000))

        self.tf_buffer = tf2_ros.Buffer(cache_time=rospy.Duration(30.0))
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

        self.pub_input = rospy.Publisher(self.rtabmap_odom_topic, Odometry, queue_size=100)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster() if self.publish_tf else None
        self.count = 0

        rospy.Subscriber(self.input_odom_topic, Odometry, self.odom_cb, queue_size=200)
        rospy.loginfo(
            "[RTAB-Map InputAdapter] %s -> %s, frames odom=%s map=%s base=%s",
            self.input_odom_topic,
            self.rtabmap_odom_topic,
            self.odom_frame_id,
            self.map_frame_id,
            self.base_frame_id,
        )

    def odom_cb(self, msg: Odometry):
        stamp = msg.header.stamp if msg.header.stamp != rospy.Time(0) else rospy.Time.now()

        # Odometry consumed by RTAB-Map. Keep FAST-LIO2 pose numeric values, but
        # expose the same benchmark local frame convention used by other algorithms:
        # camera_init -> body.
        odom_for_rtabmap = Odometry()
        odom_for_rtabmap.header.stamp = stamp
        odom_for_rtabmap.header.frame_id = self.odom_frame_id
        odom_for_rtabmap.child_frame_id = self.base_frame_id
        odom_for_rtabmap.pose = msg.pose
        odom_for_rtabmap.twist = msg.twist
        self.pub_input.publish(odom_for_rtabmap)

        if self.publish_tf:
            tf_msg = TransformStamped()
            tf_msg.header.stamp = stamp
            tf_msg.header.frame_id = self.odom_frame_id
            tf_msg.child_frame_id = self.base_frame_id
            tf_msg.transform.translation.x = msg.pose.pose.position.x
            tf_msg.transform.translation.y = msg.pose.pose.position.y
            tf_msg.transform.translation.z = msg.pose.pose.position.z
            tf_msg.transform.rotation = msg.pose.pose.orientation
            self.tf_broadcaster.sendTransform(tf_msg)

        self.count += 1
        if self.count == 1:
            rospy.loginfo("[RTAB-Map InputAdapter] first FAST-LIO2 odometry received at %.9f", stamp.to_sec())

    @staticmethod
    def _transform_pose(transform_stamped, pose):
        t = transform_stamped.transform.translation
        q = transform_stamped.transform.rotation
        transform_matrix = concatenate_matrices(
            translation_matrix([t.x, t.y, t.z]),
            quaternion_matrix([q.x, q.y, q.z, q.w]),
        )
        p = pose.position
        pq = pose.orientation
        pose_matrix = concatenate_matrices(
            translation_matrix([p.x, p.y, p.z]),
            quaternion_matrix([pq.x, pq.y, pq.z, pq.w]),
        )
        out_matrix = concatenate_matrices(transform_matrix, pose_matrix)
        out_pose = type(pose)()
        tr = translation_from_matrix(out_matrix)
        quat = quaternion_from_matrix(out_matrix)
        out_pose.position.x = float(tr[0])
        out_pose.position.y = float(tr[1])
        out_pose.position.z = float(tr[2])
        out_pose.orientation.x = float(quat[0])
        out_pose.orientation.y = float(quat[1])
        out_pose.orientation.z = float(quat[2])
        out_pose.orientation.w = float(quat[3])
        return out_pose


def main():
    rospy.init_node("rtabmap_adapter_node", anonymous=False)
    RtabmapAdapter()
    rospy.spin()


if __name__ == "__main__":
    main()
