#!/usr/bin/env python3
"""Odometry fault injector used by FAILURE_TESTING.md.

Modes are controlled at runtime with private ROS parameters:
  pass, drop, freeze, delay, nan, jump, out_of_order
"""
import collections
import copy
import math
import threading

import rospy
from nav_msgs.msg import Odometry


class PoseFaultInjector:
    def __init__(self):
        self.lock = threading.Lock()
        self.input_topic = rospy.get_param("~input_topic", "/fault/raw_odometry")
        self.output_topic = rospy.get_param("~output_topic", "/fault/odometry")
        self.pub = rospy.Publisher(self.output_topic, Odometry, queue_size=100)
        self.last = None
        self.last_mode = "pass"
        self.queue = collections.deque()
        rospy.Subscriber(self.input_topic, Odometry, self.cb, queue_size=100)
        rospy.Timer(rospy.Duration(0.01), self.timer_cb)

    def mode(self):
        return str(rospy.get_param("~mode", "pass")).strip().lower()

    def cb(self, msg: Odometry) -> None:
        with self.lock:
            mode = self.mode()
            if mode != self.last_mode:
                if mode != "delay":
                    self.queue.clear()
                if mode == "pass":
                    self.last = None
                self.last_mode = mode
            if mode == "drop":
                return
            if mode == "freeze":
                if self.last is None:
                    self.last = copy.deepcopy(msg)
                frozen = copy.deepcopy(self.last)
                self.pub.publish(frozen)
                return
            out = copy.deepcopy(msg)
            if mode == "nan":
                out.pose.pose.position.x = float("nan")
            elif mode == "jump":
                out.pose.pose.position.x += float(rospy.get_param("~jump_m", 100.0))
            elif mode == "out_of_order":
                out.header.stamp -= rospy.Duration(float(rospy.get_param("~stamp_offset_sec", 5.0)))
            elif mode == "delay":
                self.queue.append((rospy.Time.now() + rospy.Duration(float(rospy.get_param("~delay_sec", 1.0))), out))
                return
            self.last = copy.deepcopy(out)
            self.pub.publish(out)

    def timer_cb(self, _event) -> None:
        with self.lock:
            now = rospy.Time.now()
            while self.queue and self.queue[0][0] <= now:
                _, msg = self.queue.popleft()
                self.pub.publish(msg)


def main() -> None:
    rospy.init_node("pose_fault_injector")
    PoseFaultInjector()
    rospy.spin()


if __name__ == "__main__":
    main()
