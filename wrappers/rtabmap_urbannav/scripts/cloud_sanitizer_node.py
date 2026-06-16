#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import PointCloud2
from nav_msgs.msg import Odometry

class CloudSanitizer:
    def __init__(self):
        self.input_topic = rospy.get_param('~input_topic', '/cloud_registered_raw')
        self.output_topic = rospy.get_param('~output_topic', '/rtabmap/cloud_registered')
        self.frame_id = rospy.get_param('~frame_id', '')
        self.min_odom_topic = rospy.get_param('~min_odom_topic', '')
        self.drop_until_first_odom = bool(rospy.get_param('~drop_until_first_odom', True))
        self.first_odom_stamp = None
        self.dropped_early = 0
        self.pub = rospy.Publisher(self.output_topic, PointCloud2, queue_size=5)
        if self.min_odom_topic:
            rospy.Subscriber(self.min_odom_topic, Odometry, self.odom_cb, queue_size=20)
        rospy.Subscriber(self.input_topic, PointCloud2, self.cb, queue_size=5)
        rospy.loginfo('[CloudSanitizer] %s -> %s frame_override=%s odom_gate=%s',
                      self.input_topic, self.output_topic, self.frame_id or 'none', self.min_odom_topic or 'off')

    def odom_cb(self, msg):
        if self.first_odom_stamp is None and msg.header.stamp != rospy.Time(0):
            self.first_odom_stamp = msg.header.stamp
            rospy.loginfo('[CloudSanitizer] first odom gate stamp=%.9f dropped_early_clouds=%d',
                          self.first_odom_stamp.to_sec(), self.dropped_early)

    def cb(self, msg):
        if self.drop_until_first_odom and self.min_odom_topic:
            if self.first_odom_stamp is None:
                self.dropped_early += 1
                return
            if msg.header.stamp != rospy.Time(0) and msg.header.stamp < self.first_odom_stamp:
                self.dropped_early += 1
                return
        out = PointCloud2()
        out.header = msg.header
        if self.frame_id:
            out.header.frame_id = self.frame_id
        out.height = msg.height or 1
        out.width = msg.width
        out.fields = msg.fields
        out.is_bigendian = msg.is_bigendian
        out.point_step = msg.point_step
        out.row_step = msg.row_step
        if out.point_step and out.width and (not out.row_step or out.row_step != out.point_step * out.width):
            out.row_step = out.point_step * out.width
        out.data = msg.data
        out.is_dense = False
        self.pub.publish(out)

if __name__ == '__main__':
    rospy.init_node('cloud_sanitizer_node')
    CloudSanitizer()
    rospy.spin()
