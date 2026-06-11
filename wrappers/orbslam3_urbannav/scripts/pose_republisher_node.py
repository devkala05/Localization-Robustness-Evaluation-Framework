#!/usr/bin/env python3
"""
pose_republisher_node.py  (orbslam3_urbannav)
==============================================
Converts the patched native ORB-SLAM3 PoseStamped output into the benchmark
nav_msgs/Odometry + nav_msgs/Path topics.

Native ORB-SLAM3 publishes camera pose in visual camera convention. This node
rotates it into ROS x-forward/y-left/z-up convention and publishes:
  /orbslam3/odometry/mapping  nav_msgs/Odometry  (benchmark/eval)
  /orbslam3/mapping/path      nav_msgs/Path      (RViz)

Legacy aliases /orbslam3/odometry and /orbslam3/path are also published by
default for compatibility with the standalone ORB-SLAM3 wrapper.
"""

import threading

import geometry_msgs.msg as gm
import numpy as np
import rospy
import tf2_ros
import transforms3d
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Odometry, Path
from std_msgs.msg import String

MAX_PATH_LENGTH = 10000

# ORB camera/world basis -> ROS basis: x_right,y_down,z_forward to
# x_forward,y_left,z_up.
R_ROS_ORB = np.array([
    [0.0, 0.0, 1.0],
    [-1.0, 0.0, 0.0],
    [0.0, -1.0, 0.0],
])


def _pose_orb_to_ros(pose_msg):
    p_orb = np.array([pose_msg.position.x, pose_msg.position.y, pose_msg.position.z])
    p_ros = R_ROS_ORB.dot(p_orb)

    q = pose_msg.orientation
    r_orb = transforms3d.quaternions.quat2mat([q.w, q.x, q.y, q.z])
    r_ros = R_ROS_ORB.dot(r_orb).dot(R_ROS_ORB.T)
    qw, qx, qy, qz = transforms3d.quaternions.mat2quat(r_ros)

    out = gm.Pose()
    out.position.x = float(p_ros[0])
    out.position.y = float(p_ros[1])
    out.position.z = float(p_ros[2])
    out.orientation.x = float(qx)
    out.orientation.y = float(qy)
    out.orientation.z = float(qz)
    out.orientation.w = float(qw)
    return out


class PoseRepublisher:
    def __init__(self):
        self._lock = threading.Lock()
        self.input_topic = rospy.get_param("~input_topic", "/orb_slam3/camera_pose")
        self.output_odom_topic = rospy.get_param("~output_odom_topic", "/orbslam3/odometry/mapping")
        self.output_path_topic = rospy.get_param("~output_path_topic", "/orbslam3/mapping/path")
        self.status_topic = rospy.get_param("~status_topic", "/orbslam3/tracking_status")
        self.world_frame_id = rospy.get_param("~world_frame_id", "camera_init")
        self.child_frame_id = rospy.get_param("~child_frame_id", "camera_right")
        self.publish_tf = rospy.get_param("~publish_tf", True)
        self.publish_legacy_aliases = rospy.get_param("~publish_legacy_aliases", True)

        self._pub_odom = rospy.Publisher(self.output_odom_topic, Odometry, queue_size=50)
        self._pub_path = rospy.Publisher(self.output_path_topic, Path, queue_size=10)
        self._pub_status = rospy.Publisher(self.status_topic, String, queue_size=10)
        self._pub_odom_legacy = None
        self._pub_path_legacy = None
        if self.publish_legacy_aliases:
            self._pub_odom_legacy = rospy.Publisher("/orbslam3/odometry", Odometry, queue_size=50)
            self._pub_path_legacy = rospy.Publisher("/orbslam3/path", Path, queue_size=10)

        self._tf_broadcaster = tf2_ros.TransformBroadcaster()
        self._path = Path()
        self._path.header.frame_id = self.world_frame_id
        self._last_pose_sec = None
        self._total_received = 0

        self._sub = rospy.Subscriber(self.input_topic, PoseStamped, self._pose_cb, queue_size=50)
        self._watchdog = rospy.Timer(rospy.Duration(1.0), self._watchdog_cb)

        rospy.loginfo(
            "[ORB-SLAM3 PoseRepublisher] input=%s odom=%s path=%s frame=%s child=%s",
            self.input_topic,
            self.output_odom_topic,
            self.output_path_topic,
            self.world_frame_id,
            self.child_frame_id,
        )

    def _pose_cb(self, msg: PoseStamped):
        with self._lock:
            self._total_received += 1
            self._last_pose_sec = rospy.Time.now().to_sec()

            stamp = msg.header.stamp
            pose_ros = _pose_orb_to_ros(msg.pose)
            p = pose_ros.position
            q = pose_ros.orientation

            odom = Odometry()
            odom.header.stamp = stamp
            odom.header.frame_id = self.world_frame_id
            odom.child_frame_id = self.child_frame_id
            odom.pose.pose = pose_ros
            odom.pose.covariance = [1e-3] * 36
            self._pub_odom.publish(odom)
            if self._pub_odom_legacy:
                self._pub_odom_legacy.publish(odom)

            if self.publish_tf:
                ts = TransformStamped()
                ts.header.stamp = stamp
                ts.header.frame_id = self.world_frame_id
                ts.child_frame_id = self.child_frame_id
                ts.transform.translation.x = p.x
                ts.transform.translation.y = p.y
                ts.transform.translation.z = p.z
                ts.transform.rotation = q
                self._tf_broadcaster.sendTransform(ts)

            ps = PoseStamped()
            ps.header.stamp = stamp
            ps.header.frame_id = self.world_frame_id
            ps.pose = pose_ros
            self._path.poses.append(ps)
            if len(self._path.poses) > MAX_PATH_LENGTH:
                self._path.poses = self._path.poses[-MAX_PATH_LENGTH:]
            self._path.header.stamp = stamp
            self._pub_path.publish(self._path)
            if self._pub_path_legacy:
                self._pub_path_legacy.publish(self._path)

            self._pub_status.publish(String(data="TRACKING"))
            if self._total_received % 100 == 0:
                rospy.loginfo(
                    "[ORB-SLAM3 PoseRepublisher] poses=%d path_len=%d latest=%.3f",
                    self._total_received,
                    len(self._path.poses),
                    stamp.to_sec(),
                )

    def _watchdog_cb(self, _event):
        with self._lock:
            now_sec = rospy.Time.now().to_sec()
            if now_sec == 0.0:
                return
            if self._last_pose_sec is None:
                status = "WAITING"
            else:
                status = "LOST" if (now_sec - self._last_pose_sec) > 2.0 else "TRACKING"
            self._pub_status.publish(String(data=status))


def main():
    rospy.init_node("orbslam3_pose_republisher_node", anonymous=False)
    PoseRepublisher()
    rospy.loginfo("[ORB-SLAM3 PoseRepublisher] Running.")
    rospy.spin()


if __name__ == "__main__":
    main()
