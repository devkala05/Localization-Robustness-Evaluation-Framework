#!/usr/bin/env python3
"""
UrbanNav ground-truth publisher for RViz and evaluation.

This version publishes the COMPLETE fixed GT route on /ground_truth_path.
It does not clip/generate the visible GT path using current /clock time.
Default yaw_offset_deg is 0 deg; run scripts can override with GT_YAW_OFFSET_DEG.
/ground_truth_odometry still follows current bag /clock for the live GT car pose.
"""

import math
import os
from bisect import bisect_left, bisect_right
from typing import List, Optional, Tuple

import rospy
from geometry_msgs.msg import PoseStamped, Quaternion
from nav_msgs.msg import Odometry, Path

try:
    from pyproj import Transformer
except ImportError:
    Transformer = None

WGS84_A = 6378137.0
WGS84_E2 = 6.69437999014e-3


def dms_to_deg(degrees: float, minutes: float, seconds: float) -> float:
    sign = -1.0 if degrees < 0 else 1.0
    return sign * (abs(degrees) + minutes / 60.0 + seconds / 3600.0)


def ecef_from_lla_fallback(lat_deg: float, lon_deg: float, height: float) -> Tuple[float, float, float]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    normal = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    x = (normal + height) * cos_lat * math.cos(lon)
    y = (normal + height) * cos_lat * math.sin(lon)
    z = (normal * (1.0 - WGS84_E2) + height) * sin_lat
    return x, y, z


def enu_from_ecef_delta(dx: float, dy: float, dz: float, ref_lat_deg: float, ref_lon_deg: float) -> Tuple[float, float, float]:
    lat = math.radians(ref_lat_deg)
    lon = math.radians(ref_lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)
    east = -sin_lon * dx + cos_lon * dy
    north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
    up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
    return east, north, up


class GroundTruthConverter:
    def __init__(self):
        self._transformer = Transformer.from_crs("EPSG:4979", "EPSG:4978", always_xy=True) if Transformer else None

    def ecef_from_lla(self, lat_deg: float, lon_deg: float, height: float) -> Tuple[float, float, float]:
        if self._transformer:
            return self._transformer.transform(lon_deg, lat_deg, height)
        return ecef_from_lla_fallback(lat_deg, lon_deg, height)


def parse_ground_truth(path: str) -> List[dict]:
    samples = []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) < 20:
                continue
            try:
                utc = float(parts[0])
                lat = dms_to_deg(float(parts[3]), float(parts[4]), float(parts[5]))
                lon = dms_to_deg(float(parts[6]), float(parts[7]), float(parts[8]))
                height = float(parts[9])
                roll = float(parts[16])
                pitch = float(parts[17])
                heading = float(parts[18])
            except ValueError:
                continue
            samples.append({
                "utc": utc,
                "lat": lat,
                "lon": lon,
                "height": height,
                "roll": roll,
                "pitch": pitch,
                "heading": heading,
            })
    samples.sort(key=lambda s: s["utc"])
    return samples


def yaw_quaternion(yaw: float) -> Quaternion:
    half = 0.5 * yaw
    q = Quaternion()
    q.w = math.cos(half)
    q.z = math.sin(half)
    return q


def rotate_xy(x: float, y: float, yaw_offset_rad: float) -> Tuple[float, float]:
    c = math.cos(yaw_offset_rad)
    s = math.sin(yaw_offset_rad)
    return c * x - s * y, s * x + c * y


def build_path(samples: List[dict], frame_id: str, rotate_to_initial_heading: bool, yaw_offset_deg: float, z_offset: float) -> Path:
    converter = GroundTruthConverter()
    ref = samples[0]
    ref_ecef = converter.ecef_from_lla(ref["lat"], ref["lon"], ref["height"])

    heading_rad = math.radians(ref["heading"]) if rotate_to_initial_heading else 0.0
    forward_e = math.sin(heading_rad)
    forward_n = math.cos(heading_rad)
    right_e = math.cos(heading_rad)
    right_n = -math.sin(heading_rad)
    yaw_offset_rad = math.radians(yaw_offset_deg)

    path_msg = Path()
    path_msg.header.frame_id = frame_id

    for sample in samples:
        ecef = converter.ecef_from_lla(sample["lat"], sample["lon"], sample["height"])
        east, north, up = enu_from_ecef_delta(
            ecef[0] - ref_ecef[0],
            ecef[1] - ref_ecef[1],
            ecef[2] - ref_ecef[2],
            ref["lat"],
            ref["lon"],
        )

        # Original UrbanNav local frame used in this project: x=right, y=forward.
        x = east * right_e + north * right_n
        y = east * forward_e + north * forward_n
        x, y = rotate_xy(x, y, yaw_offset_rad)

        pose = PoseStamped()
        pose.header.frame_id = frame_id
        pose.header.stamp = rospy.Time.from_sec(sample["utc"])
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = up + z_offset
        pose.pose.orientation = yaw_quaternion(math.radians(sample["heading"] - ref["heading"] + yaw_offset_deg))
        path_msg.poses.append(pose)

    return path_msg


def nearest_pose(path_msg: Path, stamps: List[float], stamp: rospy.Time) -> Optional[PoseStamped]:
    if not path_msg.poses:
        return None
    target = stamp.to_sec()
    if target <= 0.0:
        return path_msg.poses[0]
    idx = bisect_left(stamps, target)
    candidates = []
    if idx < len(path_msg.poses):
        candidates.append(path_msg.poses[idx])
    if idx > 0:
        candidates.append(path_msg.poses[idx - 1])
    return min(candidates, key=lambda pose: abs(pose.header.stamp.to_sec() - target)) if candidates else path_msg.poses[-1]


def odometry_from_pose(pose: PoseStamped, stamp: rospy.Time, child_frame_id: str) -> Odometry:
    odom = Odometry()
    odom.header.frame_id = pose.header.frame_id
    odom.header.stamp = stamp
    odom.child_frame_id = child_frame_id
    odom.pose.pose = pose.pose
    return odom


def main():
    rospy.init_node("ground_truth_path_node", anonymous=False)
    gt_path = rospy.get_param("~ground_truth_path", "/data/UrbanNav_TST_GT_raw.txt")
    topic = rospy.get_param("~topic", "/ground_truth_path")
    full_topic = rospy.get_param("~full_topic", "/ground_truth_path_full")
    odom_topic = rospy.get_param("~odom_topic", "/ground_truth_odometry")
    frame_id = rospy.get_param("~frame_id", "camera_init")
    child_frame_id = rospy.get_param("~child_frame_id", "ground_truth_car")
    publish_rate = float(rospy.get_param("~publish_rate", 10.0))
    rotate_to_initial_heading = bool(rospy.get_param("~rotate_to_initial_heading", True))
    yaw_offset_deg = float(rospy.get_param("~yaw_offset_deg", 0.0))
    z_offset = float(rospy.get_param("~z_offset", 0.0))
    publish_full = bool(rospy.get_param("~publish_full_path", True))

    if not os.path.isfile(gt_path):
        rospy.logerr("[GroundTruthPath] File not found: %s", gt_path)
        return
    samples = parse_ground_truth(gt_path)
    if not samples:
        rospy.logerr("[GroundTruthPath] No valid samples in %s", gt_path)
        return

    full_path = build_path(samples, frame_id, rotate_to_initial_heading, yaw_offset_deg, z_offset)
    stamps = [pose.header.stamp.to_sec() for pose in full_path.poses]

    live_pub = rospy.Publisher(topic, Path, queue_size=1)
    full_pub = rospy.Publisher(full_topic, Path, queue_size=1, latch=True)
    odom_pub = rospy.Publisher(odom_topic, Odometry, queue_size=10)

    rospy.loginfo(
        "[GroundTruthPath] %d poses, live=%s full=%s odom=%s frame=%s yaw_offset=%.1f deg",
        len(full_path.poses), topic, full_topic, odom_topic, frame_id, yaw_offset_deg,
    )

    # Publish the complete GT path as a fixed/static visual path.
    # Do not clip it by /clock; the user requested complete GT, not time-generated GT.
    full_path.header.stamp = rospy.Time(0)
    live_pub.publish(full_path)
    if publish_full:
        full_pub.publish(full_path)

    rate = rospy.Rate(publish_rate)
    while not rospy.is_shutdown():
        now = rospy.Time.now()
        full_path.header.stamp = rospy.Time(0)
        live_pub.publish(full_path)

        # Keep live GT odometry synced with bag time for the car marker only.
        pose = nearest_pose(full_path, stamps, now)
        if pose:
            odom_pub.publish(odometry_from_pose(pose, now, child_frame_id))
        rate.sleep()


if __name__ == "__main__":
    main()
