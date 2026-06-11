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
  /rtabmap/odometry/mapping nav_msgs/Odometry for benchmark recorder
  /rtabmap/mapping/path     nav_msgs/Path for RViz
  odom -> base_link         dynamic TF, optional and enabled by default
"""

import rospy
import tf2_ros
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry, Path
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
        self.benchmark_odom_topic = rospy.get_param("~benchmark_odom_topic", "/rtabmap/odometry/mapping")
        self.path_topic = rospy.get_param("~path_topic", "/rtabmap/mapping/path")
        self.odom_frame_id = rospy.get_param("~odom_frame_id", "odom")
        self.map_frame_id = rospy.get_param("~map_frame_id", "map")
        self.base_frame_id = rospy.get_param("~base_frame_id", "base_link")
        self.publish_tf = bool(rospy.get_param("~publish_tf", True))
        self.apply_rtabmap_tf = bool(rospy.get_param("~apply_rtabmap_tf", True))
        self.max_path_length = int(rospy.get_param("~max_path_length", 200000))

        self.tf_buffer = tf2_ros.Buffer(cache_time=rospy.Duration(30.0))
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

        self.pub_input = rospy.Publisher(self.rtabmap_odom_topic, Odometry, queue_size=100)
        self.pub_benchmark = rospy.Publisher(self.benchmark_odom_topic, Odometry, queue_size=100)
        self.pub_path = rospy.Publisher(self.path_topic, Path, queue_size=10, latch=True)
        self.path = Path()
        self.path.header.frame_id = self.map_frame_id
        self.tf_broadcaster = tf2_ros.TransformBroadcaster() if self.publish_tf else None
        self.count = 0

        rospy.Subscriber(self.input_odom_topic, Odometry, self.odom_cb, queue_size=200)
        rospy.loginfo(
            "[RTAB-Map Adapter] %s -> %s and %s, frames odom=%s map=%s base=%s",
            self.input_odom_topic,
            self.rtabmap_odom_topic,
            self.benchmark_odom_topic,
            self.odom_frame_id,
            self.map_frame_id,
            self.base_frame_id,
        )

    def odom_cb(self, msg: Odometry):
        stamp = msg.header.stamp if msg.header.stamp != rospy.Time(0) else rospy.Time.now()

        # Odometry consumed by RTAB-Map. Keep FAST-LIO2 pose numeric values, but
        # expose the standard RTAB-Map odom -> base_link frame names.
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

        # Benchmark output. When RTAB-Map has published a map -> odom
        # correction, apply it so the recorded trajectory follows RTAB-Map's
        # optimized map frame. Before the first correction arrives, this is just
        # the FAST-LIO2 frontend pose in the map frame.
        benchmark_odom = Odometry()
        benchmark_odom.header.stamp = stamp
        benchmark_odom.header.frame_id = self.map_frame_id
        benchmark_odom.child_frame_id = self.base_frame_id
        benchmark_odom.pose = msg.pose
        benchmark_odom.twist = msg.twist
        if self.apply_rtabmap_tf:
            try:
                correction = self.tf_buffer.lookup_transform(
                    self.map_frame_id,
                    self.odom_frame_id,
                    rospy.Time(0),
                    rospy.Duration(0.001),
                )
                benchmark_odom.pose.pose = self._transform_pose(correction, msg.pose.pose)
            except Exception:
                pass
        self.pub_benchmark.publish(benchmark_odom)

        pose = benchmark_odom.pose.pose
        pose_stamped = self._pose_stamped(stamp, pose)
        self.path.header.stamp = stamp
        self.path.poses.append(pose_stamped)
        if self.max_path_length > 0 and len(self.path.poses) > self.max_path_length:
            self.path.poses = self.path.poses[-self.max_path_length:]
        self.pub_path.publish(self.path)

        self.count += 1
        if self.count == 1:
            rospy.loginfo("[RTAB-Map Adapter] first odometry received at %.9f", stamp.to_sec())

    def _pose_stamped(self, stamp, pose):
        from geometry_msgs.msg import PoseStamped
        out = PoseStamped()
        out.header.stamp = stamp
        out.header.frame_id = self.map_frame_id
        out.pose = pose
        return out

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
