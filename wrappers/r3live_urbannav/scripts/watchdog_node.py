#!/usr/bin/env python3
"""Watchdog for R3LIVE — logs to tmux if sensors or odometry go silent."""
import time
import rospy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image


class Watchdog:
    def __init__(self):
        self.period = float(rospy.get_param('~period', 3.0))
        self.odom_topic = rospy.get_param('~odom_topic', '/r3live/odometry/mapping')
        self.lidar_topic = rospy.get_param('~lidar_topic', '/livox/lidar')
        self.camera_topic = rospy.get_param('~camera_topic', '/camera/image_raw')
        self.last = {'odom': 0.0, 'lidar': 0.0, 'camera': 0.0}
        rospy.Subscriber(self.odom_topic, Odometry, lambda _: self.last.update({'odom': time.monotonic()}))
        rospy.Subscriber(self.lidar_topic, rospy.AnyMsg, lambda _: self.last.update({'lidar': time.monotonic()}))
        rospy.Subscriber(self.camera_topic, Image, lambda _: self.last.update({'camera': time.monotonic()}))
        rospy.Timer(rospy.Duration(self.period), self._check)
        rospy.loginfo('[R3LIVE Watchdog] monitoring odom=%s lidar=%s camera=%s',
                      self.odom_topic, self.lidar_topic, self.camera_topic)

    def _check(self, _event):
        now = time.monotonic()
        for name, last_t in self.last.items():
            age = now - last_t
            if last_t == 0.0:
                rospy.logwarn_throttle(10.0, '[R3LIVE Watchdog] %s: no messages yet', name)
            elif age > self.period * 2:
                rospy.logwarn_throttle(10.0, '[R3LIVE Watchdog] %s: stale (%.1f s ago)', name, age)


def main():
    rospy.init_node('r3live_watchdog', anonymous=False)
    Watchdog()
    rospy.spin()


if __name__ == '__main__':
    main()
