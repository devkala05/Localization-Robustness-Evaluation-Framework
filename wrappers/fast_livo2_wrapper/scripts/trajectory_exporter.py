#!/usr/bin/env python3
"""
trajectory_exporter.py
=======================
Post-processing tool: reads a recorded output bag and exports the
FAST-LIVO2 trajectory in multiple formats.

Supported export formats
────────────────────────
  TUM   : timestamp tx ty tz qx qy qz qw          (one line per pose)
  CSV   : full pose + velocity + covariance columns
  KITTI : 3×4 rotation+translation matrix per line (12 floats, space-sep)

Usage
─────
  # After pipeline finishes, run inside the container or workspace:
  rosrun fast_livo2_wrapper trajectory_exporter.py \
      _bag:=/data/output/fast_livo2_output.bag \
      _output_dir:=/data/output \
      _format:=tum            # tum | csv | kitti | all

  # Or as a standalone script (no roscore needed):
  python3 trajectory_exporter.py \
      --bag /data/output/fast_livo2_output.bag \
      --output_dir /data/output \
      --format all

Dependencies: rosbag (Python API), numpy, (optional) scipy for SE3 math.
"""

import argparse
import os
import sys
import math

try:
    import rospy
    import rosbag
    _HAS_ROS = True
except ImportError:
    _HAS_ROS = False

try:
    import numpy as np
    _HAS_NP = True
except ImportError:
    _HAS_NP = False
    print("[WARN] numpy not available — KITTI export disabled")


# ─── Quaternion helpers ───────────────────────────────────────────────────────

def quat_to_rot3x3(qx, qy, qz, qw):
    """Return a 3×3 rotation matrix from a unit quaternion (x,y,z,w)."""
    r = [
        [1 - 2*(qy*qy + qz*qz),     2*(qx*qy - qz*qw),     2*(qx*qz + qy*qw)],
        [    2*(qx*qy + qz*qw), 1 - 2*(qx*qx + qz*qz),     2*(qy*qz - qx*qw)],
        [    2*(qx*qz - qy*qw),     2*(qy*qz + qx*qw), 1 - 2*(qx*qx + qy*qy)],
    ]
    return r


# ─── Readers ─────────────────────────────────────────────────────────────────

def read_path_from_bag(bag_path: str, topic: str = "/path"):
    """
    Read all poses from a nav_msgs/Path topic in a rosbag.

    Returns a list of dicts:
        { 't': float, 'x': float, 'y': float, 'z': float,
          'qx': float, 'qy': float, 'qz': float, 'qw': float }

    Only the last Path message is used (FAST-LIVO2 replaces the full path
    on each publish), so this gives the complete final trajectory.
    """
    if not _HAS_ROS:
        raise RuntimeError("rosbag Python API not available")

    poses = []
    last_msg = None

    with rosbag.Bag(bag_path, "r") as bag:
        for _topic, msg, _t in bag.read_messages(topics=[topic]):
            last_msg = msg

    if last_msg is None:
        print(f"[WARN] No messages found on topic '{topic}' in {bag_path}")
        return poses

    for ps in last_msg.poses:
        stamp = ps.header.stamp.to_sec()
        p     = ps.pose.position
        q     = ps.pose.orientation
        poses.append({
            "t": stamp,
            "x": p.x, "y": p.y, "z": p.z,
            "qx": q.x, "qy": q.y, "qz": q.z, "qw": q.w,
        })

    return poses


def read_odometry_from_bag(bag_path: str, topic: str = "/Odometry"):
    """
    Read all nav_msgs/Odometry messages from the bag.
    Returns list of pose dicts (same schema as read_path_from_bag).
    """
    if not _HAS_ROS:
        raise RuntimeError("rosbag Python API not available")

    poses = []
    with rosbag.Bag(bag_path, "r") as bag:
        for _topic, msg, _t in bag.read_messages(topics=[topic]):
            p = msg.pose.pose.position
            q = msg.pose.pose.orientation
            poses.append({
                "t": msg.header.stamp.to_sec(),
                "x": p.x, "y": p.y, "z": p.z,
                "qx": q.x, "qy": q.y, "qz": q.z, "qw": q.w,
            })
    return poses


# ─── Writers ──────────────────────────────────────────────────────────────────

def write_tum(poses: list, filepath: str):
    """Write poses in TUM trajectory format.

    Format: timestamp tx ty tz qx qy qz qw
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write("# TUM trajectory format (FAST-LIVO2 wrapper export)\n")
        f.write("# timestamp tx ty tz qx qy qz qw\n")
        for p in poses:
            f.write(
                f"{p['t']:.9f} "
                f"{p['x']:.9f} {p['y']:.9f} {p['z']:.9f} "
                f"{p['qx']:.9f} {p['qy']:.9f} {p['qz']:.9f} {p['qw']:.9f}\n"
            )
    print(f"[Exporter] TUM → {filepath}  ({len(poses)} poses)")


def write_csv(poses: list, filepath: str):
    """Write poses to CSV with header."""
    import csv as _csv
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fieldnames = ["timestamp", "pos_x", "pos_y", "pos_z", "qx", "qy", "qz", "qw"]
    with open(filepath, "w", newline="") as f:
        writer = _csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in poses:
            writer.writerow({
                "timestamp": f"{p['t']:.9f}",
                "pos_x": f"{p['x']:.9f}",
                "pos_y": f"{p['y']:.9f}",
                "pos_z": f"{p['z']:.9f}",
                "qx": f"{p['qx']:.9f}",
                "qy": f"{p['qy']:.9f}",
                "qz": f"{p['qz']:.9f}",
                "qw": f"{p['qw']:.9f}",
            })
    print(f"[Exporter] CSV  → {filepath}  ({len(poses)} rows)")


def write_kitti(poses: list, filepath: str):
    """Write poses in KITTI odometry format: 12 floats per line (row-major 3×4 [R|t])."""
    if not _HAS_NP:
        print("[WARN] numpy required for KITTI export — skipping")
        return
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        for p in poses:
            R = quat_to_rot3x3(p["qx"], p["qy"], p["qz"], p["qw"])
            line = (
                f"{R[0][0]:.9e} {R[0][1]:.9e} {R[0][2]:.9e} {p['x']:.9e} "
                f"{R[1][0]:.9e} {R[1][1]:.9e} {R[1][2]:.9e} {p['y']:.9e} "
                f"{R[2][0]:.9e} {R[2][1]:.9e} {R[2][2]:.9e} {p['z']:.9e}\n"
            )
            f.write(line)
    print(f"[Exporter] KITTI → {filepath}  ({len(poses)} frames)")


# ─── Entry points ─────────────────────────────────────────────────────────────

def export(bag_path: str, output_dir: str, fmt: str = "all"):
    """Main export routine — reads bag, writes requested format(s)."""
    os.makedirs(output_dir, exist_ok=True)

    # Try /path first (full trajectory), fall back to /Odometry
    print(f"[Exporter] Reading /path from {bag_path} …")
    poses = read_path_from_bag(bag_path, "/path")

    if not poses:
        print("[Exporter] /path empty — falling back to /Odometry …")
        poses = read_odometry_from_bag(bag_path, "/Odometry")

    if not poses:
        print("[ERROR] No trajectory data found in bag. Aborting.")
        return

    print(f"[Exporter] {len(poses)} poses loaded. Time span: "
          f"{poses[0]['t']:.3f} → {poses[-1]['t']:.3f} s")

    if fmt in ("tum", "all"):
        write_tum(poses, os.path.join(output_dir, "trajectory_tum.txt"))
    if fmt in ("csv", "all"):
        write_csv(poses, os.path.join(output_dir, "trajectory.csv"))
    if fmt in ("kitti", "all"):
        write_kitti(poses, os.path.join(output_dir, "trajectory_kitti.txt"))

    print(f"[Exporter] Done. Results in {output_dir}")


def main_rosnode():
    rospy.init_node("trajectory_exporter", anonymous=True)
    bag_path   = rospy.get_param("~bag",        "/data/output/fast_livo2_output.bag")
    output_dir = rospy.get_param("~output_dir", "/data/output")
    fmt        = rospy.get_param("~format",     "all")
    export(bag_path, output_dir, fmt)


def main_cli():
    parser = argparse.ArgumentParser(
        description="Export FAST-LIVO2 trajectory from a recorded rosbag."
    )
    parser.add_argument("--bag",        required=True, help="Path to output bag")
    parser.add_argument("--output_dir", default="./results", help="Output directory")
    parser.add_argument("--format",     default="all",
                        choices=["tum", "csv", "kitti", "all"],
                        help="Export format (default: all)")
    args = parser.parse_args()
    export(args.bag, args.output_dir, args.format)


if __name__ == "__main__":
    if "--bag" in sys.argv:
        main_cli()
    elif _HAS_ROS:
        main_rosnode()
    else:
        print("[ERROR] Neither ROS nor --bag argument available.")
        sys.exit(1)
