#!/usr/bin/env python3
import rospy
from rosgraph_msgs.msg import Clock
from visualization_msgs.msg import Marker


class BagClockMarker:
    def __init__(self):
        self.frame_id = rospy.get_param("~frame_id", "camera_init")
        self.topic = rospy.get_param("~topic", "/benchmark/bag_clock_marker")
        self.x = float(rospy.get_param("~x", 0.0))
        self.y = float(rospy.get_param("~y", -35.0))
        self.z = float(rospy.get_param("~z", 12.0))
        self.scale = float(rospy.get_param("~scale", 4.0))
        self.clock = None
        self.pub = rospy.Publisher(self.topic, Marker, queue_size=1, latch=True)
        rospy.Subscriber("/clock", Clock, self.clock_cb, queue_size=10)

    def clock_cb(self, msg):
        self.clock = msg.clock
        self.publish()

    def publish(self):
        marker = Marker()
        marker.header.frame_id = self.frame_id
        marker.header.stamp = rospy.Time(0)
        marker.ns = "bag_clock"
        marker.id = 1
        marker.type = Marker.TEXT_VIEW_FACING
        marker.action = Marker.ADD
        marker.pose.position.x = self.x
        marker.pose.position.y = self.y
        marker.pose.position.z = self.z
        marker.pose.orientation.w = 1.0
        marker.scale.z = self.scale
        marker.color.r = 0.1
        marker.color.g = 0.95
        marker.color.b = 1.0
        marker.color.a = 1.0
        marker.text = "BAG /clock: waiting"
        if self.clock is not None:
            marker.text = "BAG /clock: %.6f" % self.clock.to_sec()
        self.pub.publish(marker)

    def spin(self):
        rate = rospy.Rate(2.0)
        while not rospy.is_shutdown():
            self.publish()
            rate.sleep()


def main():
    rospy.init_node("bag_clock_marker")
    BagClockMarker().spin()


if __name__ == "__main__":
    main()
