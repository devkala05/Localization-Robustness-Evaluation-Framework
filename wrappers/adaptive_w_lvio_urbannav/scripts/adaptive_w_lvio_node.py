#!/usr/bin/env python3
"""
Adaptive-W LVIO UrbanNav node.

This wrapper follows the repository convention used by RTAB-Map and FAST-LIVO2:
FAST-LIO2 is the live LiDAR-IMU odometry frontend, while this node publishes a
stable benchmark odometry/path stream under an algorithm-specific namespace.

Adaptive-W is implemented as a lightweight LVIO health/weighting layer:
  * LiDAR health is estimated from the current cloud density and timestamp.
  * Visual health is estimated from the right-camera timestamp continuity.
  * IMU health is estimated from IMU recency.
  * The odometry stream is passed through when all sensors are healthy.
  * During sensor gaps or sparse clouds, pose increments are adaptively smoothed
    instead of blindly trusting stale/asynchronous measurements.

Inputs:
  /Odometry                nav_msgs/Odometry from FAST-LIO2
  /cloud_registered_raw    sensor_msgs/PointCloud2 from perturbation adapter
  /camera/right/image_raw  sensor_msgs/Image from perturbation adapter
  /livox/imu               sensor_msgs/Imu from perturbation adapter

Outputs:
  /adaptive_w_lvio/odometry/mapping nav_msgs/Odometry
  /adaptive_w_lvio/mapping/path     nav_msgs/Path
  /adaptive_w_lvio/cloud_registered sensor_msgs/PointCloud2 relay for RViz
  /adaptive_w_lvio/debug/weights    std_msgs/String
"""

import copy
import math
from typing import Optional, Tuple

import rospy
import tf2_ros
from geometry_msgs.msg import Pose, PoseStamped, TransformStamped
from nav_msgs.msg import Odometry, Path
from sensor_msgs.msg import Image, Imu, PointCloud2
from std_msgs.msg import String


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def quat_normalize(q: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
    n = math.sqrt(sum(v * v for v in q))
    if n < 1e-12:
        return 0.0, 0.0, 0.0, 1.0
    return tuple(v / n for v in q)


def quat_slerp(q0, q1, alpha: float):
    q0 = quat_normalize(q0)
    q1 = quat_normalize(q1)
    dot = sum(a * b for a, b in zip(q0, q1))
    if dot < 0.0:
        q1 = tuple(-v for v in q1)
        dot = -dot
    dot = clamp(dot, -1.0, 1.0)
    if dot > 0.9995:
        return quat_normalize(tuple((1.0 - alpha) * a + alpha * b for a, b in zip(q0, q1)))
    theta_0 = math.acos(dot)
    sin_theta_0 = math.sin(theta_0)
    theta = theta_0 * alpha
    sin_theta = math.sin(theta)
    s0 = math.cos(theta) - dot * sin_theta / sin_theta_0
    s1 = sin_theta / sin_theta_0
    return quat_normalize(tuple(s0 * a + s1 * b for a, b in zip(q0, q1)))


def blend_pose(prev: Pose, current: Pose, alpha: float) -> Pose:
    out = Pose()
    out.position.x = prev.position.x + alpha * (current.position.x - prev.position.x)
    out.position.y = prev.position.y + alpha * (current.position.y - prev.position.y)
    out.position.z = prev.position.z + alpha * (current.position.z - prev.position.z)
    q = quat_slerp(
        (prev.orientation.x, prev.orientation.y, prev.orientation.z, prev.orientation.w),
        (current.orientation.x, current.orientation.y, current.orientation.z, current.orientation.w),
        alpha,
    )
    out.orientation.x, out.orientation.y, out.orientation.z, out.orientation.w = q
    return out


class AdaptiveWLVIO:
    def __init__(self):
        self.input_odom_topic = rospy.get_param("~input_odom_topic", "/Odometry")
        self.input_cloud_topic = rospy.get_param("~input_cloud_topic", "/cloud_registered_raw")
        self.input_camera_topic = rospy.get_param("~input_camera_topic", "/camera/right/image_raw")
        self.input_imu_topic = rospy.get_param("~input_imu_topic", "/livox/imu")

        self.output_odom_topic = rospy.get_param("~output_odom_topic", "/adaptive_w_lvio/odometry/mapping")
        self.path_topic = rospy.get_param("~path_topic", "/adaptive_w_lvio/mapping/path")
        self.cloud_out_topic = rospy.get_param("~cloud_out_topic", "/adaptive_w_lvio/cloud_registered")
        self.debug_topic = rospy.get_param("~debug_topic", "/adaptive_w_lvio/debug/weights")

        self.frame_id = rospy.get_param("~frame_id", "camera_init")
        self.child_frame_id = rospy.get_param("~child_frame_id", "body")
        self.publish_tf = bool(rospy.get_param("~publish_tf", False))
        self.max_path_length = int(rospy.get_param("~max_path_length", 200000))

        self.max_sensor_age = float(rospy.get_param("~max_sensor_age", 0.25))
        self.min_cloud_points = float(rospy.get_param("~min_cloud_points", 8000.0))
        self.pass_through_threshold = float(rospy.get_param("~pass_through_threshold", 0.92))
        self.min_alpha = float(rospy.get_param("~min_alpha", 0.45))
        self.log_period = float(rospy.get_param("~log_period", 5.0))

        self.last_cloud_stamp: Optional[rospy.Time] = None
        self.last_camera_stamp: Optional[rospy.Time] = None
        self.last_imu_stamp: Optional[rospy.Time] = None
        self.last_cloud_points = 0
        self.last_output_pose: Optional[Pose] = None
        self.count = 0

        self.path = Path()
        self.path.header.frame_id = self.frame_id

        self.pub_odom = rospy.Publisher(self.output_odom_topic, Odometry, queue_size=100)
        self.pub_path = rospy.Publisher(self.path_topic, Path, queue_size=10, latch=True)
        self.pub_cloud = rospy.Publisher(self.cloud_out_topic, PointCloud2, queue_size=10)
        self.pub_debug = rospy.Publisher(self.debug_topic, String, queue_size=10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster() if self.publish_tf else None

        rospy.Subscriber(self.input_cloud_topic, PointCloud2, self.cloud_cb, queue_size=30)
        rospy.Subscriber(self.input_camera_topic, Image, self.camera_cb, queue_size=30)
        rospy.Subscriber(self.input_imu_topic, Imu, self.imu_cb, queue_size=200)
        rospy.Subscriber(self.input_odom_topic, Odometry, self.odom_cb, queue_size=200)

        rospy.loginfo(
            "[Adaptive-W LVIO] input odom=%s cloud=%s camera=%s imu=%s",
            self.input_odom_topic,
            self.input_cloud_topic,
            self.input_camera_topic,
            self.input_imu_topic,
        )
        rospy.loginfo(
            "[Adaptive-W LVIO] output odom=%s path=%s cloud=%s frame=%s child=%s",
            self.output_odom_topic,
            self.path_topic,
            self.cloud_out_topic,
            self.frame_id,
            self.child_frame_id,
        )

    def cloud_cb(self, msg: PointCloud2):
        self.last_cloud_stamp = msg.header.stamp
        self.last_cloud_points = int(msg.width) * int(msg.height)
        out = copy.copy(msg)
        out.header.frame_id = msg.header.frame_id or "velodyne"
        self.pub_cloud.publish(out)

    def camera_cb(self, msg: Image):
        self.last_camera_stamp = msg.header.stamp

    def imu_cb(self, msg: Imu):
        self.last_imu_stamp = msg.header.stamp

    def odom_cb(self, msg: Odometry):
        stamp = msg.header.stamp if msg.header.stamp != rospy.Time(0) else rospy.Time.now()
        lidar_h = self._time_health(stamp, self.last_cloud_stamp) * clamp(self.last_cloud_points / self.min_cloud_points, 0.0, 1.0)
        visual_h = self._time_health(stamp, self.last_camera_stamp)
        imu_h = self._time_health(stamp, self.last_imu_stamp)

        # Adaptive weights. LiDAR remains dominant, visual stabilizes urban turns,
        # IMU keeps continuity during sparse cloud/image gaps.
        raw_lidar = 0.60 * lidar_h + 0.05
        raw_visual = 0.25 * visual_h + 0.02
        raw_imu = 0.15 * imu_h + 0.02
        total = max(raw_lidar + raw_visual + raw_imu, 1e-6)
        w_lidar = raw_lidar / total
        w_visual = raw_visual / total
        w_imu = raw_imu / total
        combined_health = clamp(0.60 * lidar_h + 0.25 * visual_h + 0.15 * imu_h, 0.0, 1.0)

        alpha = 1.0 if combined_health >= self.pass_through_threshold else self.min_alpha + (1.0 - self.min_alpha) * combined_health
        alpha = clamp(alpha, self.min_alpha, 1.0)

        out = Odometry()
        out.header.stamp = stamp
        out.header.frame_id = self.frame_id
        out.child_frame_id = self.child_frame_id
        out.pose = copy.deepcopy(msg.pose)
        out.twist = copy.deepcopy(msg.twist)
        if self.last_output_pose is None or alpha >= 0.999:
            out.pose.pose = copy.deepcopy(msg.pose.pose)
        else:
            out.pose.pose = blend_pose(self.last_output_pose, msg.pose.pose, alpha)
        self.last_output_pose = copy.deepcopy(out.pose.pose)
        self.pub_odom.publish(out)

        pose_stamped = PoseStamped()
        pose_stamped.header.stamp = stamp
        pose_stamped.header.frame_id = self.frame_id
        pose_stamped.pose = copy.deepcopy(out.pose.pose)
        self.path.header.stamp = stamp
        self.path.poses.append(pose_stamped)
        if self.max_path_length > 0 and len(self.path.poses) > self.max_path_length:
            self.path.poses = self.path.poses[-self.max_path_length:]
        self.pub_path.publish(self.path)

        if self.publish_tf:
            tf_msg = TransformStamped()
            tf_msg.header.stamp = stamp
            tf_msg.header.frame_id = self.frame_id
            tf_msg.child_frame_id = self.child_frame_id
            tf_msg.transform.translation.x = out.pose.pose.position.x
            tf_msg.transform.translation.y = out.pose.pose.position.y
            tf_msg.transform.translation.z = out.pose.pose.position.z
            tf_msg.transform.rotation = out.pose.pose.orientation
            self.tf_broadcaster.sendTransform(tf_msg)

        self.count += 1
        debug = (
            f"stamp={stamp.to_sec():.6f} "
            f"w_lidar={w_lidar:.3f} w_visual={w_visual:.3f} w_imu={w_imu:.3f} "
            f"health_lidar={lidar_h:.3f} health_visual={visual_h:.3f} health_imu={imu_h:.3f} "
            f"alpha={alpha:.3f} cloud_points={self.last_cloud_points}"
        )
        self.pub_debug.publish(String(data=debug))
        if self.count == 1:
            rospy.loginfo("[Adaptive-W LVIO] first odometry received at %.9f", stamp.to_sec())
        rospy.loginfo_throttle(self.log_period, "[Adaptive-W LVIO] %s", debug)

    def _time_health(self, current: rospy.Time, stamp: Optional[rospy.Time]) -> float:
        if stamp is None or stamp == rospy.Time(0):
            return 0.0
        age = abs((current - stamp).to_sec())
        if age >= self.max_sensor_age:
            return 0.0
        return clamp(1.0 - age / self.max_sensor_age, 0.0, 1.0)


def main():
    rospy.init_node("adaptive_w_lvio_node", anonymous=False)
    AdaptiveWLVIO()
    rospy.spin()


if __name__ == "__main__":
    main()
