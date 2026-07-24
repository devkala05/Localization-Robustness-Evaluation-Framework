#!/usr/bin/env python3
"""Replay selected UrbanLoco streams using exact rosbag event timestamps."""

import time

import rosbag
import rospy
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import CompressedImage, Imu, PointCloud2


class UrbanBagPlayer:
    def __init__(self):
        self.bag_path = rospy.get_param("~bag_path")
        self.rate = float(rospy.get_param("~rate", 1.0))
        self.start_offset = float(rospy.get_param("~start_offset", 0.0))
        self.duration = float(rospy.get_param("~duration", 0.0))
        self.lidar_topic = rospy.get_param("~lidar_topic", "/rslidar_points")
        self.imu_topic = rospy.get_param("~imu_topic", "/imu_raw")
        self.camera_topic = rospy.get_param(
            "~camera_topic", "/camera_array/cam0/image_raw/compressed")
        self.enable_lidar = bool(rospy.get_param("~enable_lidar", True))
        self.enable_imu = bool(rospy.get_param("~enable_imu", True))
        self.enable_camera = bool(rospy.get_param("~enable_camera", True))
        if self.rate <= 0.0 or self.start_offset < 0.0 or self.duration < 0.0:
            raise rospy.ROSInitException("rate must be positive; offsets must be non-negative")
        self.clock_pub = rospy.Publisher("/clock", Clock, queue_size=10)
        self.publishers = {}
        if self.enable_lidar:
            self.publishers[self.lidar_topic] = rospy.Publisher(
                self.lidar_topic, PointCloud2, queue_size=20)
        if self.enable_imu:
            self.publishers[self.imu_topic] = rospy.Publisher(
                self.imu_topic, Imu, queue_size=200)
        if self.enable_camera:
            self.publishers[self.camera_topic] = rospy.Publisher(
                self.camera_topic, CompressedImage, queue_size=20)

    def run(self):
        with rosbag.Bag(self.bag_path, "r") as bag:
            bag_start = bag.get_start_time()
            event_start = bag_start + self.start_offset
            event_end = event_start + self.duration if self.duration > 0.0 else bag.get_end_time()
            topics = list(self.publishers)
            start_ros = rospy.Time.from_sec(event_start)
            end_ros = rospy.Time.from_sec(event_end)
            wall_start = time.monotonic()
            counts = {topic: 0 for topic in topics}
            # Allow estimator subscribers to finish connecting before event zero.
            time.sleep(0.5)
            for topic, message, event_stamp in bag.read_messages(
                    topics=topics, start_time=start_ros, end_time=end_ros):
                if rospy.is_shutdown():
                    break
                target_wall = wall_start + (event_stamp.to_sec() - event_start) / self.rate
                while not rospy.is_shutdown():
                    remaining = target_wall - time.monotonic()
                    if remaining <= 0.0:
                        break
                    time.sleep(min(remaining, 0.01))
                self.clock_pub.publish(Clock(clock=event_stamp))
                # UrbanLoco camera headers are zero. The rosbag event time is
                # the authoritative sensor timestamp and must be attached
                # before any downstream decoding or queuing occurs.
                if topic == self.camera_topic:
                    message.header.stamp = event_stamp
                self.publishers[topic].publish(message)
                counts[topic] += 1
            self.clock_pub.publish(Clock(clock=end_ros))
            rospy.loginfo("[UrbanBagPlayer] completed counts=%s", counts)


def main():
    rospy.init_node("urban_bag_player")
    UrbanBagPlayer().run()


if __name__ == "__main__":
    main()
