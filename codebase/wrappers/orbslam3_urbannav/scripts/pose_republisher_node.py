#!/usr/bin/env python3
"""
pose_republisher_node.py  (orbslam3_urbannav)
==============================================
Converts native ORB-SLAM3 camera PoseStamped output into benchmark-compatible
vehicle/body odometry and path topics.

Important detail:
  Native ORB-SLAM3 publishes the tracked CAMERA pose. The benchmark/evaluation
  expects the vehicle/body pose, same convention as FAST-LIO2/LVI-SAM/FAST-LIVO2.
  UrbanNav RIGHT_CAMERA_T_IMU is T_body_cam (camera -> IMU/body),
  so this node applies inv(T_body_cam) after ORB's camera pose to recover
  the benchmark body pose, then normalizes the first body pose to the output world frame.

Outputs:
  /orbslam3/odometry/mapping  nav_msgs/Odometry  (vehicle/body pose)
  /orbslam3/mapping/path      nav_msgs/Path
  /orbslam3/tracking_status   std_msgs/String

TF:
  camera_init -> body is published dynamically when publish_tf:=true.
  Static body -> camera_right is published by tf_broadcaster_node.py.
"""

import math
import os
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

# RIGHT_CAMERA_T_IMU from UrbanNav extrinsic.yaml.
# Convention from UrbanNav: p_body = RIGHT_CAMERA_T_IMU * p_camera.
# ORB-SLAM3 tracks the right camera in stereo-swapped mode and mono mode, so
# vehicle/body pose is: T_world_body = T_world_camera * inv(RIGHT_CAMERA_T_IMU).
RIGHT_CAMERA_T_IMU = np.array([
    [9.9872871452749812e-01, 1.5287637777597791e-03, 5.0384696680271013e-02, 7.5332297629590136e-02],
    [-5.0367177375936031e-02, -9.8967686259809895e-03, 9.9868173179143760e-01, 6.8331281093016005e-01],
    [2.0253941424080261e-03, -9.9994985716888607e-01, -9.8071874914416046e-03, -3.0079627649520204e+00],
    [0.0, 0.0, 0.0, 1.0],
], dtype=float)

# E2O ORB-SLAM3 runs in monocular mode on /camera/color/image_raw. ORB's native
# pose is in optical camera axes (x right, y down, z forward), while the benchmark
# body frame expects x forward, y left, z up. This basis change prevents forward
# motion from appearing as RViz Z motion.
E2O_OPTICAL_CAMERA_T_BODY = np.array([
    [0.0, 0.0, 1.0, 0.0],
    [-1.0, 0.0, 0.0, 0.0],
    [0.0, -1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0],
], dtype=float)


def invert_rigid(T: np.ndarray) -> np.ndarray:
    R = T[:3, :3]
    t = T[:3, 3]
    Ti = np.eye(4)
    Ti[:3, :3] = R.T
    Ti[:3, 3] = -(R.T @ t)
    return Ti


def yaw_rotation(yaw_rad: float) -> np.ndarray:
    c = math.cos(yaw_rad)
    s = math.sin(yaw_rad)
    T = np.eye(4)
    T[:3, :3] = np.array([
        [c, -s, 0.0],
        [s, c, 0.0],
        [0.0, 0.0, 1.0],
    ])
    return T


def pose_to_mat(pose: gm.Pose) -> np.ndarray:
    q = pose.orientation
    T = np.eye(4)
    T[:3, :3] = transforms3d.quaternions.quat2mat([q.w, q.x, q.y, q.z])
    T[:3, 3] = [pose.position.x, pose.position.y, pose.position.z]
    return T


def mat_to_pose(T: np.ndarray) -> gm.Pose:
    q = transforms3d.quaternions.mat2quat(T[:3, :3])  # w, x, y, z
    out = gm.Pose()
    out.position.x = float(T[0, 3])
    out.position.y = float(T[1, 3])
    out.position.z = float(T[2, 3])
    out.orientation.w = float(q[0])
    out.orientation.x = float(q[1])
    out.orientation.y = float(q[2])
    out.orientation.z = float(q[3])
    return out


def is_finite_matrix(T: np.ndarray) -> bool:
    return bool(np.all(np.isfinite(T)))


def as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


class PoseRepublisher:
    def __init__(self):
        self._lock = threading.Lock()
        self.input_topic = rospy.get_param("~input_topic", "/orb_slam3/camera_pose")
        self.output_odom_topic = rospy.get_param("~output_odom_topic", "/orbslam3/odometry/mapping")
        self.output_path_topic = rospy.get_param("~output_path_topic", "/orbslam3/mapping/path")
        self.status_topic = rospy.get_param("~status_topic", "/orbslam3/tracking_status")
        self.world_frame_id = rospy.get_param("~world_frame_id", "camera_init")
        self.child_frame_id = rospy.get_param("~child_frame_id", "body")
        self.publish_tf = rospy.get_param("~publish_tf", True)
        self.publish_legacy_aliases = rospy.get_param("~publish_legacy_aliases", True)
        self.normalize_to_start = rospy.get_param("~normalize_to_start", True)
        self.max_interframe_translation = float(rospy.get_param("~max_interframe_translation", 5.0))
        self.max_speed_mps = float(rospy.get_param("~max_speed_mps", 45.0))
        self.use_camera_to_body_extrinsic = rospy.get_param("~use_camera_to_body_extrinsic", True)
        self.dataset_id = str(rospy.get_param("~dataset_id", os.environ.get("DATASET_ID", "urbannav"))).lower()
        self.camera_to_body_extrinsic = E2O_OPTICAL_CAMERA_T_BODY if self.dataset_id == "e2o" else RIGHT_CAMERA_T_IMU
        self.pose_scale = float(rospy.get_param("~pose_scale", 1.0))
        self.yaw_offset_rad = math.radians(float(rospy.get_param("~yaw_offset_deg", 0.0)))
        self.yaw_offset_T = yaw_rotation(self.yaw_offset_rad)
        self.align_to_gt = as_bool(rospy.get_param("~align_to_gt", False))
        self.gt_odom_topic = rospy.get_param("~gt_odom_topic", "/ground_truth_odometry")
        self.align_min_gt_motion_m = float(rospy.get_param("~align_min_gt_motion_m", rospy.get_param("~align_min_motion_m", 5.0)))
        self.align_min_orb_motion_m = float(rospy.get_param("~align_min_orb_motion_m", 0.05))
        self.align_scale = 1.0
        self.align_yaw_rad = 0.0
        self._latest_gt_T = None
        self._gt_origin_inv = None
        self._align_ready = False

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
        self._last_wall_pose_sec = None
        self._last_stamp = None
        self._last_position = None
        self._first_body_inv = None
        self._total_received = 0
        self._total_published = 0
        self._total_rejected = 0

        self._sub = rospy.Subscriber(self.input_topic, PoseStamped, self._pose_cb, queue_size=50)
        self._gt_sub = None
        if self.align_to_gt:
            self._gt_sub = rospy.Subscriber(self.gt_odom_topic, Odometry, self._gt_cb, queue_size=50)
        self._watchdog = rospy.Timer(rospy.Duration(1.0), self._watchdog_cb)

        rospy.loginfo(
            "[ORB-SLAM3 PoseRepublisher] input=%s odom=%s path=%s frame=%s child=%s dataset=%s body_extrinsic=%s normalize=%s scale=%.3f yaw_offset=%.2fdeg gt_align=%s jump_guard=%.1fm/%.1fmps",
            self.input_topic,
            self.output_odom_topic,
            self.output_path_topic,
            self.world_frame_id,
            self.child_frame_id,
            self.dataset_id,
            self.use_camera_to_body_extrinsic,
            self.normalize_to_start,
            self.pose_scale,
            math.degrees(self.yaw_offset_rad),
            self.align_to_gt,
            self.max_interframe_translation,
            self.max_speed_mps,
        )

    def _gt_cb(self, msg: Odometry):
        self._latest_gt_T = pose_to_mat(msg.pose.pose)

    def _apply_gt_alignment(self, T_world_body: np.ndarray) -> np.ndarray:
        if not self.align_to_gt or self._latest_gt_T is None:
            return T_world_body

        if self._gt_origin_inv is None:
            self._gt_origin_inv = invert_rigid(self._latest_gt_T)
            rospy.loginfo("[ORB-SLAM3 PoseRepublisher] Locked GT pose for ORB similarity alignment")

        T_gt_rel = self._gt_origin_inv @ self._latest_gt_T
        orb_xy = T_world_body[:2, 3]
        gt_xy = T_gt_rel[:2, 3]
        orb_norm = float(np.linalg.norm(orb_xy))
        gt_norm = float(np.linalg.norm(gt_xy))

        if orb_norm >= self.align_min_orb_motion_m and gt_norm >= self.align_min_gt_motion_m:
            orb_yaw = math.atan2(float(orb_xy[1]), float(orb_xy[0]))
            gt_yaw = math.atan2(float(gt_xy[1]), float(gt_xy[0]))
            self.align_scale = gt_norm / orb_norm
            self.align_yaw_rad = math.atan2(math.sin(gt_yaw - orb_yaw), math.cos(gt_yaw - orb_yaw))
            if not self._align_ready:
                rospy.loginfo(
                    "[ORB-SLAM3 PoseRepublisher] GT alignment ready scale=%.3f yaw=%.2fdeg orb_motion=%.2fm gt_motion=%.2fm",
                    self.align_scale,
                    math.degrees(self.align_yaw_rad),
                    orb_norm,
                    gt_norm,
                )
            self._align_ready = True

        if not self._align_ready:
            return T_world_body

        aligned = yaw_rotation(self.align_yaw_rad) @ T_world_body
        aligned[:2, 3] *= self.align_scale
        return aligned

    def _convert_camera_pose_to_body(self, msg: PoseStamped) -> np.ndarray:
        T_world_camera = pose_to_mat(msg.pose)
        if self.use_camera_to_body_extrinsic:
            T_world_body = T_world_camera @ invert_rigid(self.camera_to_body_extrinsic)
        else:
            T_world_body = T_world_camera

        if self.normalize_to_start:
            if self._first_body_inv is None:
                self._first_body_inv = invert_rigid(T_world_body)
                rospy.loginfo("[ORB-SLAM3 PoseRepublisher] Locked first ORB body pose as camera_init origin")
            T_world_body = self._first_body_inv @ T_world_body
        if self.pose_scale != 1.0:
            T_world_body[:3, 3] *= self.pose_scale
        if self.yaw_offset_rad != 0.0:
            T_world_body = self.yaw_offset_T @ T_world_body
        T_world_body = self._apply_gt_alignment(T_world_body)
        return T_world_body

    def _passes_jump_guard(self, stamp: rospy.Time, position: np.ndarray) -> bool:
        if self._last_position is None or self._last_stamp is None:
            return True
        dt = (stamp - self._last_stamp).to_sec()
        jump = float(np.linalg.norm(position - self._last_position))
        if self.max_interframe_translation > 0.0 and jump > self.max_interframe_translation:
            rospy.logwarn_throttle(
                2.0,
                "[ORB-SLAM3 PoseRepublisher] Rejected pose jump %.2fm > %.2fm",
                jump,
                self.max_interframe_translation,
            )
            return False
        if dt > 1.0e-3 and self.max_speed_mps > 0.0:
            speed = jump / dt
            if speed > self.max_speed_mps:
                rospy.logwarn_throttle(
                    2.0,
                    "[ORB-SLAM3 PoseRepublisher] Rejected pose speed %.2fm/s > %.2fm/s",
                    speed,
                    self.max_speed_mps,
                )
                return False
        return True

    def _pose_cb(self, msg: PoseStamped):
        with self._lock:
            self._total_received += 1
            if self.dataset_id == "e2o":
                stamp = rospy.Time.now()
            else:
                stamp = msg.header.stamp if msg.header.stamp != rospy.Time(0) else rospy.Time.now()

            try:
                T_body = self._convert_camera_pose_to_body(msg)
            except Exception as exc:  # keep node alive if a bad quaternion arrives
                self._total_rejected += 1
                rospy.logwarn_throttle(2.0, "[ORB-SLAM3 PoseRepublisher] Bad pose conversion: %s", exc)
                self._pub_status.publish(String(data="REJECTED"))
                return

            if not is_finite_matrix(T_body):
                self._total_rejected += 1
                rospy.logwarn_throttle(2.0, "[ORB-SLAM3 PoseRepublisher] Rejected non-finite pose")
                self._pub_status.publish(String(data="REJECTED"))
                return

            position = T_body[:3, 3].copy()
            if not self._passes_jump_guard(stamp, position):
                self._total_rejected += 1
                self._pub_status.publish(String(data="REJECTED"))
                return

            pose_body = mat_to_pose(T_body)
            p = pose_body.position
            q = pose_body.orientation

            odom = Odometry()
            odom.header.stamp = stamp
            odom.header.frame_id = self.world_frame_id
            odom.child_frame_id = self.child_frame_id
            odom.pose.pose = pose_body
            # Non-zero covariance prevents downstream tools treating it as unknown.
            odom.pose.covariance = [0.0] * 36
            odom.pose.covariance[0] = 1e-3
            odom.pose.covariance[7] = 1e-3
            odom.pose.covariance[14] = 1e-3
            odom.pose.covariance[21] = 1e-2
            odom.pose.covariance[28] = 1e-2
            odom.pose.covariance[35] = 1e-2
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
            ps.pose = pose_body
            self._path.poses.append(ps)
            if len(self._path.poses) > MAX_PATH_LENGTH:
                self._path.poses = self._path.poses[-MAX_PATH_LENGTH:]
            self._path.header.stamp = stamp
            self._pub_path.publish(self._path)
            if self._pub_path_legacy:
                self._pub_path_legacy.publish(self._path)

            self._last_wall_pose_sec = rospy.Time.now().to_sec()
            self._last_stamp = stamp
            self._last_position = position
            self._total_published += 1
            self._pub_status.publish(String(data="TRACKING"))
            if self._total_published % 100 == 0:
                rospy.loginfo(
                    "[ORB-SLAM3 PoseRepublisher] received=%d published=%d rejected=%d path_len=%d latest=%.3f pos=(%.2f %.2f %.2f)",
                    self._total_received,
                    self._total_published,
                    self._total_rejected,
                    len(self._path.poses),
                    stamp.to_sec(),
                    p.x,
                    p.y,
                    p.z,
                )

    def _watchdog_cb(self, _event):
        with self._lock:
            now_sec = rospy.Time.now().to_sec()
            if now_sec == 0.0:
                return
            if self._last_wall_pose_sec is None:
                status = "WAITING"
            else:
                status = "LOST" if (now_sec - self._last_wall_pose_sec) > 2.0 else "TRACKING"
            self._pub_status.publish(String(data=status))


def main():
    rospy.init_node("orbslam3_pose_republisher_node", anonymous=False)
    PoseRepublisher()
    rospy.loginfo("[ORB-SLAM3 PoseRepublisher] Running.")
    rospy.spin()


if __name__ == "__main__":
    main()
