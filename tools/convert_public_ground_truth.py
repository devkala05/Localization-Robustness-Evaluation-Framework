#!/usr/bin/env python3
"""Convert official UrbanLoco or Boreas-RT ground truth to benchmark CSV."""
from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path

import numpy as np


FIELDS = ["timestamp_s", "x_m", "y_m", "z_m", "qx", "qy", "qz", "qw",
          "frame_id", "child_frame_id", "source_method", "notes"]
GPS_EPOCH_UNIX_S = 315964800.0
# UrbanLoco's California recordings were made in August 2019, when GPS was
# 18 seconds ahead of UTC. INSPVAX stores gps_week_seconds in milliseconds.
URBANLOCO_GPS_UTC_LEAP_SECONDS = 18.0


def rotation_x(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)


def rotation_y(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)


def rotation_z(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)


def boreas_rotation(heading, pitch, roll):
    """Match pyboreas yawPitchRollToRot exactly."""
    def passive_roll(r):
        c, s = math.cos(r), math.sin(r)
        return np.array([[1, 0, 0], [0, c, s], [0, -s, c]], dtype=float)
    def passive_pitch(p):
        c, s = math.cos(p), math.sin(p)
        return np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]], dtype=float)
    def passive_yaw(y):
        c, s = math.cos(y), math.sin(y)
        return np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]], dtype=float)
    return passive_roll(roll) @ passive_pitch(pitch) @ passive_yaw(heading)


def matrix_to_quaternion(matrix):
    matrix = np.asarray(matrix, dtype=float)
    trace = float(np.trace(matrix))
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        values = [(matrix[2, 1] - matrix[1, 2]) / s,
                  (matrix[0, 2] - matrix[2, 0]) / s,
                  (matrix[1, 0] - matrix[0, 1]) / s, 0.25 * s]
    else:
        index = int(np.argmax(np.diag(matrix)))
        if index == 0:
            s = math.sqrt(1.0 + matrix[0, 0] - matrix[1, 1] - matrix[2, 2]) * 2.0
            values = [0.25*s, (matrix[0, 1]+matrix[1, 0])/s,
                      (matrix[0, 2]+matrix[2, 0])/s, (matrix[2, 1]-matrix[1, 2])/s]
        elif index == 1:
            s = math.sqrt(1.0 + matrix[1, 1] - matrix[0, 0] - matrix[2, 2]) * 2.0
            values = [(matrix[0, 1]+matrix[1, 0])/s, 0.25*s,
                      (matrix[1, 2]+matrix[2, 1])/s, (matrix[0, 2]-matrix[2, 0])/s]
        else:
            s = math.sqrt(1.0 + matrix[2, 2] - matrix[0, 0] - matrix[1, 1]) * 2.0
            values = [(matrix[0, 2]+matrix[2, 0])/s,
                      (matrix[1, 2]+matrix[2, 1])/s, 0.25*s,
                      (matrix[1, 0]-matrix[0, 1])/s]
    q = np.asarray(values, dtype=float)
    q /= np.linalg.norm(q)
    return q


def geodetic_to_ecef(latitude_deg, longitude_deg, height_m):
    a = 6378137.0
    e2 = 6.69437999014e-3
    lat, lon = math.radians(latitude_deg), math.radians(longitude_deg)
    n = a / math.sqrt(1.0 - e2 * math.sin(lat) ** 2)
    return np.array([(n + height_m) * math.cos(lat) * math.cos(lon),
                     (n + height_m) * math.cos(lat) * math.sin(lon),
                     (n * (1.0 - e2) + height_m) * math.sin(lat)])


def ecef_to_enu(ecef, origin_ecef, latitude_deg, longitude_deg):
    lat, lon = math.radians(latitude_deg), math.radians(longitude_deg)
    transform = np.array([
        [-math.sin(lon), math.cos(lon), 0.0],
        [-math.sin(lat)*math.cos(lon), -math.sin(lat)*math.sin(lon), math.cos(lat)],
        [math.cos(lat)*math.cos(lon), math.cos(lat)*math.sin(lon), math.sin(lat)],
    ])
    return transform @ (ecef - origin_ecef)


def write_rows(output: Path, rows) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(FIELDS)
        writer.writerows(rows)
    if not rows:
        raise RuntimeError("ground-truth conversion produced no poses")


def parse_urban_calibration(path: Path):
    """Read the IMU/SPAN transforms from the downloaded official text file."""
    text = path.read_text(encoding="utf-8")
    imu_section = text.split("%% IMU", 1)[1].split("%% UBLOX", 1)[0]
    span_section = text.split("%% SPAN-CPT", 1)[1]
    number = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
    imu_match = re.search(r"data\s*:\s*\[([^]]+)\]", imu_section, re.DOTALL)
    span_matches = list(re.finditer(r"\[([^]]+)\]", span_section, re.DOTALL))
    if not imu_match or not span_matches:
        raise RuntimeError(f"cannot parse UrbanLoco IMU/SPAN calibration from {path}")
    imu_values = [float(value) for value in re.findall(number, imu_match.group(1))]
    span_candidates = [[float(value) for value in re.findall(number, match.group(1))]
                       for match in span_matches]
    span_values = next((values for values in span_candidates if len(values) == 12), [])
    if len(imu_values) != 12 or len(span_values) != 12:
        raise RuntimeError(f"unexpected UrbanLoco calibration dimensions: {len(imu_values)}, {len(span_values)}")
    t_lidar_imu = np.eye(4); t_lidar_imu[:3, :] = np.asarray(imu_values).reshape(3, 4)
    t_lidar_span = np.eye(4); t_lidar_span[:3, :] = np.asarray(span_values).reshape(3, 4)
    return t_lidar_imu, t_lidar_span


def convert_boreas(sequence_root: Path, output: Path) -> None:
    gt_path = sequence_root / "applanix" / "gps_post_process.csv"
    calibration = np.loadtxt(sequence_root / "calib" / "T_applanix_dmu.txt")
    rows = []
    first_position = None
    with gt_path.open(newline="", encoding="utf-8") as stream:
        for item in csv.DictReader(stream):
            values = [float(item[name]) for name in
                      ("GPSTime", "easting", "northing", "altitude", "roll", "pitch", "heading")]
            if not all(math.isfinite(value) for value in values):
                continue
            stamp, x, y, z, roll, pitch, heading = values
            t_enu_applanix = np.eye(4)
            t_enu_applanix[:3, :3] = boreas_rotation(heading, pitch, roll)
            t_enu_applanix[:3, 3] = (x, y, z)
            t_enu_dmu = t_enu_applanix @ calibration
            if first_position is None:
                first_position = t_enu_dmu[:3, 3].copy()
            position = t_enu_dmu[:3, 3] - first_position
            q = matrix_to_quaternion(t_enu_dmu[:3, :3])
            rows.append([stamp, *position, *q, "boreas_enu_local", "base_link",
                         "Applanix POSPac post-processed GNSS/INS/wheel",
                         "official ENU translated to first pose; independent DMU used by estimators"])
    write_rows(output, rows)


def urban_attitude(roll_deg, pitch_deg, azimuth_deg):
    """NovAtel intrinsic Z-X-Y attitude, expressed in ENU."""
    roll, pitch, azimuth = map(math.radians, (roll_deg, pitch_deg, azimuth_deg))
    return rotation_z(-azimuth) @ rotation_x(pitch) @ rotation_y(roll)


def urban_novatel_timestamp(header) -> float:
    """Return the INSPVAX receiver measurement time as Unix UTC seconds."""
    week = int(header.gps_week)
    week_milliseconds = int(header.gps_week_seconds)
    if week <= 0 or week_milliseconds < 0 or week_milliseconds >= 604800000:
        raise ValueError("invalid NovAtel GPS week timestamp")
    return (GPS_EPOCH_UNIX_S + week * 604800.0 + week_milliseconds * 1.0e-3
            - URBANLOCO_GPS_UTC_LEAP_SECONDS)


def convert_urbanloco(bag: Path, calibration_path: Path, output: Path) -> None:
    try:
        import rosbag
    except ImportError as exc:
        raise RuntimeError("UrbanLoco conversion must run in the ROS Noetic container") from exc
    if not calibration_path.is_file():
        raise FileNotFoundError(calibration_path)
    t_lidar_imu, t_lidar_span = parse_urban_calibration(calibration_path)
    t_span_imu = np.linalg.inv(t_lidar_span) @ t_lidar_imu
    accepted = {3}  # INS_SOLUTION_GOOD
    samples = []
    origin = None
    with rosbag.Bag(str(bag), "r") as source:
        for _, msg, _bag_stamp in source.read_messages(topics=["/novatel_data/inspvax"]):
            if int(msg.ins_status) not in accepted:
                continue
            latitude, longitude = float(msg.latitude), float(msg.longitude)
            height = float(msg.altitude) + float(msg.undulation)
            values = (latitude, longitude, height, float(msg.roll), float(msg.pitch), float(msg.azimuth))
            if not all(math.isfinite(value) for value in values):
                continue
            if origin is None:
                origin = (latitude, longitude, height, geodetic_to_ecef(latitude, longitude, height))
            ecef = geodetic_to_ecef(latitude, longitude, height)
            position = ecef_to_enu(ecef, origin[3], origin[0], origin[1])
            t_enu_span = np.eye(4)
            t_enu_span[:3, :3] = urban_attitude(float(msg.roll), float(msg.pitch), float(msg.azimuth))
            t_enu_span[:3, 3] = position
            t_enu_imu = t_enu_span @ t_span_imu
            # The rosbag record is about 0.2 s later than the receiver time in
            # this sequence. Use the embedded measurement time so reference
            # poses and acquisition-stamped estimator poses represent the same
            # instant.
            samples.append((urban_novatel_timestamp(msg.header), t_enu_imu))
    if samples:
        offset = samples[0][1][:3, 3].copy()
    rows = []
    for stamp, pose in samples:
        q = matrix_to_quaternion(pose[:3, :3])
        rows.append([stamp, *(pose[:3, 3] - offset), *q,
                     "urbanloco_enu", "base_link", "NovAtel SPAN-CPT INSPVAX",
                     "WGS84 ENU; receiver GPS measurement time; INS_SOLUTION_GOOD only; "
                     "supplied SPAN/IMU/LiDAR extrinsics"])
    write_rows(output, rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=("urbanloco", "boreas_rt"))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--calibration", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.dataset == "boreas_rt":
        convert_boreas(args.input, args.output)
    else:
        if args.calibration is None:
            parser.error("--calibration is required for UrbanLoco")
        convert_urbanloco(args.input, args.calibration, args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
