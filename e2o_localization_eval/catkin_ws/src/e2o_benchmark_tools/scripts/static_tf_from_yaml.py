#!/usr/bin/env python3
"""Publish static transforms from config/calibration/e2o/static_transforms.yaml."""
import os
import yaml
import numpy as np
import rospy
import tf.transformations as tft
import tf2_ros
from geometry_msgs.msg import TransformStamped


def matrix_to_quaternion(rotation_matrix):
    M = np.eye(4)
    M[:3, :3] = np.asarray(rotation_matrix, dtype=float)
    q = tft.quaternion_from_matrix(M)
    return q


def make_transform(item):
    msg = TransformStamped()
    msg.header.stamp = rospy.Time.now()
    msg.header.frame_id = str(item["parent"])
    msg.child_frame_id = str(item["child"])
    tx, ty, tz = [float(x) for x in item.get("translation", [0, 0, 0])]
    msg.transform.translation.x = tx
    msg.transform.translation.y = ty
    msg.transform.translation.z = tz
    if "quaternion" in item:
        qx, qy, qz, qw = [float(x) for x in item["quaternion"]]
    else:
        qx, qy, qz, qw = matrix_to_quaternion(item["rotation_matrix"])
    msg.transform.rotation.x = qx
    msg.transform.rotation.y = qy
    msg.transform.rotation.z = qz
    msg.transform.rotation.w = qw
    return msg


if __name__ == "__main__":
    rospy.init_node("static_tf_from_yaml")
    yaml_path = rospy.get_param("~yaml_path")
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(yaml_path)
    with open(yaml_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    transforms = [make_transform(x) for x in cfg.get("transforms", [])]
    broadcaster = tf2_ros.StaticTransformBroadcaster()
    broadcaster.sendTransform(transforms)
    rospy.loginfo("Published %d static transforms from %s", len(transforms), yaml_path)
    rospy.spin()
