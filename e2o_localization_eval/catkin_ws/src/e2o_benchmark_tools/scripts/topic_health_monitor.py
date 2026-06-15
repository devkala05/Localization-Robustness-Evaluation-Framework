#!/usr/bin/env python3
"""Simple topic rate monitor for the e2o bag topics."""
import time
import rospy
from rospy.msg import AnyMsg


class Monitor:
    def __init__(self):
        self.topics = rospy.get_param("~topics", [
            "/camera/color/image_raw",
            "/lidar102/velodyne_points",
            "/lidar103/velodyne_points",
            "/lidar104/velodyne_points",
            "/merged/velodyne_points",
        ])
        self.window = float(rospy.get_param("~window", 5.0))
        self.last = {t: [] for t in self.topics}
        for t in self.topics:
            rospy.Subscriber(t, AnyMsg, self.cb, callback_args=t, queue_size=200)
        rospy.Timer(rospy.Duration(self.window), self.report)

    def cb(self, _msg, topic):
        now = time.time()
        arr = self.last[topic]
        arr.append(now)
        cutoff = now - self.window
        while arr and arr[0] < cutoff:
            arr.pop(0)

    def report(self, _event):
        rospy.loginfo("---- e2o topic health over %.1fs ----", self.window)
        for t in self.topics:
            rate = len(self.last[t]) / self.window
            rospy.loginfo("%-38s %7.2f Hz", t, rate)


if __name__ == "__main__":
    rospy.init_node("topic_health_monitor")
    Monitor()
    rospy.spin()
