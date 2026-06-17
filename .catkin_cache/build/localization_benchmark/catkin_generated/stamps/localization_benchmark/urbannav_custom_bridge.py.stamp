#!/usr/bin/env python3
"""Dataset-to-benchmark message adapter.

The historical filename is retained so existing Docker images and launch files keep
working. All source topics, labels and optional streams are ROS parameters; no
dataset-specific topic is hard-coded into the runtime path.
"""
import threading

import rospy
from sensor_msgs.msg import Image, Imu, PointCloud2
from std_msgs.msg import Header

from custom_localization_msgs.msg import CustomImage, CustomImu, CustomPointCloud


class DatasetCustomBridge:
    def __init__(self):
        self.dataset = rospy.get_param("~dataset", "urbannav_hk_tst_20210517")
        self.counts = {"lidar": 0, "imu": 0, "camera_right": 0, "camera_left": 0}
        self.lock = threading.Lock()

        self.lidar_topic = rospy.get_param("~source_lidar_topic", "/velodyne_points")
        self.imu_topic = rospy.get_param("~source_imu_topic", "/imu/data")
        self.camera_topic = rospy.get_param("~source_camera_topic", "/zed2/camera/right/image_raw")
        self.camera_left_topic = rospy.get_param("~source_left_camera_topic", "/zed2/camera/left/image_raw")
        self.lidar_sensor_name = rospy.get_param("~lidar_sensor_name", "lidar")
        self.imu_sensor_name = rospy.get_param("~imu_sensor_name", "imu")
        self.camera_sensor_name = rospy.get_param("~camera_sensor_name", "camera_right")
        self.left_camera_sensor_name = rospy.get_param("~left_camera_sensor_name", "camera_left")
        self.use_clock_stamp = self._as_bool(rospy.get_param("~use_clock_stamp", False))

        self.lidar_pub = rospy.Publisher(
            rospy.get_param("~custom_lidar_topic", "/mycar/lidar/custom_points"),
            CustomPointCloud, queue_size=50,
        )
        self.imu_pub = rospy.Publisher(
            rospy.get_param("~custom_imu_topic", "/mycar/imu/custom_imu"),
            CustomImu, queue_size=200,
        )
        self.camera_pub = rospy.Publisher(
            rospy.get_param("~custom_camera_topic", "/mycar/camera/right/custom_image"),
            CustomImage, queue_size=20,
        )
        self.camera_left_pub = rospy.Publisher(
            rospy.get_param("~custom_left_camera_topic", "/mycar/camera/left/custom_image"),
            CustomImage, queue_size=20,
        )

        self._subscribe_required(self.lidar_topic, PointCloud2, self.lidar_cb, 50, "LiDAR")
        self._subscribe_required(self.imu_topic, Imu, self.imu_cb, 200, "IMU")
        self._subscribe_optional(self.camera_topic, Image, self.camera_cb, 20, "camera")
        self._subscribe_optional(self.camera_left_topic, Image, self.camera_left_cb, 20, "left camera")
        rospy.Timer(rospy.Duration(5.0), self.log_rates)
        rospy.loginfo(
            "[DatasetCustomBridge] dataset=%s lidar=%s imu=%s camera=%s left=%s use_clock_stamp=%s",
            self.dataset, self.lidar_topic, self.imu_topic,
            self.camera_topic or "disabled", self.camera_left_topic or "disabled",
            self.use_clock_stamp,
        )

    @staticmethod
    def _subscribe_required(topic, msg_type, callback, queue_size, label):
        if not topic:
            raise rospy.ROSInitException("Required %s source topic is empty" % label)
        rospy.Subscriber(topic, msg_type, callback, queue_size=queue_size)

    @staticmethod
    def _subscribe_optional(topic, msg_type, callback, queue_size, label):
        if topic:
            rospy.Subscriber(topic, msg_type, callback, queue_size=queue_size)
        else:
            rospy.loginfo("[DatasetCustomBridge] optional %s stream disabled", label)

    @staticmethod
    def _as_bool(value):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("1", "true", "yes", "on")

    def _bridge_header(self, header):
        if not self.use_clock_stamp:
            return header
        out = Header()
        out.seq = header.seq
        out.stamp = rospy.Time.now()
        out.frame_id = header.frame_id
        return out

    def lidar_cb(self, msg):
        out = CustomPointCloud()
        out.header = self._bridge_header(msg.header)
        out.dataset = self.dataset
        out.sensor_name = self.lidar_sensor_name
        out.source_topic = self.lidar_topic
        out.perturbation_label = "none"
        out.cloud = msg
        self.lidar_pub.publish(out)
        with self.lock:
            self.counts["lidar"] += 1

    def imu_cb(self, msg):
        out = CustomImu()
        out.header = self._bridge_header(msg.header)
        out.dataset = self.dataset
        out.sensor_name = self.imu_sensor_name
        out.source_topic = self.imu_topic
        out.perturbation_label = "none"
        out.imu = msg
        self.imu_pub.publish(out)
        with self.lock:
            self.counts["imu"] += 1

    def _make_custom_image(self, msg, sensor_name, source_topic):
        out = CustomImage()
        out.header = self._bridge_header(msg.header)
        out.dataset = self.dataset
        out.sensor_name = sensor_name
        out.source_topic = source_topic
        out.perturbation_label = "none"
        out.image = msg
        return out

    def camera_cb(self, msg):
        self.camera_pub.publish(self._make_custom_image(msg, self.camera_sensor_name, self.camera_topic))
        with self.lock:
            self.counts["camera_right"] += 1

    def camera_left_cb(self, msg):
        self.camera_left_pub.publish(self._make_custom_image(msg, self.left_camera_sensor_name, self.camera_left_topic))
        with self.lock:
            self.counts["camera_left"] += 1

    def log_rates(self, _event):
        with self.lock:
            rospy.loginfo(
                "[DatasetCustomBridge] totals lidar=%d imu=%d camera=%d left=%d",
                self.counts["lidar"], self.counts["imu"],
                self.counts["camera_right"], self.counts["camera_left"],
            )


def main():
    rospy.init_node("dataset_custom_bridge")
    DatasetCustomBridge()
    rospy.spin()


if __name__ == "__main__":
    main()
