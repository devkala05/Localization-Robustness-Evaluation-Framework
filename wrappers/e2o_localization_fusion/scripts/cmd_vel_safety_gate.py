#!/usr/bin/env python3
"""Block navigation velocity commands whenever fused localization is invalid."""
import threading
import time

import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool


class CmdVelSafetyGate:
    def __init__(self):
        self.lock = threading.Lock()
        self.input_topic = rospy.get_param("~input_topic", "/cmd_vel_unfiltered")
        self.output_topic = rospy.get_param("~output_topic", "/cmd_vel")
        self.status_topic = rospy.get_param("~status_topic", "/fused_localization/navigation_ok")
        self.status_timeout = float(rospy.get_param("~status_timeout_sec", 1.0))
        self.allow = False
        self.last_status_wall = None
        self.pub = rospy.Publisher(self.output_topic, Twist, queue_size=20)
        rospy.Subscriber(self.input_topic, Twist, self.cmd_cb, queue_size=20)
        rospy.Subscriber(self.status_topic, Bool, self.status_cb, queue_size=20)
        rospy.Timer(rospy.Duration(0.1), self.watchdog_cb)
        rospy.on_shutdown(self.publish_stop)
        rospy.loginfo("[CmdVelSafetyGate] %s -> %s, health=%s", self.input_topic, self.output_topic, self.status_topic)

    def status_cb(self, msg: Bool) -> None:
        with self.lock:
            self.allow = bool(msg.data)
            self.last_status_wall = time.monotonic()
            if not self.allow:
                self.publish_stop()

    def valid_status(self) -> bool:
        return self.allow and self.last_status_wall is not None and time.monotonic() - self.last_status_wall <= self.status_timeout

    def cmd_cb(self, msg: Twist) -> None:
        with self.lock:
            self.pub.publish(msg if self.valid_status() else Twist())

    def watchdog_cb(self, _event) -> None:
        with self.lock:
            if not self.valid_status():
                self.pub.publish(Twist())

    def publish_stop(self) -> None:
        try:
            self.pub.publish(Twist())
        except Exception:
            pass


def main() -> None:
    rospy.init_node("cmd_vel_safety_gate")
    CmdVelSafetyGate()
    rospy.spin()


if __name__ == "__main__":
    main()
