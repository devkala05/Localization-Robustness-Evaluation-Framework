#!/usr/bin/env python3
"""Robust R3LIVE trajectory publisher.

R3LIVE publishes the live body pose as TF (camera_init -> body) from its LIO
subsystem. Some builds also publish /r3live/odometry or /Odometry.
This node makes output deterministic: uses odometry when available, falls back
to TF when odometry is absent or stale.

Publishes:
    /r3live/odometry/mapping    nav_msgs/Odometry
    /r3live/mapping/path        nav_msgs/Path
"""

import math
import time
from typing import List, Optional, Tuple

import rospy
import tf2_ros
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Odometry, Path


def _split_topics(text: str) -> List[str]:
    return [t.strip() for t in text.split(',') if t.strip()]


def _split_tf_pairs(text: str) -> List[Tuple[str, str]]:
    pairs = []
    for item in text.split(','):
        item = item.strip()
        if not item:
            continue
        if ':' in item:
            parent, child = item.split(':', 1)
        elif '->' in item:
            parent, child = item.split('->', 1)
        else:
            continue
        parent = parent.strip()
        child = child.strip()
        if parent and child:
            pairs.append((parent, child))
    return pairs


def _pose_distance(a: PoseStamped, b: PoseStamped) -> float:
    dx = a.pose.position.x - b.pose.position.x
    dy = a.pose.position.y - b.pose.position.y
    dz = a.pose.position.z - b.pose.position.z
    return math.sqrt(dx*dx + dy*dy + dz*dz)


def _pose_from_transform(ts: TransformStamped) -> PoseStamped:
    pose = PoseStamped()
    pose.header.stamp = ts.header.stamp if ts.header.stamp != rospy.Time(0) else rospy.Time.now()
    pose.header.frame_id = ts.header.frame_id
    pose.pose.position.x = ts.transform.translation.x
    pose.pose.position.y = ts.transform.translation.y
    pose.pose.position.z = ts.transform.translation.z
    pose.pose.orientation = ts.transform.rotation
    return pose


def _odom_from_pose(pose: PoseStamped, child_frame_id: str) -> Odometry:
    odom = Odometry()
    odom.header = pose.header
    odom.child_frame_id = child_frame_id
    odom.pose.pose = pose.pose
    return odom


class TrajectoryMux:
    def __init__(self):
        topics_text = rospy.get_param('~odom_topics', '/r3live/odometry,/Odometry')
        self.odom_topics = _split_topics(topics_text)
        self.output_odom_topic = rospy.get_param('~output_odom_topic', '/r3live/odometry/mapping')
        self.output_path_topic = rospy.get_param('~output_path_topic', '/r3live/mapping/path')
        self.fixed_frame = rospy.get_param('~fixed_frame', 'camera_init')
        self.child_frame = rospy.get_param('~child_frame', 'body')
        # Accept several upstream TF conventions. Official/forked R3LIVE builds
        # may use camera_init->body, camera_init->base_link, or map->body.
        tf_pairs_text = rospy.get_param('~tf_pairs', '')
        self.tf_pairs = _split_tf_pairs(tf_pairs_text)
        self.tf_parent = rospy.get_param('~tf_parent', 'camera_init')
        self.tf_child = rospy.get_param('~tf_child', 'body')
        if not self.tf_pairs:
            self.tf_pairs = [(self.tf_parent, self.tf_child)]
        self.use_tf_fallback = bool(rospy.get_param('~use_tf_fallback', True))
        self.odom_stale_sec = float(rospy.get_param('~odom_stale_sec', 0.75))
        self.publish_rate = float(rospy.get_param('~publish_rate', 20.0))
        self.min_path_step = float(rospy.get_param('~min_path_step', 0.02))
        self.max_poses = int(rospy.get_param('~max_poses', 300000))

        self.path = Path()
        self.path.header.frame_id = self.fixed_frame
        self.last_odom_wall = 0.0
        self.odom_count = 0
        self.tf_count = 0
        self.last_pose: Optional[PoseStamped] = None
        self.first_source = None
        self.last_warn = 0.0

        self.odom_pub = rospy.Publisher(self.output_odom_topic, Odometry, queue_size=100)
        self.path_pub = rospy.Publisher(self.output_path_topic, Path, queue_size=10, latch=True)

        for topic in self.odom_topics:
            rospy.Subscriber(topic, Odometry, self._odom_cb, callback_args=topic, queue_size=100)

        self.tf_buffer = tf2_ros.Buffer(cache_time=rospy.Duration(30.0))
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)
        if self.use_tf_fallback:
            rospy.Timer(rospy.Duration(1.0 / max(1.0, self.publish_rate)), self._tf_timer)

        rospy.loginfo('[R3LIVE TrajectoryMux] odom topics=%s', ', '.join(self.odom_topics))
        rospy.loginfo('[R3LIVE TrajectoryMux] output odom=%s path=%s', self.output_odom_topic, self.output_path_topic)
        rospy.loginfo('[R3LIVE TrajectoryMux] TF fallback %s: %s',
                      'ON' if self.use_tf_fallback else 'OFF',
                      ', '.join('%s->%s' % p for p in self.tf_pairs))

    def _append_publish(self, pose: PoseStamped, odom: Odometry, source: str):
        if not pose.header.frame_id:
            pose.header.frame_id = self.fixed_frame
            odom.header.frame_id = self.fixed_frame
        self.odom_pub.publish(odom)
        should_append = (self.last_pose is None or
                         _pose_distance(self.last_pose, pose) >= self.min_path_step)
        if should_append:
            self.path.header.frame_id = pose.header.frame_id
            self.path.header.stamp = pose.header.stamp
            self.path.poses.append(pose)
            if len(self.path.poses) > self.max_poses:
                self.path.poses = self.path.poses[-self.max_poses:]
            self.path_pub.publish(self.path)
            self.last_pose = pose
        if self.first_source is None:
            self.first_source = source
            rospy.loginfo('[R3LIVE TrajectoryMux] first pose from %s', source)

    def _odom_cb(self, msg: Odometry, topic: str):
        self.last_odom_wall = time.monotonic()
        self.odom_count += 1
        odom = Odometry()
        odom.header = msg.header
        if not odom.header.frame_id:
            odom.header.frame_id = self.fixed_frame
        odom.child_frame_id = msg.child_frame_id or self.child_frame
        odom.pose = msg.pose
        odom.twist = msg.twist
        pose = PoseStamped()
        pose.header = odom.header
        pose.pose = odom.pose.pose
        self._append_publish(pose, odom, f'odometry:{topic}')
        if self.odom_count == 1:
            rospy.loginfo('[R3LIVE TrajectoryMux] receiving odometry from %s', topic)

    def _tf_timer(self, _event):
        if time.monotonic() - self.last_odom_wall <= self.odom_stale_sec:
            return
        ts = None
        used_pair = None
        last_exc = None
        for parent, child in self.tf_pairs:
            try:
                ts = self.tf_buffer.lookup_transform(parent, child, rospy.Time(0), rospy.Duration(0.01))
                used_pair = (parent, child)
                break
            except Exception as exc:
                last_exc = exc
        if ts is None:
            now = time.monotonic()
            if now - self.last_warn > 5.0:
                rospy.logwarn('[R3LIVE TrajectoryMux] waiting for odom or TF among [%s] (%s)',
                              ', '.join('%s->%s' % p for p in self.tf_pairs), last_exc)
                self.last_warn = now
            return
        pose = _pose_from_transform(ts)
        odom = _odom_from_pose(pose, used_pair[1])
        self.tf_count += 1
        self._append_publish(pose, odom, f'tf:{used_pair[0]}->{used_pair[1]}')
        if self.tf_count == 1:
            rospy.logwarn('[R3LIVE TrajectoryMux] no odometry yet; using TF %s->%s',
                          used_pair[0], used_pair[1])


def main():
    rospy.init_node('r3live_trajectory_mux', anonymous=False)
    TrajectoryMux()
    rospy.spin()


if __name__ == '__main__':
    main()
