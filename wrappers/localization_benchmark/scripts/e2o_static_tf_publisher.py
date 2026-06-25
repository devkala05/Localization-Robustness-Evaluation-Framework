#!/usr/bin/env python3
"""Publish only the static E2O sensor transforms required by the two estimators."""
import math

import numpy as np
import rospy
import tf2_ros
from geometry_msgs.msg import TransformStamped


def matrix_to_quaternion(matrix):
    m = np.asarray(matrix, dtype=float).reshape(3, 3)
    trace = float(np.trace(m))
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s,
             (m[1, 0] - m[0, 1]) / s, 0.25 * s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
        q = [0.25 * s, (m[0, 1] + m[1, 0]) / s,
             (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s]
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
        q = [(m[0, 1] + m[1, 0]) / s, 0.25 * s,
             (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
        q = [(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s,
             0.25 * s, (m[1, 0] - m[0, 1]) / s]
    q = np.asarray(q, dtype=float)
    q /= np.linalg.norm(q)
    return q.tolist()


def main():
    rospy.init_node("e2o_static_tf_publisher")
    transforms = rospy.get_param("/e2o/static_transforms", [])
    messages = []
    for item in transforms:
        msg = TransformStamped()
        msg.header.stamp = rospy.Time.now()
        msg.header.frame_id = str(item["parent"])
        msg.child_frame_id = str(item["child"])
        translation = item.get("translation", [0.0, 0.0, 0.0])
        msg.transform.translation.x, msg.transform.translation.y, msg.transform.translation.z = map(float, translation)
        quaternion = item.get("quaternion")
        if quaternion is None:
            quaternion = matrix_to_quaternion(item["rotation"])
        msg.transform.rotation.x, msg.transform.rotation.y, msg.transform.rotation.z, msg.transform.rotation.w = map(float, quaternion)
        messages.append(msg)
    broadcaster = tf2_ros.StaticTransformBroadcaster()
    broadcaster.sendTransform(messages)
    rospy.loginfo("[E2OStaticTF] published %d sensor transforms", len(messages))
    rospy.spin()


if __name__ == "__main__":
    main()
