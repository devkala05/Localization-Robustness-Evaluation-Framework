#!/usr/bin/env python3
"""Normalize native algorithm odometry into the benchmark topic contract.

Publishes:
  /<algo>/odometry/local
  /<algo>/path/local
  /<algo>/odometry/output and /<algo>/path/output when GPS is disabled

When GPS is enabled, output_selector.py owns /<algo>/odometry/output.
"""
import math
import time
import rospy
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped, TransformStamped
import tf2_ros
from std_msgs.msg import String


def dist(a, b):
    dx=a.pose.position.x-b.pose.position.x; dy=a.pose.position.y-b.pose.position.y; dz=a.pose.position.z-b.pose.position.z
    return math.sqrt(dx*dx+dy*dy+dz*dz)

def yaw_from_quaternion(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))

def yaw_quaternion(yaw):
    from geometry_msgs.msg import Quaternion
    q = Quaternion()
    q.w = math.cos(0.5 * yaw)
    q.z = math.sin(0.5 * yaw)
    return q

class StandardOutputRepublisher:
    def __init__(self):
        self.source_topic = rospy.get_param('~source_topic')
        self.algo_ns = rospy.get_param('~algo_ns', 'algorithm')
        self.local_odom_topic = rospy.get_param('~local_odom_topic', f'/{self.algo_ns}/odometry/local')
        self.local_path_topic = rospy.get_param('~local_path_topic', f'/{self.algo_ns}/path/local')
        self.output_odom_topic = rospy.get_param('~output_odom_topic', f'/{self.algo_ns}/odometry/output')
        self.output_path_topic = rospy.get_param('~output_path_topic', f'/{self.algo_ns}/path/output')
        self.status_topic = rospy.get_param('~status_topic', f'/{self.algo_ns}/benchmark_status')
        self.gps_enabled = bool(rospy.get_param('~gps_enabled', False))
        self.fixed_frame = rospy.get_param('~fixed_frame', 'camera_init')
        self.child_frame = rospy.get_param('~child_frame', 'body')
        self.publish_tf = bool(rospy.get_param('~publish_tf', True))
        self.tf_parent_frame = rospy.get_param('~tf_parent_frame', '')
        self.tf_child_frame = rospy.get_param('~tf_child_frame', self.child_frame)
        self.preserve_native_child_frame = bool(rospy.get_param('~preserve_native_child_frame', False))
        self.rebase_origin = bool(rospy.get_param('~rebase_origin', False))
        self.origin_min_norm = float(rospy.get_param('~origin_min_norm', 0.0))
        self.origin = None
        self.tf_broadcaster = tf2_ros.TransformBroadcaster() if self.publish_tf else None
        self.last_tf_stamp_by_edge = {}
        self.min_path_step = float(rospy.get_param('~min_path_step', 0.02))
        self.max_poses = int(rospy.get_param('~max_poses', 300000))
        self.local_pub = rospy.Publisher(self.local_odom_topic, Odometry, queue_size=100)
        self.local_path_pub = rospy.Publisher(self.local_path_topic, Path, queue_size=10, latch=True)
        self.status_pub = rospy.Publisher(self.status_topic, String, queue_size=5, latch=True)
        self.output_pub = None if self.gps_enabled else rospy.Publisher(self.output_odom_topic, Odometry, queue_size=100)
        self.output_path_pub = None if self.gps_enabled else rospy.Publisher(self.output_path_topic, Path, queue_size=10, latch=True)
        self.path = Path(); self.path.header.frame_id = self.fixed_frame
        self.output_path = Path(); self.output_path.header.frame_id = self.fixed_frame
        self.last_pose = None
        self.count = 0
        self.last_log = 0.0
        rospy.Subscriber(self.source_topic, Odometry, self.cb, queue_size=200)
        self.status_pub.publish(String(data='waiting_for_native_odometry'))
        rospy.loginfo('[BenchmarkOutput] source=%s local=%s output=%s gps=%s tf=%s', self.source_topic, self.local_odom_topic, self.output_odom_topic, self.gps_enabled, self.publish_tf)

    def maybe_rebase(self, odom):
        if not self.rebase_origin:
            return odom
        p = odom.pose.pose.position
        q = odom.pose.pose.orientation
        pose_norm = math.sqrt(p.x * p.x + p.y * p.y + p.z * p.z)
        if self.origin is None:
            if pose_norm < self.origin_min_norm:
                return None
            self.origin = (p.x, p.y, p.z, yaw_from_quaternion(q))
            rospy.loginfo(
                '[BenchmarkOutput] rebasing origin at stamp=%.9f xyz=(%.3f, %.3f, %.3f) yaw=%.3f',
                odom.header.stamp.to_sec(), p.x, p.y, p.z, self.origin[3],
            )
        ox, oy, oz, oyaw = self.origin
        dx = p.x - ox
        dy = p.y - oy
        c = math.cos(-oyaw)
        s = math.sin(-oyaw)
        odom.pose.pose.position.x = c * dx - s * dy
        odom.pose.pose.position.y = s * dx + c * dy
        odom.pose.pose.position.z = p.z - oz
        odom.pose.pose.orientation = yaw_quaternion(yaw_from_quaternion(q) - oyaw)
        return odom

    def publish_local_tf(self, odom):
        # robot_localization/navsat_transform needs a real TF link between the
        # local odom frame and the benchmark body frame. Native algorithms often
        # publish Odometry messages without publishing exactly odom->body.
        parent = self.tf_parent_frame or odom.header.frame_id or self.fixed_frame
        child = self.tf_child_frame or odom.child_frame_id or self.child_frame
        if not parent or not child or parent == child:
            return
        stamp_ns = odom.header.stamp.to_nsec()
        edge = (parent, child)
        last_ns = self.last_tf_stamp_by_edge.get(edge)
        if last_ns is not None and stamp_ns <= last_ns:
            return
        self.last_tf_stamp_by_edge[edge] = stamp_ns
        t = TransformStamped()
        t.header.stamp = odom.header.stamp
        t.header.frame_id = parent
        t.child_frame_id = child
        t.transform.translation.x = odom.pose.pose.position.x
        t.transform.translation.y = odom.pose.pose.position.y
        t.transform.translation.z = odom.pose.pose.position.z
        t.transform.rotation = odom.pose.pose.orientation
        self.tf_broadcaster.sendTransform(t)

    def cb(self, msg):
        out = Odometry()
        out.header = msg.header
        if not out.header.frame_id:
            out.header.frame_id = self.fixed_frame
        out.child_frame_id = msg.child_frame_id if self.preserve_native_child_frame else self.child_frame
        if not out.child_frame_id:
            out.child_frame_id = self.child_frame
        out.pose = msg.pose
        out.twist = msg.twist
        out = self.maybe_rebase(out)
        if out is None:
            return
        self.local_pub.publish(out)
        if self.publish_tf:
            self.publish_local_tf(out)
        pose = PoseStamped(); pose.header = out.header; pose.pose = out.pose.pose
        if self.last_pose is None or dist(self.last_pose, pose) >= self.min_path_step:
            self.path.header.frame_id = pose.header.frame_id or self.fixed_frame
            self.path.header.stamp = pose.header.stamp
            self.path.poses.append(pose)
            if len(self.path.poses) > self.max_poses:
                self.path.poses = self.path.poses[-self.max_poses:]
            self.local_path_pub.publish(self.path)
            self.last_pose = pose
        if not self.gps_enabled:
            self.output_pub.publish(out)
            self.output_path.header = self.path.header
            self.output_path.poses = list(self.path.poses)
            self.output_path_pub.publish(self.output_path)
        self.count += 1
        if self.count == 1:
            self.status_pub.publish(String(data='local_output_active'))
            rospy.loginfo('[BenchmarkOutput] first_odometry source=%s stamp=%.9f frame=%s child=%s', self.source_topic, out.header.stamp.to_sec(), out.header.frame_id, out.child_frame_id)
        now=time.monotonic()
        if now-self.last_log>10.0:
            self.status_pub.publish(String(data=f'local_output_active count={self.count} gps_enabled={self.gps_enabled}'))
            self.last_log=now

if __name__ == '__main__':
    rospy.init_node('standard_output_republisher')
    StandardOutputRepublisher()
    rospy.spin()
