#!/usr/bin/env python3
"""Publish dataset calibration without changing localization internals."""
import math

import rospy
import tf2_ros
import yaml
from geometry_msgs.msg import TransformStamped


def matrix_to_quaternion(m):
    # Stable 3x3 rotation-matrix to xyzw quaternion conversion.
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        qw = 0.25 * s
        qx = (m[2][1] - m[1][2]) / s
        qy = (m[0][2] - m[2][0]) / s
        qz = (m[1][0] - m[0][1]) / s
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2.0
        qw = (m[2][1] - m[1][2]) / s
        qx = 0.25 * s
        qy = (m[0][1] + m[1][0]) / s
        qz = (m[0][2] + m[2][0]) / s
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2.0
        qw = (m[0][2] - m[2][0]) / s
        qx = (m[0][1] + m[1][0]) / s
        qy = 0.25 * s
        qz = (m[1][2] + m[2][1]) / s
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2.0
        qw = (m[1][0] - m[0][1]) / s
        qx = (m[0][2] + m[2][0]) / s
        qy = (m[1][2] + m[2][1]) / s
        qz = 0.25 * s
    norm = math.sqrt(qx*qx + qy*qy + qz*qz + qw*qw) or 1.0
    return [qx/norm, qy/norm, qz/norm, qw/norm]


def make_tf(parent, child, translation, quaternion):
    msg = TransformStamped()
    msg.header.stamp = rospy.Time.now()
    msg.header.frame_id = parent
    msg.child_frame_id = child
    msg.transform.translation.x = float(translation[0])
    msg.transform.translation.y = float(translation[1])
    msg.transform.translation.z = float(translation[2])
    msg.transform.rotation.x = float(quaternion[0])
    msg.transform.rotation.y = float(quaternion[1])
    msg.transform.rotation.z = float(quaternion[2])
    msg.transform.rotation.w = float(quaternion[3])
    return msg


def main():
    rospy.init_node("dataset_tf_broadcaster")
    path = rospy.get_param("~config_path")
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    messages = []
    for item in data.get("transforms", []):
        q = item.get("quaternion")
        if q is None:
            q = matrix_to_quaternion(item["rotation_matrix"])
        messages.append(make_tf(item["parent"], item["child"], item.get("translation", [0, 0, 0]), q))

    if rospy.get_param("~publish_map_odom", False):
        messages.append(make_tf("map", "odom", [0, 0, 0], [0, 0, 0, 1]))
    if rospy.get_param("~publish_camera_init_map", False):
        messages.append(make_tf("camera_init", "map", [0, 0, 0], [0, 0, 0, 1]))
    if rospy.get_param("~publish_base_link_body", False):
        messages.append(make_tf("base_link", "body", [0, 0, 0], [0, 0, 0, 1]))

    if not messages:
        raise rospy.ROSInitException("No transforms found in %s" % path)
    tf2_ros.StaticTransformBroadcaster().sendTransform(messages)
    rospy.loginfo("[dataset_tf_broadcaster] published %d transforms from %s", len(messages), path)
    rospy.spin()


if __name__ == "__main__":
    main()
