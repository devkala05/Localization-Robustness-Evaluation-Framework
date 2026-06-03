#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image
from rosbags.rosbag2 import Writer
from rosbags.typesys import Stores, get_typestore


TOPICS = {
    "lidar": ("/kitti/velo/pointcloud", "sensor_msgs/msg/PointCloud2"),
    "left": ("/kitti/camera/color/left/image_raw", "sensor_msgs/msg/Image"),
    "right": ("/kitti/camera/color/right/image_raw", "sensor_msgs/msg/Image"),
    "imu": ("/kitti/oxts/imu", "sensor_msgs/msg/Imu"),
    "gps": ("/kitti/oxts/gps/fix", "sensor_msgs/msg/NavSatFix"),
}

POINT_STEP = 32
SCAN_LINES = 64
SCAN_RATE_HZ = 10.0


def parse_timestamp(line: str) -> int:
    text = line.strip().replace("Z", "+00:00")
    if "." in text:
        base, frac = text.split(".", 1)
        frac = frac.split("+", 1)[0].split("-", 1)[0]
        frac = (frac + "000000000")[:9]
        dt = datetime.fromisoformat(base).replace(tzinfo=timezone.utc)
        return int(dt.timestamp()) * 1_000_000_000 + int(frac)
    dt = datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000_000)


def stamp_msg(types: dict, timestamp_ns: int):
    sec, nanosec = divmod(int(timestamp_ns), 1_000_000_000)
    return types["builtin_interfaces/msg/Time"](sec=sec, nanosec=nanosec)


def header(types: dict, timestamp_ns: int, frame_id: str):
    return types["std_msgs/msg/Header"](stamp=stamp_msg(types, timestamp_ns), frame_id=frame_id)


def quat_from_rpy(types: dict, roll: float, pitch: float, yaw: float):
    cr, sr = math.cos(roll / 2.0), math.sin(roll / 2.0)
    cp, sp = math.cos(pitch / 2.0), math.sin(pitch / 2.0)
    cy, sy = math.cos(yaw / 2.0), math.sin(yaw / 2.0)
    return types["geometry_msgs/msg/Quaternion"](
        x=sr * cp * cy - cr * sp * sy,
        y=cr * sp * cy + sr * cp * sy,
        z=cr * cp * sy - sr * sp * cy,
        w=cr * cp * cy + sr * sp * sy,
    )


def vector3(types: dict, x: float, y: float, z: float):
    return types["geometry_msgs/msg/Vector3"](x=float(x), y=float(y), z=float(z))


def estimate_ring_time(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    horizontal = np.linalg.norm(points[:, :2], axis=1)
    elevation = np.degrees(np.arctan2(points[:, 2], np.maximum(horizontal, 1e-6)))
    ring = np.rint((2.0 - elevation) / (2.0 - (-24.9)) * (SCAN_LINES - 1))
    ring = np.clip(ring, 0, SCAN_LINES - 1).astype("<u2")

    azimuth = (np.arctan2(points[:, 1], points[:, 0]) + 2.0 * math.pi) % (2.0 * math.pi)
    time = (azimuth / (2.0 * math.pi) / SCAN_RATE_HZ).astype("<f4")
    return ring, time


def velodyne_pointcloud_bytes(points: np.ndarray) -> np.ndarray:
    ring, time = estimate_ring_time(points)
    dtype = np.dtype(
        {
            "names": ["x", "y", "z", "pad", "intensity", "time", "ring", "pad2"],
            "formats": ["<f4", "<f4", "<f4", "<f4", "<f4", "<f4", "<u2", ("u1", 6)],
            "offsets": [0, 4, 8, 12, 16, 20, 24, 26],
            "itemsize": POINT_STEP,
        }
    )
    packed = np.zeros(len(points), dtype=dtype)
    packed["x"] = points[:, 0].astype("<f4")
    packed["y"] = points[:, 1].astype("<f4")
    packed["z"] = points[:, 2].astype("<f4")
    packed["intensity"] = points[:, 3].astype("<f4")
    packed["time"] = time
    packed["ring"] = ring
    return packed.view(np.uint8).reshape(-1)


def pointcloud_msg(types: dict, timestamp_ns: int, path: Path):
    points = np.fromfile(path, dtype=np.float32).reshape(-1, 4)
    fields = [
        types["sensor_msgs/msg/PointField"]("x", 0, 7, 1),
        types["sensor_msgs/msg/PointField"]("y", 4, 7, 1),
        types["sensor_msgs/msg/PointField"]("z", 8, 7, 1),
        types["sensor_msgs/msg/PointField"]("intensity", 16, 7, 1),
        types["sensor_msgs/msg/PointField"]("time", 20, 7, 1),
        types["sensor_msgs/msg/PointField"]("ring", 24, 4, 1),
    ]
    data = velodyne_pointcloud_bytes(points)
    return types["sensor_msgs/msg/PointCloud2"](
        header=header(types, timestamp_ns, "velodyne"),
        height=1,
        width=len(points),
        fields=fields,
        is_bigendian=False,
        point_step=POINT_STEP,
        row_step=POINT_STEP * len(points),
        data=data,
        is_dense=True,
    )


def image_msg(types: dict, timestamp_ns: int, path: Path, frame_id: str):
    image = np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)
    height, width = image.shape[:2]
    return types["sensor_msgs/msg/Image"](
        header=header(types, timestamp_ns, frame_id),
        height=height,
        width=width,
        encoding="rgb8",
        is_bigendian=0,
        step=width * 3,
        data=image.reshape(-1),
    )


def imu_msg(types: dict, timestamp_ns: int, values: np.ndarray):
    # KITTI OXTS columns: roll,pitch,yaw = 3:6; accel = 11:14; gyro = 17:20.
    cov_unknown = np.full(9, -1.0, dtype=np.float64)
    cov_small = np.eye(3, dtype=np.float64).reshape(-1) * 0.01
    return types["sensor_msgs/msg/Imu"](
        header=header(types, timestamp_ns, "imu_link"),
        orientation=quat_from_rpy(types, values[3], values[4], values[5]),
        orientation_covariance=cov_small,
        angular_velocity=vector3(types, values[17], values[18], values[19]),
        angular_velocity_covariance=cov_small,
        linear_acceleration=vector3(types, values[11], values[12], values[13]),
        linear_acceleration_covariance=cov_unknown,
    )


def gps_msg(types: dict, timestamp_ns: int, values: np.ndarray):
    status = types["sensor_msgs/msg/NavSatStatus"](status=0, service=1)
    cov = np.eye(3, dtype=np.float64).reshape(-1) * max(float(values[23]) if len(values) > 23 else 1.0, 1.0)
    return types["sensor_msgs/msg/NavSatFix"](
        header=header(types, timestamp_ns, "gps"),
        status=status,
        latitude=float(values[0]),
        longitude=float(values[1]),
        altitude=float(values[2]),
        position_covariance=cov,
        position_covariance_type=2,
    )


def read_timestamps(seq_dir: Path) -> list[int]:
    ts_file = seq_dir / "oxts/timestamps.txt"
    return [parse_timestamp(line) for line in ts_file.read_text().splitlines() if line.strip()]


def convert(kitti_root: Path, sequence: str, output: Path) -> None:
    seq_dir = kitti_root / sequence
    if not seq_dir.exists():
        raise FileNotFoundError(seq_dir)
    if output.exists():
        shutil.rmtree(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    typestore = get_typestore(Stores.ROS2_HUMBLE)
    types = typestore.types
    timestamps = read_timestamps(seq_dir)
    velo = sorted((seq_dir / "velodyne_points/data").glob("*.bin"))
    left = sorted((seq_dir / "image_02/data").glob("*.png"))
    right = sorted((seq_dir / "image_03/data").glob("*.png"))
    oxts = sorted((seq_dir / "oxts/data").glob("*.txt"))
    count = min(len(timestamps), len(velo), len(left), len(right), len(oxts))
    if count == 0:
        raise RuntimeError(f"no synchronized KITTI frames found in {seq_dir}")

    with Writer(output, version=8) as writer:
        conns = {name: writer.add_connection(topic, msgtype, typestore=typestore) for name, (topic, msgtype) in TOPICS.items()}
        for idx in range(count):
            ts = timestamps[idx]
            oxts_values = np.asarray([float(x) for x in oxts[idx].read_text().split()], dtype=float)
            messages = [
                ("lidar", pointcloud_msg(types, ts, velo[idx])),
                ("left", image_msg(types, ts, left[idx], "camera_left")),
                ("right", image_msg(types, ts, right[idx], "camera_right")),
                ("imu", imu_msg(types, ts, oxts_values)),
                ("gps", gps_msg(types, ts, oxts_values)),
            ]
            for name, msg in messages:
                topic, msgtype = TOPICS[name]
                writer.write(conns[name], ts, typestore.serialize_cdr(msg, msgtype))
    print(f"Converted {count} synchronized frames from {sequence} to {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kitti_root", required=True, type=Path)
    parser.add_argument("--sequence", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--calib", type=Path)
    args = parser.parse_args()
    convert(args.kitti_root, args.sequence, args.output)


if __name__ == "__main__":
    main()
