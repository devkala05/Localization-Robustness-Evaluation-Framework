#!/usr/bin/env python3
"""Republish native LVI-SAM mapping odometry under one benchmark topic.

When LVI-SAM is restarted during a fault run, its native map starts in a fresh
local frame. This wrapper can seed that fresh frame from the current fused pose
so the exported benchmark trajectory resumes from the active localization pose.
"""
import copy
import math
import time

import numpy as np
import rospy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry


def as_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def normalize_quaternion(q):
    out = np.asarray(q, dtype=float)
    norm = float(np.linalg.norm(out))
    if not math.isfinite(norm) or norm < 1.0e-12:
        raise ValueError("invalid quaternion")
    return out / norm


def quaternion_to_matrix(q_xyzw):
    x, y, z, w = normalize_quaternion(q_xyzw)
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return np.array([
        [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
        [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
        [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
    ], dtype=float)


def matrix_to_quaternion(R):
    m = np.asarray(R, dtype=float)
    trace = float(np.trace(m))
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        q = np.array([(m[2, 1] - m[1, 2]) / s,
                      (m[0, 2] - m[2, 0]) / s,
                      (m[1, 0] - m[0, 1]) / s,
                      0.25 * s])
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
        q = np.array([0.25 * s, (m[0, 1] + m[1, 0]) / s,
                      (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s])
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
        q = np.array([(m[0, 1] + m[1, 0]) / s, 0.25 * s,
                      (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s])
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
        q = np.array([(m[0, 2] + m[2, 0]) / s,
                      (m[1, 2] + m[2, 1]) / s, 0.25 * s,
                      (m[1, 0] - m[0, 1]) / s])
    return normalize_quaternion(q)


def pose_to_matrix(pose):
    T = np.eye(4, dtype=float)
    T[:3, :3] = quaternion_to_matrix([
        pose.orientation.x, pose.orientation.y,
        pose.orientation.z, pose.orientation.w,
    ])
    T[:3, 3] = [pose.position.x, pose.position.y, pose.position.z]
    return T


def matrix_to_pose(T, pose):
    q = matrix_to_quaternion(T[:3, :3])
    pose.position.x, pose.position.y, pose.position.z = map(float, T[:3, 3])
    pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w = map(float, q)


def invert_transform(T):
    out = np.eye(4, dtype=float)
    out[:3, :3] = T[:3, :3].T
    out[:3, 3] = -(out[:3, :3] @ T[:3, 3])
    return out


class OdometryAliasNode:
    def __init__(self):
        self.input_topic = rospy.get_param("~input_topic", "/lvi_sam/lidar/mapping/odometry")
        self.output_topic = rospy.get_param("~output_topic", "/lvisam/odometry")
        self.rebase_on_start = as_bool(rospy.get_param("~rebase_on_start", True))
        self.anchor_pose_topic = rospy.get_param("~anchor_pose_topic", "/fused_localization/pose")
        self.anchor_wait_sec = float(rospy.get_param("~anchor_wait_sec", 2.0))
        self.anchor_max_age_sec = float(rospy.get_param("~anchor_max_age_sec", 2.0))
        # Hard deadline for waiting on an actual anchor pose message. The fusion
        # node only starts publishing /fused_localization/pose once a source is
        # already healthy, so waiting on "topic advertised" alone (see
        # anchor_topic_available) can deadlock forever at startup: fusion waits
        # for odometry, this node waits for fusion's pose. Past this deadline we
        # give up and publish in the native frame regardless.
        self.anchor_giveup_sec = float(rospy.get_param("~anchor_giveup_sec", 6.0))
        sensor_to_body = rospy.get_param(
            "~sensor_to_body", [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        )
        self.sensor_to_body = np.asarray(sensor_to_body, dtype=float).reshape(4, 4)
        if not np.all(np.isfinite(self.sensor_to_body)):
            raise rospy.ROSInitException("~sensor_to_body must be a finite 4x4 transform")
        self.start_wall = time.monotonic()
        self.latest_anchor_T = None
        self.latest_anchor_wall = 0.0
        self.latest_anchor_frame = ""
        self.output_from_native = None
        self.last_published_stamp = None
        self.pub = rospy.Publisher(self.output_topic, Odometry, queue_size=100)
        if self.rebase_on_start:
            rospy.Subscriber(self.anchor_pose_topic, PoseStamped, self.anchor_cb, queue_size=20)
        rospy.Subscriber(self.input_topic, Odometry, self.odom_cb, queue_size=100)
        rospy.loginfo(
            "[LVISAM OdomAlias] %s -> %s rebase=%s anchor=%s",
            self.input_topic,
            self.output_topic,
            self.rebase_on_start,
            self.anchor_pose_topic,
        )

    def anchor_cb(self, msg):
        try:
            self.latest_anchor_T = pose_to_matrix(msg.pose)
            self.latest_anchor_wall = time.monotonic()
            self.latest_anchor_frame = msg.header.frame_id
        except Exception as exc:
            rospy.logwarn_throttle(2.0, "[LVISAM OdomAlias] rejected anchor pose: %s", exc)

    def anchor_topic_available(self):
        try:
            anchor = rospy.resolve_name(self.anchor_pose_topic)
            return any(topic == anchor for topic, _types in rospy.get_published_topics())
        except Exception:
            return False

    def odom_cb(self, msg):
        stamp = msg.header.stamp.to_sec()
        if stamp <= 0.0:
            rospy.logwarn_throttle(2.0, "[LVISAM OdomAlias] dropping zero timestamp")
            return
        if self.last_published_stamp is not None and stamp <= self.last_published_stamp:
            rospy.logwarn_throttle(2.0, "[LVISAM OdomAlias] dropping non-monotonic timestamp")
            return
        out = self.rebased_message(msg)
        if out is None:
            return
        self.last_published_stamp = stamp
        self.pub.publish(out)

    def rebased_message(self, msg):
        try:
            native_T = pose_to_matrix(msg.pose.pose) @ self.sensor_to_body
        except Exception as exc:
            rospy.logwarn_throttle(2.0, "[LVISAM OdomAlias] dropping invalid native pose: %s", exc)
            return None
        if self.output_from_native is None:
            if self.rebase_on_start and self.latest_anchor_T is not None:
                anchor_age = time.monotonic() - self.latest_anchor_wall
                if anchor_age <= self.anchor_max_age_sec:
                    self.output_from_native = self.latest_anchor_T @ invert_transform(native_T)
                    rospy.logwarn(
                        "[LVISAM OdomAlias] rebased native startup frame to %s using %s",
                        self.latest_anchor_frame or "anchor",
                        self.anchor_pose_topic,
                    )
                elif time.monotonic() - self.start_wall < self.anchor_wait_sec:
                    return None
            if self.output_from_native is None:
                elapsed = time.monotonic() - self.start_wall
                if self.rebase_on_start and elapsed < self.anchor_wait_sec:
                    return None
                if (self.rebase_on_start and elapsed < self.anchor_giveup_sec and
                        self.anchor_topic_available()):
                    rospy.logwarn_throttle(
                        2.0,
                        "[LVISAM OdomAlias] waiting for fresh startup anchor from %s; refusing native frame",
                        self.anchor_pose_topic,
                    )
                    return None
                self.output_from_native = np.eye(4, dtype=float)
                rospy.logwarn(
                    "[LVISAM OdomAlias] no fresh startup anchor within %.1fs; publishing native frame",
                    self.anchor_giveup_sec,
                )
        out = copy.deepcopy(msg)
        rebased_T = self.output_from_native @ native_T
        matrix_to_pose(rebased_T, out.pose.pose)
        if self.latest_anchor_frame:
            out.header.frame_id = self.latest_anchor_frame
        return out


def main():
    rospy.init_node("lvisam_odometry_alias", anonymous=False)
    OdometryAliasNode()
    rospy.spin()


if __name__ == "__main__":
    main()
