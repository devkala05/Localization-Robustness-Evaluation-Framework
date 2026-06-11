#!/usr/bin/env python3
import threading

import rospy
from sensor_msgs.msg import Image, Imu, PointCloud2

from custom_localization_msgs.msg import CustomImage, CustomImu, CustomPointCloud


class UrbanNavCustomBridge:
    def __init__(self):
        self.dataset = rospy.get_param("~dataset", "urbannav_hk_tst_20210517")
        self.counts = {"lidar": 0, "imu": 0, "camera_right": 0, "camera_left": 0}
        self.lock = threading.Lock()

        self.lidar_pub = rospy.Publisher(
            rospy.get_param("~custom_lidar_topic", "/mycar/lidar/custom_points"),
            CustomPointCloud,
            queue_size=50,
        )
        self.imu_pub = rospy.Publisher(
            rospy.get_param("~custom_imu_topic", "/mycar/imu/custom_imu"),
            CustomImu,
            queue_size=200,
        )
        self.camera_pub = rospy.Publisher(
            rospy.get_param("~custom_camera_topic", "/mycar/camera/right/custom_image"),
            CustomImage,
            queue_size=20,
        )
        self.camera_left_pub = rospy.Publisher(
            rospy.get_param("~custom_left_camera_topic", "/mycar/camera/left/custom_image"),
            CustomImage,
            queue_size=20,
        )

        self.lidar_topic = rospy.get_param("~source_lidar_topic", "/velodyne_points")
        self.imu_topic = rospy.get_param("~source_imu_topic", "/imu/data")
        self.camera_topic = rospy.get_param("~source_camera_topic", "/zed2/camera/right/image_raw")
        self.camera_left_topic = rospy.get_param("~source_left_camera_topic", "/zed2/camera/left/image_raw")

        rospy.Subscriber(self.lidar_topic, PointCloud2, self.lidar_cb, queue_size=50)
        rospy.Subscriber(self.imu_topic, Imu, self.imu_cb, queue_size=200)
        rospy.Subscriber(self.camera_topic, Image, self.camera_cb, queue_size=20)
        rospy.Subscriber(self.camera_left_topic, Image, self.camera_left_cb, queue_size=20)
        rospy.Timer(rospy.Duration(5.0), self.log_rates)

    def lidar_cb(self, msg):
        out = CustomPointCloud()
        out.header = msg.header
        out.dataset = self.dataset
        out.sensor_name = "velodyne_center"
        out.source_topic = self.lidar_topic
        out.perturbation_label = "none"
        out.cloud = msg
        self.lidar_pub.publish(out)
        with self.lock:
            self.counts["lidar"] += 1

    def imu_cb(self, msg):
        out = CustomImu()
        out.header = msg.header
        out.dataset = self.dataset
        out.sensor_name = "xsens_imu"
        out.source_topic = self.imu_topic
        out.perturbation_label = "none"
        out.imu = msg
        self.imu_pub.publish(out)
        with self.lock:
            self.counts["imu"] += 1

    def _make_custom_image(self, msg, sensor_name, source_topic):
        out = CustomImage()
        out.header = msg.header
        out.dataset = self.dataset
        out.sensor_name = sensor_name
        out.source_topic = source_topic
        out.perturbation_label = "none"
        out.image = msg
        return out

    def camera_cb(self, msg):
        self.camera_pub.publish(self._make_custom_image(msg, "zed2_right", self.camera_topic))
        with self.lock:
            self.counts["camera_right"] += 1

    def camera_left_cb(self, msg):
        self.camera_left_pub.publish(self._make_custom_image(msg, "zed2_left", self.camera_left_topic))
        with self.lock:
            self.counts["camera_left"] += 1

    def log_rates(self, _event):
        with self.lock:
            rospy.loginfo(
                "[UrbanNavCustomBridge] totals lidar=%d imu=%d camera_right=%d camera_left=%d",
                self.counts["lidar"],
                self.counts["imu"],
                self.counts["camera_right"],
                self.counts["camera_left"],
            )


def main():
    rospy.init_node("urbannav_custom_bridge")
    UrbanNavCustomBridge()
    rospy.spin()


if __name__ == "__main__":
    main()
