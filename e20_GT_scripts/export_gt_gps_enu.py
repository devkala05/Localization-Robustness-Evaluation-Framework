#!/usr/bin/env python3
import argparse
import csv
import math
from collections import deque

import rosbag


GPS_TOPIC = "/mavros/global_position/global"
WGS84_A = 6378137.0
WGS84_E2 = 6.69437999014e-3


def geodetic_to_ecef(lat_deg, lon_deg, alt_m):
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    x = (n + alt_m) * cos_lat * math.cos(lon)
    y = (n + alt_m) * cos_lat * math.sin(lon)
    z = (n * (1.0 - WGS84_E2) + alt_m) * sin_lat
    return x, y, z


def ecef_to_enu(x, y, z, origin):
    ox, oy, oz, lat0, lon0 = origin
    dx = x - ox
    dy = y - oy
    dz = z - oz
    sin_lat = math.sin(lat0)
    cos_lat = math.cos(lat0)
    sin_lon = math.sin(lon0)
    cos_lon = math.cos(lon0)

    east = -sin_lon * dx + cos_lon * dy
    north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
    up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
    return east, north, up


def yaw_to_quat(yaw):
    half = 0.5 * yaw
    return 0.0, 0.0, math.sin(half), math.cos(half)


def mean(values):
    return sum(values) / len(values)


def safe_sqrt(value):
    return math.sqrt(value) if value >= 0.0 and math.isfinite(value) else float("nan")


def is_finite_fix(msg):
    return (
        math.isfinite(msg.latitude)
        and math.isfinite(msg.longitude)
        and math.isfinite(msg.altitude)
        and abs(msg.latitude) <= 90.0
        and abs(msg.longitude) <= 180.0
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export a conservative GPS-derived pseudo-GT CSV in a local ENU frame."
    )
    parser.add_argument("--bag", default="one_full_loop.bag", help="Input ROS1 bag.")
    parser.add_argument(
        "--output",
        default="gt_one_full_loop_gps_enu.csv",
        help="Output CSV path.",
    )
    parser.add_argument("--topic", default=GPS_TOPIC, help="NavSatFix topic.")
    parser.add_argument(
        "--smooth-window",
        type=int,
        default=31,
        help="Odd/even rolling mean window size in samples. 31 samples is about 0.31 s for this bag.",
    )
    parser.add_argument(
        "--min-yaw-baseline",
        type=float,
        default=0.35,
        help="Minimum smoothed ENU displacement in meters before deriving yaw.",
    )
    parser.add_argument(
        "--min-step",
        type=float,
        default=0.001,
        help="Reject non-initial GNSS jumps smaller than this only for yaw updates, not for position export.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.smooth_window < 1:
        raise SystemExit("--smooth-window must be >= 1")

    origin = None
    yaw_anchor_xy = None
    last_valid_yaw = float("nan")
    recent_e = deque(maxlen=args.smooth_window)
    recent_n = deque(maxlen=args.smooth_window)
    recent_u = deque(maxlen=args.smooth_window)
    accepted = 0
    rejected = 0

    header = [
        "timestamp_ns",
        "timestamp_s",
        "frame_id",
        "source_method",
        "x_m",
        "y_m",
        "z_m",
        "qx",
        "qy",
        "qz",
        "qw",
        "roll_rad",
        "pitch_rad",
        "yaw_rad",
        "std_x_m",
        "std_y_m",
        "std_z_m",
        "quality_score",
        "fix_status",
        "covariance_type",
        "origin_lat_deg",
        "origin_lon_deg",
        "origin_alt_m",
        "notes",
    ]

    with rosbag.Bag(args.bag) as bag, open(args.output, "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(header)

        for _, msg, _ in bag.read_messages(topics=[args.topic]):
            if msg.status.status < 0 or not is_finite_fix(msg):
                rejected += 1
                continue

            if origin is None:
                ox, oy, oz = geodetic_to_ecef(msg.latitude, msg.longitude, msg.altitude)
                origin = (
                    ox,
                    oy,
                    oz,
                    math.radians(msg.latitude),
                    math.radians(msg.longitude),
                    msg.latitude,
                    msg.longitude,
                    msg.altitude,
                )

            x, y, z = geodetic_to_ecef(msg.latitude, msg.longitude, msg.altitude)
            east, north, up = ecef_to_enu(x, y, z, origin[:5])
            recent_e.append(east)
            recent_n.append(north)
            recent_u.append(up)
            se = mean(recent_e)
            sn = mean(recent_n)
            su = mean(recent_u)

            yaw = float("nan")
            qx, qy, qz, qw = 0.0, 0.0, 0.0, 1.0
            notes = ["gps_fix", "rolling_mean_position"]

            if yaw_anchor_xy is not None:
                dx = se - yaw_anchor_xy[0]
                dy = sn - yaw_anchor_xy[1]
                dist = math.hypot(dx, dy)
                if dist >= args.min_yaw_baseline:
                    yaw = math.atan2(dy, dx)
                    last_valid_yaw = yaw
                    yaw_anchor_xy = (se, sn)
                    qx, qy, qz, qw = yaw_to_quat(yaw)
                    notes.append("yaw_from_smoothed_motion")
                elif math.isfinite(last_valid_yaw) and dist >= args.min_step:
                    yaw = last_valid_yaw
                    qx, qy, qz, qw = yaw_to_quat(yaw)
                    notes.append("yaw_carried")
                else:
                    notes.append("yaw_untrusted")
            else:
                yaw_anchor_xy = (se, sn)
                notes.append("yaw_untrusted")

            if msg.position_covariance_type != 0:
                std_x = safe_sqrt(msg.position_covariance[0])
                std_y = safe_sqrt(msg.position_covariance[4])
                std_z = safe_sqrt(msg.position_covariance[8])
                quality = 1.0
            else:
                std_x = std_y = std_z = float("nan")
                quality = 0.5
                notes.append("covariance_unknown")

            stamp_ns = msg.header.stamp.to_nsec()
            writer.writerow(
                [
                    stamp_ns,
                    "{:.9f}".format(stamp_ns * 1e-9),
                    "enu",
                    "gps_enu_rolling_mean",
                    "{:.6f}".format(se),
                    "{:.6f}".format(sn),
                    "{:.6f}".format(su),
                    "{:.10f}".format(qx),
                    "{:.10f}".format(qy),
                    "{:.10f}".format(qz),
                    "{:.10f}".format(qw),
                    "0.0000000000",
                    "0.0000000000",
                    "{:.10f}".format(yaw) if math.isfinite(yaw) else "nan",
                    "{:.6f}".format(std_x) if math.isfinite(std_x) else "nan",
                    "{:.6f}".format(std_y) if math.isfinite(std_y) else "nan",
                    "{:.6f}".format(std_z) if math.isfinite(std_z) else "nan",
                    "{:.3f}".format(quality),
                    msg.status.status,
                    msg.position_covariance_type,
                    "{:.10f}".format(origin[5]),
                    "{:.10f}".format(origin[6]),
                    "{:.6f}".format(origin[7]),
                    ";".join(notes),
                ]
            )
            accepted += 1

    print("wrote {}".format(args.output))
    print("accepted_fixes={}".format(accepted))
    print("rejected_fixes={}".format(rejected))
    if origin is not None:
        print(
            "origin_lat_lon_alt={:.10f},{:.10f},{:.6f}".format(
                origin[5], origin[6], origin[7]
            )
        )


if __name__ == "__main__":
    main()
