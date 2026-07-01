#!/usr/bin/env python3
"""
Visualize any number of trajectory CSVs in RViz (ROS1 / Noetic).

Examples:
  python3 compare_csv_trajectories_multi.py \
    --csv-a lvisam.csv --name-a LVISAM \
    --csv-b fastlio2.csv --name-b FASTLIO2 \
    --csv-c fastlivo2.csv --name-c FASTLIVO2 \
    --csv-d orbslam3.csv --name-d ORB-SLAM3 \
    --align se2 --frame map

All trajectories are published together:
  /csv_compare/markers       MarkerArray  <-- use this in RViz
  /csv_compare/path_a
  /csv_compare/path_b
  /csv_compare/path_c
  ...

CSV format:
  Supports x_m,y_m,z_m + qx,qy,qz,qw and common alternatives:
  x,y,z; position_x,position_y,position_z;
  timestamp_s/timestamp/time/timestamp_ns;
  qx,qy,qz,qw or roll,pitch,yaw.

Alignment:
  --align none         show original coordinates
  --align translation  place every trajectory after A at A's first XYZ
  --align se2          place every trajectory after A at A's first XYZ + yaw
"""

import argparse
import csv
import math
import os
import re
import string
import sys

import rospy
from geometry_msgs.msg import PoseStamped, Point
from nav_msgs.msg import Path
from std_msgs.msg import ColorRGBA
from visualization_msgs.msg import Marker, MarkerArray


# Distinct, RViz-friendly RGBA colours. More trajectories reuse the palette.
PALETTE = [
    (0.05, 0.75, 1.00, 1.00),  # cyan
    (1.00, 0.42, 0.05, 1.00),  # orange
    (0.25, 0.95, 0.35, 1.00),  # green
    (0.95, 0.20, 0.85, 1.00),  # magenta
    (1.00, 0.95, 0.15, 1.00),  # yellow
    (0.55, 0.35, 1.00, 1.00),  # purple
    (0.10, 0.95, 0.85, 1.00),  # teal
    (1.00, 0.30, 0.30, 1.00),  # red
]


def finite_float(value, default=None):
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def canonical_header(name):
    return (name or "").replace("\ufeff", "").strip().lower()


def find_column(headers, aliases):
    normalized = {canonical_header(h): h for h in headers if h}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def normalize_quaternion(qx, qy, qz, qw):
    norm = math.sqrt(qx*qx + qy*qy + qz*qz + qw*qw)
    if norm < 1e-12:
        return 0.0, 0.0, 0.0, 1.0
    return qx / norm, qy / norm, qz / norm, qw / norm


def yaw_from_quaternion(qx, qy, qz, qw):
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    return math.atan2(siny_cosp, cosy_cosp)


def euler_to_quaternion(roll, pitch, yaw):
    cr, sr = math.cos(roll / 2.0), math.sin(roll / 2.0)
    cp, sp = math.cos(pitch / 2.0), math.sin(pitch / 2.0)
    cy, sy = math.cos(yaw / 2.0), math.sin(yaw / 2.0)
    return normalize_quaternion(
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    )


def q_multiply(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw - az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def load_csv(path, stride):
    poses = []

    with open(path, "r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise RuntimeError(f"{path}: CSV has no header row.")

        headers = reader.fieldnames
        col_time_s = find_column(headers, ("timestamp_s", "timestamp", "time", "t", "stamp"))
        col_time_ns = find_column(headers, ("timestamp_ns", "time_ns", "stamp_ns"))
        col_x = find_column(headers, ("x_m", "x", "position_x", "pos_x", "px"))
        col_y = find_column(headers, ("y_m", "y", "position_y", "pos_y", "py"))
        col_z = find_column(headers, ("z_m", "z", "position_z", "pos_z", "pz"))

        col_qx = find_column(headers, ("qx", "orientation_x", "quat_x", "q_x"))
        col_qy = find_column(headers, ("qy", "orientation_y", "quat_y", "q_y"))
        col_qz = find_column(headers, ("qz", "orientation_z", "quat_z", "q_z"))
        col_qw = find_column(headers, ("qw", "orientation_w", "quat_w", "q_w"))
        col_roll = find_column(headers, ("roll_rad", "roll", "r"))
        col_pitch = find_column(headers, ("pitch_rad", "pitch", "p"))
        col_yaw = find_column(headers, ("yaw_rad", "yaw", "heading", "psi"))

        missing = [name for name, col in (("x", col_x), ("y", col_y), ("z", col_z)) if col is None]
        if missing:
            raise RuntimeError(
                f"{path}: missing {', '.join(missing)} columns. Found: {', '.join(headers)}"
            )

        has_quaternion = all((col_qx, col_qy, col_qz, col_qw))
        has_euler = all((col_roll, col_pitch, col_yaw))
        if not has_quaternion and not has_euler:
            raise RuntimeError(
                f"{path}: need qx,qy,qz,qw or roll,pitch,yaw. Found: {', '.join(headers)}"
            )

        for row_index, row in enumerate(reader):
            if row_index % stride != 0:
                continue

            x = finite_float(row.get(col_x))
            y = finite_float(row.get(col_y))
            z = finite_float(row.get(col_z))
            if any(v is None for v in (x, y, z)):
                continue

            if col_time_s is not None:
                stamp = finite_float(row.get(col_time_s), float(row_index))
            elif col_time_ns is not None:
                ns = finite_float(row.get(col_time_ns))
                stamp = ns / 1e9 if ns is not None else float(row_index)
            else:
                stamp = float(row_index)

            if has_quaternion:
                qx = finite_float(row.get(col_qx))
                qy = finite_float(row.get(col_qy))
                qz = finite_float(row.get(col_qz))
                qw = finite_float(row.get(col_qw))
                if any(v is None for v in (qx, qy, qz, qw)):
                    continue
                qx, qy, qz, qw = normalize_quaternion(qx, qy, qz, qw)
            else:
                roll = finite_float(row.get(col_roll))
                pitch = finite_float(row.get(col_pitch))
                yaw = finite_float(row.get(col_yaw))
                if any(v is None for v in (roll, pitch, yaw)):
                    continue
                qx, qy, qz, qw = euler_to_quaternion(roll, pitch, yaw)

            poses.append({
                "timestamp_s": stamp,
                "x": x, "y": y, "z": z,
                "qx": qx, "qy": qy, "qz": qz, "qw": qw,
            })

    if not poses:
        raise RuntimeError(f"{path}: no valid pose rows found.")
    return poses


def align_to_reference(reference_poses, poses, mode):
    """Transform one trajectory so its first pose matches reference's first pose."""
    if mode == "none":
        return [dict(p) for p in poses]

    ref0, p0 = reference_poses[0], poses[0]
    theta = 0.0
    if mode == "se2":
        theta = (
            yaw_from_quaternion(ref0["qx"], ref0["qy"], ref0["qz"], ref0["qw"])
            - yaw_from_quaternion(p0["qx"], p0["qy"], p0["qz"], p0["qw"])
        )

    c, s = math.cos(theta), math.sin(theta)
    p0_rx = c * p0["x"] - s * p0["y"]
    p0_ry = s * p0["x"] + c * p0["y"]
    tx = ref0["x"] - p0_rx
    ty = ref0["y"] - p0_ry
    tz = ref0["z"] - p0["z"]
    q_align = (0.0, 0.0, math.sin(theta / 2.0), math.cos(theta / 2.0))

    result = []
    for p in poses:
        out = dict(p)
        out["x"] = c * p["x"] - s * p["y"] + tx
        out["y"] = s * p["x"] + c * p["y"] + ty
        out["z"] = p["z"] + tz
        out["qx"], out["qy"], out["qz"], out["qw"] = normalize_quaternion(
            *q_multiply(q_align, (p["qx"], p["qy"], p["qz"], p["qw"]))
        )
        result.append(out)
    return result


def to_path(poses, frame, now):
    path = Path()
    path.header.frame_id = frame
    path.header.stamp = now

    for p in poses:
        pose = PoseStamped()
        pose.header.frame_id = frame
        pose.header.stamp = rospy.Time.from_sec(p["timestamp_s"])
        pose.pose.position.x = p["x"]
        pose.pose.position.y = p["y"]
        pose.pose.position.z = p["z"]
        pose.pose.orientation.x = p["qx"]
        pose.pose.orientation.y = p["qy"]
        pose.pose.orientation.z = p["qz"]
        pose.pose.orientation.w = p["qw"]
        path.poses.append(pose)
    return path


def line_marker(marker_id, poses, frame, now, color, width):
    marker = Marker()
    marker.header.frame_id = frame
    marker.header.stamp = now
    marker.ns = "csv_trajectory"
    marker.id = marker_id
    marker.type = Marker.LINE_STRIP
    marker.action = Marker.ADD
    marker.pose.orientation.w = 1.0
    marker.scale.x = width
    marker.color = ColorRGBA(*color)
    marker.lifetime = rospy.Duration(0)

    for p in poses:
        marker.points.append(Point(p["x"], p["y"], p["z"]))
    return marker


def sphere_marker(marker_id, p, frame, now, color, scale=0.35):
    marker = Marker()
    marker.header.frame_id = frame
    marker.header.stamp = now
    marker.ns = "csv_trajectory_points"
    marker.id = marker_id
    marker.type = Marker.SPHERE
    marker.action = Marker.ADD
    marker.pose.position.x = p["x"]
    marker.pose.position.y = p["y"]
    marker.pose.position.z = p["z"]
    marker.pose.orientation.w = 1.0
    marker.scale.x = marker.scale.y = marker.scale.z = scale
    marker.color = ColorRGBA(*color)
    marker.lifetime = rospy.Duration(0)
    return marker


def text_marker(marker_id, p, frame, now, color, text):
    marker = Marker()
    marker.header.frame_id = frame
    marker.header.stamp = now
    marker.ns = "csv_trajectory_labels"
    marker.id = marker_id
    marker.type = Marker.TEXT_VIEW_FACING
    marker.action = Marker.ADD
    marker.pose.position.x = p["x"]
    marker.pose.position.y = p["y"]
    marker.pose.position.z = p["z"] + 0.45
    marker.pose.orientation.w = 1.0
    marker.scale.z = 0.32
    marker.color = ColorRGBA(*color)
    marker.text = text
    marker.lifetime = rospy.Duration(0)
    return marker


def extract_trajectory_arguments(argv):
    """
    Allows arbitrary --csv-a, --csv-b ... --csv-z options without hardcoding
    their count in argparse. Matching --name-a ... --name-z are optional.
    """
    csv_values = {}
    name_values = {}
    remaining = []
    i = 0
    csv_re = re.compile(r"^--csv-([a-z])$")
    name_re = re.compile(r"^--name-([a-z])$")

    while i < len(argv):
        item = argv[i]
        match_csv = csv_re.match(item)
        match_name = name_re.match(item)

        if match_csv or match_name:
            if i + 1 >= len(argv):
                raise ValueError(f"{item} requires a value.")
            letter = (match_csv or match_name).group(1)
            value = argv[i + 1]
            if match_csv:
                csv_values[letter] = value
            else:
                name_values[letter] = value
            i += 2
        else:
            remaining.append(item)
            i += 1

    if len(csv_values) < 2:
        raise ValueError(
            "Provide at least two trajectories, for example: "
            "--csv-a lvisam.csv --csv-b fastlio2.csv"
        )

    trajectories = []
    for letter in sorted(csv_values):
        csv_path = csv_values[letter]
        default_name = "Trajectory " + letter.upper()
        trajectories.append({
            "letter": letter,
            "csv": csv_path,
            "name": name_values.get(letter, default_name),
        })
    return trajectories, remaining


def parse_args(argv):
    trajectories, remaining = extract_trajectory_arguments(argv)

    parser = argparse.ArgumentParser(
        description="Publish two or more trajectory CSVs to RViz as colored markers."
    )
    parser.add_argument(
        "--align",
        choices=("none", "translation", "se2"),
        default="none",
        help=(
            "Align every trajectory after A to A's first pose: "
            "none=raw coordinates; translation=initial XYZ; se2=initial XYZ+yaw."
        ),
    )
    parser.add_argument("--frame", default="map")
    parser.add_argument("--topic-ns", default="/csv_compare")
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--line-width", type=float, default=0.08)
    args = parser.parse_args(remaining)
    return args, trajectories


def main():
    args, trajectory_specs = parse_args(sys.argv[1:])

    if args.stride < 1:
        raise ValueError("--stride must be >= 1")
    if args.line_width <= 0:
        raise ValueError("--line-width must be > 0")

    for spec in trajectory_specs:
        if not os.path.isfile(spec["csv"]):
            raise FileNotFoundError(f"CSV not found: {spec['csv']}")

    rospy.init_node("compare_csv_trajectories", anonymous=False)

    # CSV A is the visual reference for optional alignment.
    loaded = []
    for spec in trajectory_specs:
        poses = load_csv(spec["csv"], args.stride)
        loaded.append({**spec, "poses": poses})

    reference_poses = loaded[0]["poses"]
    for index, item in enumerate(loaded):
        if index > 0:
            item["poses"] = align_to_reference(reference_poses, item["poses"], args.align)

    ns = args.topic_ns.rstrip("/")
    path_publishers = {}
    for item in loaded:
        path_publishers[item["letter"]] = rospy.Publisher(
            f"{ns}/path_{item['letter']}", Path, queue_size=1, latch=True
        )
    marker_pub = rospy.Publisher(f"{ns}/markers", MarkerArray, queue_size=1, latch=True)

    now = rospy.Time.now()
    markers = MarkerArray()

    for index, item in enumerate(loaded):
        color = PALETTE[index % len(PALETTE)]
        poses = item["poses"]
        letter = item["letter"]
        name = item["name"]

        path_publishers[letter].publish(to_path(poses, args.frame, now))
        base_id = index * 10
        markers.markers.extend([
            line_marker(base_id, poses, args.frame, now, color, args.line_width),
            sphere_marker(base_id + 1, poses[0], args.frame, now, color, 0.38),
            sphere_marker(base_id + 2, poses[-1], args.frame, now, color, 0.24),
            text_marker(base_id + 3, poses[0], args.frame, now, color, f"{name} (start)"),
        ])

        rospy.loginfo(
            "%s: %d poses | topic %s/path_%s",
            name, len(poses), ns, letter
        )

    marker_pub.publish(markers)
    rospy.loginfo(
        "Published %d trajectories. RViz Fixed Frame='%s', MarkerArray='%s/markers'. "
        "Alignment=%s",
        len(loaded), args.frame, ns, args.align
    )
    rospy.spin()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
