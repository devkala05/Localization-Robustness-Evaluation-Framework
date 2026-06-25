#!/usr/bin/env python3
"""Republish FAST-LIVO2 odometry under one stable benchmark topic.

Some FAST-LIVO2 builds publish nav_msgs/Odometry on /Odometry, while others
publish /aft_mapped_to_init. This small wrapper keeps the upstream algorithm
unchanged and exposes a single topic for the benchmark recorder.
"""
import time

import rospy
from nav_msgs.msg import Odometry


class OdometryAliasNode:
    def __init__(self):
        self.preferred_topic = rospy.get_param("~preferred_topic", "/Odometry")
        self.fallback_topic = rospy.get_param("~fallback_topic", "/aft_mapped_to_init")
        self.output_topic = rospy.get_param("~output_topic", "/fast_livo2/odometry")
        self.preferred_timeout = float(rospy.get_param("~preferred_timeout", 1.0))
        self.last_preferred_wall = 0.0
        self.count_preferred = 0
        self.count_fallback = 0
        self.last_published_stamp = None
        self.pub = rospy.Publisher(self.output_topic, Odometry, queue_size=100)
        rospy.Subscriber(self.preferred_topic, Odometry, self.preferred_cb, queue_size=100)
        if self.fallback_topic != self.preferred_topic:
            rospy.Subscriber(self.fallback_topic, Odometry, self.fallback_cb, queue_size=100)
        rospy.loginfo(
            "[FASTLIVO2 OdomAlias] preferred=%s fallback=%s -> %s",
            self.preferred_topic,
            self.fallback_topic,
            self.output_topic,
        )

    def preferred_cb(self, msg):
        self.last_preferred_wall = time.monotonic()
        self.count_preferred += 1
        self.publish_if_monotonic(msg)
        if self.count_preferred == 1:
            rospy.loginfo("[FASTLIVO2 OdomAlias] first preferred odometry from %s", self.preferred_topic)

    def fallback_cb(self, msg):
        if time.monotonic() - self.last_preferred_wall <= self.preferred_timeout:
            return
        self.count_fallback += 1
        self.publish_if_monotonic(msg)
        if self.count_fallback == 1:
            rospy.logwarn("[FASTLIVO2 OdomAlias] using fallback odometry from %s", self.fallback_topic)

    def publish_if_monotonic(self, msg):
        stamp = msg.header.stamp.to_sec()
        if stamp <= 0.0:
            rospy.logwarn_throttle(2.0, "[FASTLIVO2 OdomAlias] dropping zero timestamp")
            return
        if self.last_published_stamp is not None and stamp <= self.last_published_stamp:
            rospy.logwarn_throttle(2.0, "[FASTLIVO2 OdomAlias] dropping non-monotonic timestamp")
            return
        self.last_published_stamp = stamp
        self.pub.publish(msg)


def main():
    rospy.init_node("fastlivo2_odometry_alias", anonymous=False)
    OdometryAliasNode()
    rospy.spin()


if __name__ == "__main__":
    main()
