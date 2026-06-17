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

def as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)

class StandardOutputRepublisher:
    def __init__(self):
        self.source_topic = rospy.get_param('~source_topic')
        self.algo_ns = rospy.get_param('~algo_ns', 'algorithm')
        self.local_odom_topic = rospy.get_param('~local_odom_topic', f'/{self.algo_ns}/odometry/local')
        self.local_path_topic = rospy.get_param('~local_path_topic', f'/{self.algo_ns}/path/local')
        self.output_odom_topic = rospy.get_param('~output_odom_topic', f'/{self.algo_ns}/odometry/output')
        self.output_path_topic = rospy.get_param('~output_path_topic', f'/{self.algo_ns}/path/output')
        self.status_topic = rospy.get_param('~status_topic', f'/{self.algo_ns}/benchmark_status')
        self.gps_enabled = as_bool(rospy.get_param('~gps_enabled', False))
        self.fixed_frame = rospy.get_param('~fixed_frame', 'camera_init')
        self.child_frame = rospy.get_param('~child_frame', 'body')
        self.publish_tf = as_bool(rospy.get_param('~publish_tf', True))
        self.tf_parent_frame = rospy.get_param('~tf_parent_frame', '')
        self.tf_child_frame = rospy.get_param('~tf_child_frame', self.child_frame)
        self.preserve_native_child_frame = as_bool(rospy.get_param('~preserve_native_child_frame', False))
        self.rebase_origin = as_bool(rospy.get_param('~rebase_origin', False))
        self.align_to_gt = as_bool(rospy.get_param('~align_to_gt', False))
        self.ground_truth_odom_topic = rospy.get_param('~ground_truth_odom_topic', '/ground_truth_odometry')
        self.align_min_motion = float(rospy.get_param('~align_min_motion', 1.0))
        self.use_motion_yaw = as_bool(rospy.get_param('~use_motion_yaw', False))
        self.origin_min_norm = float(rospy.get_param('~origin_min_norm', 0.0))
        self.origin = None
        self.gt_origin = None
        self.latest_gt = None
        self.align_ready = False
        self.align_yaw_delta = 0.0
        self.align_native_anchor = None
        self.align_gt_anchor = None
        self.last_motion_xy = None
        self.last_motion_yaw = None
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
        if self.align_to_gt:
            rospy.Subscriber(self.ground_truth_odom_topic, Odometry, self.gt_cb, queue_size=100)
        self.status_pub.publish(String(data='waiting_for_native_odometry'))
        rospy.loginfo('[BenchmarkOutput] source=%s local=%s output=%s gps=%s tf=%s', self.source_topic, self.local_odom_topic, self.output_odom_topic, self.gps_enabled, self.publish_tf)

    def gt_cb(self, msg):
        self.latest_gt = msg

    def maybe_rebase(self, odom):
        if not self.rebase_origin and not self.align_to_gt:
            return odom
        p = odom.pose.pose.position
        q = odom.pose.pose.orientation
        pose_norm = math.sqrt(p.x * p.x + p.y * p.y + p.z * p.z)
        if self.origin is None:
            if self.align_to_gt and self.latest_gt is None:
                return None
            if pose_norm < self.origin_min_norm:
                return None
            self.origin = (p.x, p.y, p.z, yaw_from_quaternion(q))
            if self.align_to_gt:
                gp = self.latest_gt.pose.pose.position
                gq = self.latest_gt.pose.pose.orientation
                self.gt_origin = (gp.x, gp.y, gp.z, yaw_from_quaternion(gq))
                self.align_ready = self.align_min_motion <= 0.0
                self.align_yaw_delta = self.gt_origin[3] - self.origin[3]
            rospy.loginfo(
                '[BenchmarkOutput] aligning origin at stamp=%.9f xyz=(%.3f, %.3f, %.3f) yaw=%.3f gt=%s',
                odom.header.stamp.to_sec(), p.x, p.y, p.z, self.origin[3],
                'yes' if self.align_to_gt else 'no',
            )
        ox, oy, oz, oyaw = self.origin
        dx = p.x - ox
        dy = p.y - oy
        dz = p.z - oz
        if self.align_to_gt and self.gt_origin is not None:
            gx, gy, gz, gyaw = self.gt_origin
            if not self.align_ready:
                gp = self.latest_gt.pose.pose.position if self.latest_gt is not None else None
                if gp is None:
                    return None
                nd = math.sqrt(dx * dx + dy * dy)
                gdx = gp.x - gx
                gdy = gp.y - gy
                gd = math.sqrt(gdx * gdx + gdy * gdy)
                if nd < self.align_min_motion or gd < self.align_min_motion:
                    return None
                self.align_yaw_delta = math.atan2(gdy, gdx) - math.atan2(dy, dx)
                gq = self.latest_gt.pose.pose.orientation
                self.align_native_anchor = (p.x, p.y, p.z)
                self.align_gt_anchor = (gp.x, gp.y, gp.z, yaw_from_quaternion(gq))
                self.last_motion_xy = None
                self.last_motion_yaw = self.align_gt_anchor[3]
                self.align_ready = True
                rospy.loginfo(
                    '[BenchmarkOutput] motion yaw alignment ready native_motion=%.3f gt_motion=%.3f yaw_delta=%.2f deg',
                    nd, gd, math.degrees(self.align_yaw_delta),
                )
            if self.align_native_anchor is None or self.align_gt_anchor is None:
                self.align_native_anchor = (ox, oy, oz)
                self.align_gt_anchor = (gx, gy, gz, gyaw)
            ax, ay, az = self.align_native_anchor
            gx, gy, gz, gyaw = self.align_gt_anchor
            dx = p.x - ax
            dy = p.y - ay
            dz = p.z - az
            yaw_delta = self.align_yaw_delta
            c = math.cos(yaw_delta)
            s = math.sin(yaw_delta)
            odom.pose.pose.position.x = gx + c * dx - s * dy
            odom.pose.pose.position.y = gy + s * dx + c * dy
            odom.pose.pose.position.z = gz + dz
            if self.use_motion_yaw:
                xy = (odom.pose.pose.position.x, odom.pose.pose.position.y)
                if self.last_motion_xy is not None:
                    mdx = xy[0] - self.last_motion_xy[0]
                    mdy = xy[1] - self.last_motion_xy[1]
                    if math.sqrt(mdx * mdx + mdy * mdy) >= self.min_path_step:
                        self.last_motion_yaw = math.atan2(mdy, mdx)
                odom.pose.pose.orientation = yaw_quaternion(self.last_motion_yaw if self.last_motion_yaw is not None else gyaw)
                self.last_motion_xy = xy
            else:
                odom.pose.pose.orientation = yaw_quaternion(yaw_from_quaternion(q) + yaw_delta)
        else:
            c = math.cos(-oyaw)
            s = math.sin(-oyaw)
            odom.pose.pose.position.x = c * dx - s * dy
            odom.pose.pose.position.y = s * dx + c * dy
            odom.pose.pose.position.z = dz
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
        if self.rebase_origin or self.align_to_gt:
            out.header.frame_id = self.fixed_frame
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
