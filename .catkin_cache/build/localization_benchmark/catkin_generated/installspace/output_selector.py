#!/usr/bin/env python3
"""Select local or GPS-fused odometry for the benchmark recorder."""
import math
import time
import rospy
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String

def pose_dist(a,b):
    dx=a.pose.position.x-b.pose.position.x; dy=a.pose.position.y-b.pose.position.y; dz=a.pose.position.z-b.pose.position.z
    return math.sqrt(dx*dx+dy*dy+dz*dz)

class OutputSelector:
    def __init__(self):
        self.algo_ns = rospy.get_param('~algo_ns', 'algorithm')
        self.gps_enabled = bool(rospy.get_param('~gps_enabled', False))
        self.local_topic = rospy.get_param('~local_odom_topic', f'/{self.algo_ns}/odometry/local')
        self.gps_topic = rospy.get_param('~gps_odom_topic', f'/{self.algo_ns}/odometry/gps_fused')
        self.output_topic = rospy.get_param('~output_odom_topic', f'/{self.algo_ns}/odometry/output')
        self.output_path_topic = rospy.get_param('~output_path_topic', f'/{self.algo_ns}/path/output')
        self.status_topic = rospy.get_param('~status_topic', f'/{self.algo_ns}/status')
        self.gps_timeout = float(rospy.get_param('~gps_timeout_sec', 2.0))
        self.min_path_step = float(rospy.get_param('~min_path_step', 0.02))
        self.max_poses = int(rospy.get_param('~max_poses', 300000))
        self.pub = rospy.Publisher(self.output_topic, Odometry, queue_size=100)
        self.path_pub = rospy.Publisher(self.output_path_topic, Path, queue_size=10, latch=True)
        self.status_pub = rospy.Publisher(self.status_topic, String, queue_size=10, latch=True)
        self.path = Path(); self.path.header.frame_id='camera_init'
        self.last_pose=None
        self.last_gps_odom=None; self.last_gps_wall=0.0
        rospy.Subscriber(self.local_topic, Odometry, self.local_cb, queue_size=100)
        if self.gps_enabled:
            rospy.Subscriber(self.gps_topic, Odometry, self.gps_cb, queue_size=100)
        rospy.loginfo('[OutputSelector] gps_enabled=%s local=%s gps=%s output=%s', self.gps_enabled, self.local_topic, self.gps_topic, self.output_topic)

    def gps_cb(self,msg):
        self.last_gps_odom=msg; self.last_gps_wall=time.monotonic()

    def publish(self,msg,source):
        self.pub.publish(msg)
        pose=PoseStamped(); pose.header=msg.header; pose.pose=msg.pose.pose
        if self.last_pose is None or pose_dist(self.last_pose, pose)>=self.min_path_step:
            self.path.header.frame_id=pose.header.frame_id or 'camera_init'; self.path.header.stamp=pose.header.stamp
            self.path.poses.append(pose)
            if len(self.path.poses)>self.max_poses: self.path.poses=self.path.poses[-self.max_poses:]
            self.path_pub.publish(self.path)
            self.last_pose=pose
        self.status_pub.publish(String(data=source))

    def local_cb(self,msg):
        if self.gps_enabled and self.last_gps_odom is not None and time.monotonic()-self.last_gps_wall<=self.gps_timeout:
            self.publish(self.last_gps_odom, 'output=gps_fused')
        else:
            self.publish(msg, 'output=local_fallback' if self.gps_enabled else 'output=local')

if __name__ == '__main__':
    rospy.init_node('output_selector')
    OutputSelector()
    rospy.spin()
