#!/usr/bin/env python3
"""Publish CameraInfo messages synchronized with an Image topic."""
import os
import yaml
import rospy
from sensor_msgs.msg import Image, CameraInfo


def _load_camera_info(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    msg = CameraInfo()
    msg.width = int(cfg.get("image_width", 0))
    msg.height = int(cfg.get("image_height", 0))
    msg.distortion_model = cfg.get("distortion_model", "plumb_bob")
    msg.D = list(map(float, cfg.get("distortion_coefficients", {}).get("data", [])))
    msg.K = list(map(float, cfg.get("camera_matrix", {}).get("data", [0.0] * 9)))
    msg.R = list(map(float, cfg.get("rectification_matrix", {}).get("data", [1,0,0,0,1,0,0,0,1])))
    msg.P = list(map(float, cfg.get("projection_matrix", {}).get("data", [0.0] * 12)))
    return msg


class CameraInfoSyncPublisher:
    def __init__(self):
        image_topic = rospy.get_param("~image_topic", "/camera/color/image_raw")
        info_topic = rospy.get_param("~camera_info_topic", "/camera/color/camera_info")
        config_path = rospy.get_param("~camera_info_yaml")
        self.default_frame_id = rospy.get_param("~frame_id", "front_camera")
        self.camera_info = _load_camera_info(config_path)
        self.pub = rospy.Publisher(info_topic, CameraInfo, queue_size=10)
        self.sub = rospy.Subscriber(image_topic, Image, self.cb, queue_size=10)
        rospy.loginfo("CameraInfo publisher: %s -> %s using %s", image_topic, info_topic, config_path)

    def cb(self, img):
        msg = CameraInfo()
        msg.header = img.header
        if not msg.header.frame_id:
            msg.header.frame_id = self.default_frame_id
        msg.width = self.camera_info.width or img.width
        msg.height = self.camera_info.height or img.height
        msg.distortion_model = self.camera_info.distortion_model
        msg.D = self.camera_info.D
        msg.K = self.camera_info.K
        msg.R = self.camera_info.R
        msg.P = self.camera_info.P
        self.pub.publish(msg)


if __name__ == "__main__":
    rospy.init_node("camera_info_sync_publisher")
    CameraInfoSyncPublisher()
    rospy.spin()
