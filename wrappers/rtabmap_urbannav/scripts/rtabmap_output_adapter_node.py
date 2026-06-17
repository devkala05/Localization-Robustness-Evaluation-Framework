#!/usr/bin/env python3
"""Publish benchmark odometry from RTAB-Map's optimized path.

The RTAB-Map wrapper now runs standalone LiDAR ICP odometry:

    /cloud_registered_raw -> /rtabmap/scan_cloud -> icp_odometry -> /rtabmap/icp_odom -> rtabmap

This node converts RTAB-Map's own optimized mapPath output into the standardized
benchmark odometry/path topics. It does not read FAST-LIO2 /Odometry.
"""
import rospy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry, Path


class RtabmapOutputAdapter:
    def __init__(self):
        self.input_path_topic = rospy.get_param('~input_path_topic', '/rtabmap/mapPath')
        self.output_odom_topic = rospy.get_param('~output_odom_topic', '/rtabmap/odometry/mapping')
        self.output_path_topic = rospy.get_param('~output_path_topic', '/rtabmap/mapping/path')
        self.child_frame_id = rospy.get_param('~child_frame_id', 'body')
        self.max_path_length = int(rospy.get_param('~max_path_length', 200000))
        self.pub_odom = rospy.Publisher(self.output_odom_topic, Odometry, queue_size=50)
        self.pub_path = rospy.Publisher(self.output_path_topic, Path, queue_size=10, latch=True)
        self.path = Path()
        self.count = 0
        rospy.Subscriber(self.input_path_topic, Path, self.path_cb, queue_size=10)
        rospy.loginfo('[RTAB-Map OutputAdapter] %s -> odom=%s path=%s', self.input_path_topic, self.output_odom_topic, self.output_path_topic)

    def path_cb(self, msg: Path):
        if not msg.poses:
            return
        pose_stamped: PoseStamped = msg.poses[-1]
        stamp = pose_stamped.header.stamp if pose_stamped.header.stamp != rospy.Time(0) else msg.header.stamp
        if stamp == rospy.Time(0):
            stamp = rospy.Time.now()
        frame_id = pose_stamped.header.frame_id or msg.header.frame_id or 'map'

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = frame_id
        odom.child_frame_id = self.child_frame_id
        odom.pose.pose = pose_stamped.pose
        self.pub_odom.publish(odom)

        self.path.header.stamp = stamp
        self.path.header.frame_id = frame_id
        self.path.poses = list(msg.poses[-self.max_path_length:]) if self.max_path_length > 0 else list(msg.poses)
        self.pub_path.publish(self.path)
        self.count += 1
        if self.count == 1:
            rospy.loginfo('[RTAB-Map OutputAdapter] first RTAB-Map optimized pose at %.9f frame=%s', stamp.to_sec(), frame_id)


def main():
    rospy.init_node('rtabmap_output_adapter_node', anonymous=False)
    RtabmapOutputAdapter()
    rospy.spin()


if __name__ == '__main__':
    main()
