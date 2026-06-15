#!/usr/bin/env python3
"""Static preflight for a ROS1 dataset bag used by the benchmark.

Run inside one of the project ROS Noetic images. The script never rewrites the bag.
It checks the exact topic/type/field assumptions that can prevent the seven black-box
algorithms from starting or producing trajectories.
"""
import argparse
import math
import os
import sys
from collections import OrderedDict

try:
    import rosbag
    import sensor_msgs.point_cloud2 as pc2
except Exception as exc:
    print("ERROR: ROS1 rosbag/sensor_msgs Python modules are unavailable. Run through ./inspect_bag.sh.", file=sys.stderr)
    print("DETAIL:", exc, file=sys.stderr)
    sys.exit(2)

EXPECTED_TYPES = {
    "lidar": "sensor_msgs/PointCloud2",
    "imu": "sensor_msgs/Imu",
    "camera": "sensor_msgs/Image",
    "gps": "sensor_msgs/NavSatFix",
}


def first_message(bag, topic):
    for _topic, msg, stamp in bag.read_messages(topics=[topic]):
        return msg, stamp.to_sec()
    return None, None


def read_gt_range(path):
    if not path or not os.path.isfile(path):
        return None
    stamps = []
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.replace(",", " ").split()
            try:
                if len(parts) >= 8 and len(parts) < 20:  # TUM
                    stamps.append(float(parts[0]))
                elif len(parts) >= 20:  # UrbanNav INS-like table
                    stamps.append(float(parts[0]))
            except ValueError:
                pass
    return (min(stamps), max(stamps), len(stamps)) if stamps else None


def fmt_status(ok):
    return "OK  " if ok else "FAIL"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bag", required=True)
    ap.add_argument("--gt", default="")
    ap.add_argument("--lidar-topic", required=True)
    ap.add_argument("--imu-topic", required=True)
    ap.add_argument("--camera-topic", default="")
    ap.add_argument("--gps-topic", default="")
    ap.add_argument("--camera-width", type=int, default=0)
    ap.add_argument("--camera-height", type=int, default=0)
    ap.add_argument("--point-time-field", default="time")
    ap.add_argument("--point-time-unit", choices=("auto", "s", "ms", "us", "ns"), default="auto")
    ap.add_argument("--scan-lines", type=int, default=64)
    ap.add_argument("--strict", action="store_true", help="Treat missing ring/time fields as a failing preflight")
    args = ap.parse_args()

    if not os.path.isfile(args.bag):
        print("ERROR: bag not found:", args.bag, file=sys.stderr)
        return 2

    checks = []
    warnings = []
    with rosbag.Bag(args.bag, "r") as bag:
        info = bag.get_type_and_topic_info().topics
        start, end = bag.get_start_time(), bag.get_end_time()
        print("=== DATASET BAG PREFLIGHT ===")
        print(f"bag:       {args.bag}")
        print(f"start:     {start:.9f}")
        print(f"end:       {end:.9f}")
        print(f"duration:  {end-start:.3f} s")
        print(f"topics:    {len(info)}")

        requested = OrderedDict([
            ("lidar", args.lidar_topic),
            ("imu", args.imu_topic),
            ("camera", args.camera_topic),
            ("gps", args.gps_topic),
        ])
        print("\n=== REQUIRED INTERFACES ===")
        for role, topic in requested.items():
            if not topic:
                if role in ("camera", "gps"):
                    print(f"SKIP {role:7s} disabled")
                    continue
                checks.append((False, f"{role} topic is empty"))
                print(f"FAIL {role:7s} empty topic")
                continue
            present = topic in info
            actual = info[topic].msg_type if present else "missing"
            expected = EXPECTED_TYPES[role]
            type_ok = present and actual == expected
            required = role in ("lidar", "imu") or role == "camera"
            if required:
                checks.append((type_ok, f"{role}: {topic} expected {expected}, got {actual}"))
            elif not type_ok:
                warnings.append(f"optional {role}: {topic} expected {expected}, got {actual}")
            count = info[topic].message_count if present else 0
            freq = info[topic].frequency or 0.0 if present else 0.0
            print(f"{fmt_status(type_ok)} {role:7s} {topic:38s} type={actual} count={count} nominal_hz={freq:.3f}")

        # LiDAR payload details and parser-critical fields.
        if args.lidar_topic in info and info[args.lidar_topic].msg_type == EXPECTED_TYPES["lidar"]:
            msg, bag_t = first_message(bag, args.lidar_topic)
            fields = {f.name: f for f in msg.fields}
            names = list(fields)
            print("\n=== LIDAR PAYLOAD ===")
            print(f"frame_id:   {msg.header.frame_id!r}")
            print(f"stamp:      {msg.header.stamp.to_sec():.9f} (bag record {bag_t:.9f})")
            print(f"shape:      {msg.width} x {msg.height}; point_step={msg.point_step}; dense={msg.is_dense}")
            print("fields:     " + ", ".join(f"{f.name}[datatype={f.datatype},offset={f.offset}]" for f in msg.fields))
            xyz_ok = all(x in fields for x in ("x", "y", "z"))
            checks.append((xyz_ok, "LiDAR PointCloud2 must contain x/y/z"))
            ring_ok = "ring" in fields
            time_ok = args.point_time_field in fields
            if not ring_ok:
                text="LiDAR lacks 'ring'; FAST-LIO/LVI-SAM spinning-LiDAR parsers may fail"
                (checks if args.strict else warnings).append((False,text) if args.strict else text)
            if not time_ok:
                text=f"LiDAR lacks '{args.point_time_field}'; deskewing may be disabled or fail"
                (checks if args.strict else warnings).append((False,text) if args.strict else text)

            sample_fields = [n for n in ("ring", args.point_time_field) if n in fields]
            values = {n: [] for n in sample_fields}
            if sample_fields:
                try:
                    for idx, point in enumerate(pc2.read_points(msg, field_names=sample_fields, skip_nans=True)):
                        for n, v in zip(sample_fields, point):
                            values[n].append(float(v))
                        if idx >= 4999:
                            break
                except Exception as exc:
                    warnings.append(f"could not sample LiDAR ring/time fields: {exc}")
            if values.get("ring"):
                lo, hi = min(values["ring"]), max(values["ring"])
                print(f"ring sample: min={lo:g} max={hi:g} configured_upper_bound={args.scan_lines}")
                if hi >= args.scan_lines:
                    checks.append((False, f"sample ring max {hi:g} is not < scan_lines {args.scan_lines}"))
            if values.get(args.point_time_field):
                vals = values[args.point_time_field]
                lo, hi = min(vals), max(vals)
                if args.point_time_unit != "auto":
                    unit_hint = args.point_time_unit + " (configured)"
                elif hi <= 1.0:
                    unit_hint = "s (auto guess)"
                elif hi <= 1.0e3:
                    unit_hint = "ms (auto guess)"
                elif hi <= 1.0e6:
                    unit_hint = "us (auto guess)"
                else:
                    unit_hint = "ns/ticks (auto guess)"
                print(f"{args.point_time_field} sample: min={lo:.9g} max={hi:.9g} unit_hint={unit_hint}")
                if args.point_time_unit == "auto":
                    warnings.append("point_time_unit is auto-detected; set it explicitly in datasets.yaml after verifying this sample")

        if args.imu_topic in info and info[args.imu_topic].msg_type == EXPECTED_TYPES["imu"]:
            msg, _ = first_message(bag, args.imu_topic)
            a = msg.linear_acceleration
            g = msg.angular_velocity
            amag = math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z)
            print("\n=== IMU PAYLOAD ===")
            print(f"frame_id:   {msg.header.frame_id!r}")
            print(f"accel:      [{a.x:.6g}, {a.y:.6g}, {a.z:.6g}] |a|={amag:.6g}")
            print(f"gyro:       [{g.x:.6g}, {g.y:.6g}, {g.z:.6g}]")
            print("orientation_covariance[0]:", msg.orientation_covariance[0])
            if amag < 1.0 or amag > 30.0:
                warnings.append("first IMU acceleration magnitude is unusual; verify units are m/s^2")

        if args.camera_topic and args.camera_topic in info and info[args.camera_topic].msg_type == EXPECTED_TYPES["camera"]:
            msg, _ = first_message(bag, args.camera_topic)
            print("\n=== CAMERA PAYLOAD ===")
            print(f"frame_id:   {msg.header.frame_id!r}")
            print(f"size:       {msg.width} x {msg.height}")
            print(f"encoding:   {msg.encoding}")
            if args.camera_width and args.camera_height and (msg.width, msg.height) != (args.camera_width, args.camera_height):
                warnings.append(f"configured camera size is {args.camera_width}x{args.camera_height}, bag reports {msg.width}x{msg.height}")
            if msg.encoding.lower() not in ("rgb8", "bgr8", "mono8", "8uc1", "8uc3"):
                warnings.append(f"camera encoding {msg.encoding!r} may require conversion for ORB-SLAM3")

        gt_range = read_gt_range(args.gt)
        if gt_range:
            gs, ge, n = gt_range
            overlap = max(0.0, min(end, ge) - max(start, gs))
            print("\n=== GROUND TRUTH CLOCK ===")
            print(f"gt:        {args.gt}")
            print(f"samples:   {n}")
            print(f"range:     {gs:.9f} .. {ge:.9f} ({ge-gs:.3f} s)")
            print(f"overlap:   {overlap:.3f} s with bag clock")
            checks.append((overlap > 0.0, "ground-truth timestamps do not overlap bag timestamps"))
            if overlap < 0.8 * min(end-start, ge-gs):
                warnings.append("bag/GT overlap is partial; metrics will cover only the overlapping interval")
        elif args.gt:
            warnings.append(f"ground-truth file missing or unreadable: {args.gt}")

    print("\n=== RESULT ===")
    failures = [text for ok, text in checks if not ok]
    for ok, text in checks:
        print(("PASS " if ok else "FAIL ") + text)
    for item in warnings:
        if isinstance(item, tuple):
            _ok, item = item
        print("WARN " + item)
    if failures:
        print(f"\nPreflight failed with {len(failures)} blocking issue(s).")
        return 1
    print("\nPreflight passed. Warnings identify provisional calibration or parser assumptions to verify.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
