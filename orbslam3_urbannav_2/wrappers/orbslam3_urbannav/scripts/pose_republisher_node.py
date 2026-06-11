#!/usr/bin/env python3
"""
pose_republisher_node.py  (orbslam3_urbannav)
==============================================
ORB-SLAM3's ROS node publishes its pose as a raw geometry_msgs/PoseStamped
on /orb_slam3/camera_pose. This node:

  1. Subscribes to /orb_slam3/camera_pose
  2. Republishes as nav_msgs/Odometry  →  /orbslam3/odometry
  3. Accumulates into nav_msgs/Path    →  /orbslam3/path
  4. Broadcasts dynamic TF:   odom → camera_right
  5. Publishes tracking status         →  /orbslam3/tracking_status (std_msgs/String)

This mirrors the role that Fast-LIO2 itself plays in the fast_lio_urbannav
pipeline — closing the loop between the algorithm's raw output and all
downstream consumers (RViz, evaluation scripts, TF tree).

Coordinate convention:
  ORB-SLAM3 publishes camera poses in its visual-SLAM camera convention:
  x right, y down, z forward. RViz/ROS expects x forward, y left, z up.
  This node rotates ORB-SLAM coordinates into the ROS convention before
  publishing odometry, path, and TF.
"""

import rospy
import tf2_ros
import geometry_msgs.msg as gm
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Odometry, Path
from std_msgs.msg import String
import transforms3d
import numpy as np
import threading


MAX_PATH_LENGTH = 10000   # cap stored poses to avoid memory growth

# ORB camera/world basis -> ROS basis: x_right,y_down,z_forward to
# x_forward,y_left,z_up.
R_ROS_ORB = np.array([
    [0.0, 0.0, 1.0],
    [-1.0, 0.0, 0.0],
    [0.0, -1.0, 0.0],
])


def _pose_orb_to_ros(pose_msg):
    p_orb = np.array([
        pose_msg.position.x,
        pose_msg.position.y,
        pose_msg.position.z,
    ])
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

        # ── Publishers ───────────────────────────────────────────────────────
        self._pub_odom   = rospy.Publisher(
            "/orbslam3/odometry", Odometry, queue_size=50)
        self._pub_path   = rospy.Publisher(
            "/orbslam3/path", Path, queue_size=10)
        self._pub_status = rospy.Publisher(
            "/orbslam3/tracking_status", String, queue_size=10)

        # ── TF broadcaster ───────────────────────────────────────────────────
        self._tf_broadcaster = tf2_ros.TransformBroadcaster()

        # ── Accumulated path ─────────────────────────────────────────────────
        self._path          = Path()
        self._path.header.frame_id = "odom"
        self._last_pose_sec = None
        self._total_received = 0

        # ── Subscriber ───────────────────────────────────────────────────────
        self._sub = rospy.Subscriber(
            "/orb_slam3/camera_pose",
            PoseStamped,
            self._pose_cb,
            queue_size=50,
        )

        # ── Status watchdog — publishes LOST if no pose for > 2s ─────────────
        self._watchdog = rospy.Timer(
            rospy.Duration(1.0), self._watchdog_cb)

        rospy.loginfo("[PoseRepublisher] Listening on /orb_slam3/camera_pose")

    # ── Pose callback ─────────────────────────────────────────────────────────
    def _pose_cb(self, msg: PoseStamped):
        with self._lock:
            self._total_received += 1
            self._last_pose_sec  = rospy.Time.now().to_sec()

            stamp = msg.header.stamp
            pose_ros = _pose_orb_to_ros(msg.pose)
            p     = pose_ros.position
            q     = pose_ros.orientation

            # ── 1. Odometry message ──────────────────────────────────────────
            odom                     = Odometry()
            odom.header.stamp        = stamp
            odom.header.frame_id     = "odom"
            odom.child_frame_id      = "camera_right"
            odom.pose.pose           = pose_ros
            # Covariance unknown — set diagonal to a large value
            odom.pose.covariance     = [1e-3] * 36
            self._pub_odom.publish(odom)

            # ── 2. TF: odom → camera_right ────────────────────────────────
            ts                           = TransformStamped()
            ts.header.stamp              = stamp
            ts.header.frame_id           = "odom"
            ts.child_frame_id            = "camera_right"
            ts.transform.translation.x   = p.x
            ts.transform.translation.y   = p.y
            ts.transform.translation.z   = p.z
            ts.transform.rotation        = q
            self._tf_broadcaster.sendTransform(ts)

            # ── 3. Path ───────────────────────────────────────────────────────
            ps             = PoseStamped()
            ps.header      = msg.header
            ps.header.frame_id = "odom"
            ps.pose        = pose_ros
            self._path.poses.append(ps)

            # Trim to cap memory
            if len(self._path.poses) > MAX_PATH_LENGTH:
                self._path.poses = self._path.poses[-MAX_PATH_LENGTH:]

            self._path.header.stamp = stamp
            self._pub_path.publish(self._path)

            # ── 4. Tracking status ────────────────────────────────────────────
            self._pub_status.publish(String(data="TRACKING"))

            if self._total_received % 100 == 0:
                rospy.loginfo(
                    f"[PoseRepublisher] poses received: {self._total_received}"
                    f"  path length: {len(self._path.poses)}"
                )

    # ── Watchdog ──────────────────────────────────────────────────────────────
    def _watchdog_cb(self, _event):
        with self._lock:
            now_sec = rospy.Time.now().to_sec()
            if now_sec == 0.0:
                return

            if self._last_pose_sec is None:
                status = "WAITING"
            else:
                elapsed = now_sec - self._last_pose_sec
                status  = "LOST" if elapsed > 2.0 else "TRACKING"
            self._pub_status.publish(String(data=status))


def main():
    rospy.init_node("pose_republisher_node", anonymous=False)
    PoseRepublisher()
    rospy.loginfo("[PoseRepublisher] Running.")
    rospy.spin()


if __name__ == "__main__":
    main()
