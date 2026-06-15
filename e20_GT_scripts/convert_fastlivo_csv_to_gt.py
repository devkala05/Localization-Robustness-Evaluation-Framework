#!/usr/bin/env python3
import argparse
import csv
import math
from collections import OrderedDict


def parse_args():
    parser = argparse.ArgumentParser(description="Convert FAST-LIVO2 odometry CSV to GT schema.")
    parser.add_argument("--input", default="fastlivo_output/odometry.csv")
    parser.add_argument("--output", default="gt_one_full_loop_fastlivo2_lidar103.csv")
    parser.add_argument("--frame-id", default="camera_init")
    parser.add_argument("--source-method", default="fastlivo2_lidar103_imu")
    return parser.parse_args()


def stamp_to_ns(stamp_text):
    return int(round(float(stamp_text) * 1e9))


def yaw_from_quat(qx, qy, qz, qw):
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    return math.atan2(siny_cosp, cosy_cosp)


def main():
    args = parse_args()
    deduped = OrderedDict()
    with open(args.input, newline="") as src:
        reader = csv.DictReader(src)
        for row in reader:
            timestamp_ns = stamp_to_ns(row["timestamp"])
            deduped[timestamp_ns] = row

    with open(args.output, "w", newline="") as dst:
        writer = csv.writer(dst)
        writer.writerow(
            [
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
        )

        for timestamp_ns, row in deduped.items():
            qx = float(row["qx"])
            qy = float(row["qy"])
            qz = float(row["qz"])
            qw = float(row["qw"])
            yaw = yaw_from_quat(qx, qy, qz, qw)
            writer.writerow(
                [
                    timestamp_ns,
                    "{:.9f}".format(timestamp_ns * 1e-9),
                    args.frame_id,
                    args.source_method,
                    "{:.6f}".format(float(row["pos_x"])),
                    "{:.6f}".format(float(row["pos_y"])),
                    "{:.6f}".format(float(row["pos_z"])),
                    "{:.10f}".format(qx),
                    "{:.10f}".format(qy),
                    "{:.10f}".format(qz),
                    "{:.10f}".format(qw),
                    "nan",
                    "nan",
                    "{:.10f}".format(yaw) if math.isfinite(yaw) else "nan",
                    "0.050000",
                    "0.050000",
                    "0.100000",
                    "0.900",
                    "0",
                    "0",
                    "nan",
                    "nan",
                    "nan",
                    "fastlivo2_lio_mode;lidar=/lidar103/velodyne_points;imu=/mavros/imu/data;img_en=0;no_external_gt",
                ]
            )

    print("wrote {}".format(args.output))
    print("rows={}".format(len(deduped)))


if __name__ == "__main__":
    main()
