#!/usr/bin/env python3
"""Log lag between current /clock and selected message header stamps.

This does not modify any data.  It is only a diagnostic to show whether LVI-SAM
outputs are falling behind raw rosbag camera/LiDAR playback.
"""

import threading

import rospy
import rostopic
from rosgraph_msgs.msg import Clock


class TimeSyncMonitor:
    def __init__(self):
        topics_raw = rospy.get_param(
            "~topics",
            "/camera/right/image_raw,/cloud_registered_raw,/lvi_sam/lidar/mapping/odometry,/lvi_sam/lidar/mapping/cloud_registered,/ground_truth_odometry",
        )
        self.topics = [t.strip() for t in topics_raw.split(",") if t.strip()]
        self.lock = threading.Lock()
        self.clock = None
        self.last = {}
        self.subs = {}
        rospy.Subscriber("/clock", Clock, self.clock_cb, queue_size=10)
        rospy.Timer(rospy.Duration(1.0), self.subscribe_missing)
        rospy.Timer(rospy.Duration(2.0), self.report)

    def clock_cb(self, msg):
        with self.lock:
            self.clock = msg.clock.to_sec()

    def subscribe_missing(self, _event):
        for topic in self.topics:
            if topic in self.subs:
                continue
            msg_class, real_topic, _ = rostopic.get_topic_class(topic, blocking=False)
            if msg_class is None:
                continue
            self.subs[topic] = rospy.Subscriber(
                real_topic,
                msg_class,
                lambda msg, name=topic: self.msg_cb(name, msg),
                queue_size=5,
            )
            rospy.loginfo("[TimeSyncMonitor] watching %s", topic)

    def msg_cb(self, topic, msg):
        header = getattr(msg, "header", None)
        if header is None:
            return
        stamp = header.stamp.to_sec()
        with self.lock:
            self.last[topic] = stamp

    def report(self, _event):
        with self.lock:
            clock = self.clock
            last = dict(self.last)
        if clock is None:
            return
        chunks = []
        for topic in self.topics:
            stamp = last.get(topic)
            if stamp is None:
                chunks.append(f"{topic}=no_msg")
            else:
                chunks.append(f"{topic} lag={clock - stamp:+.3f}s")
        rospy.loginfo("[TimeSyncMonitor] /clock=%.3f | %s", clock, " | ".join(chunks))


def main():
    rospy.init_node("time_sync_monitor")
    TimeSyncMonitor()
    rospy.spin()


if __name__ == "__main__":
    main()
