from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from rosbags.rosbag2 import Reader, Writer
from rosbags.typesys import Stores, get_typestore

from .perturbations import apply_chain, build_chain


POINT_STEP = 32
SCAN_LINES = 64
SCAN_RATE_HZ = 10.0


def _stamp_to_ns(stamp: Any) -> int:
    return int(stamp.sec) * 1_000_000_000 + int(stamp.nanosec)


def _set_stamp(msg: Any, timestamp_ns: int) -> None:
    if not hasattr(msg, "header"):
        return
    sec, nanosec = divmod(int(timestamp_ns), 1_000_000_000)
    msg.header.stamp.sec = sec
    msg.header.stamp.nanosec = nanosec


def _message_time_s(msg: Any, fallback_ns: int, start_ns: int) -> float:
    if hasattr(msg, "header"):
        return (_stamp_to_ns(msg.header.stamp) - start_ns) / 1_000_000_000.0
    return (fallback_ns - start_ns) / 1_000_000_000.0


def _sensor_key(topic: str, msgtype: str) -> str | None:
    if msgtype == "sensor_msgs/msg/PointCloud2" or "pointcloud" in topic or "velo" in topic:
        return "lidar"
    if msgtype == "sensor_msgs/msg/Image" or "camera" in topic:
        return "camera"
    if msgtype == "sensor_msgs/msg/Imu" or "imu" in topic:
        return "imu"
    if msgtype == "sensor_msgs/msg/NavSatFix" or "gps" in topic:
        return "gps"
    return None


def _field_offset(msg: Any, name: str) -> int | None:
    for field in msg.fields:
        if field.name == name:
            return int(field.offset)
    return None


def _float_field(msg: Any, raw: bytes, name: str, default: float = 0.0) -> np.ndarray:
    offset = _field_offset(msg, name)
    count = int(msg.width) * int(msg.height)
    if offset is None:
        return np.full(count, default, dtype=np.float32)
    return np.ndarray(shape=(count,), dtype="<f4", buffer=raw, offset=offset, strides=(int(msg.point_step),)).copy()


def _estimate_ring_time(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    horizontal = np.linalg.norm(points[:, :2], axis=1)
    elevation = np.degrees(np.arctan2(points[:, 2], np.maximum(horizontal, 1e-6)))
    ring = np.rint((2.0 - elevation) / (2.0 - (-24.9)) * (SCAN_LINES - 1))
    ring = np.clip(ring, 0, SCAN_LINES - 1).astype("<u2")

    azimuth = (np.arctan2(points[:, 1], points[:, 0]) + 2.0 * math.pi) % (2.0 * math.pi)
    time = (azimuth / (2.0 * math.pi) / SCAN_RATE_HZ).astype("<f4")
    return ring, time


def _velodyne_pointcloud_bytes(points: np.ndarray) -> np.ndarray:
    ring, time = _estimate_ring_time(points)
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


def _pointcloud_to_dict(msg: Any, t: float) -> dict[str, Any]:
    if int(msg.point_step) < 16:
        raise ValueError(f"unsupported PointCloud2 point_step={msg.point_step}; expected at least XYZI fields")
    raw = np.asarray(msg.data, dtype=np.uint8).tobytes()
    points = np.column_stack(
        [
            _float_field(msg, raw, "x"),
            _float_field(msg, raw, "y"),
            _float_field(msg, raw, "z"),
            _float_field(msg, raw, "intensity"),
        ]
    )
    return {"t": t, "points": points}


def _dict_to_pointcloud(data: dict[str, Any], msg: Any) -> Any:
    points = np.asarray(data["points"], dtype="<f4")
    msg.width = int(points.shape[0])
    msg.height = 1
    msg.point_step = POINT_STEP
    msg.row_step = POINT_STEP * int(points.shape[0])
    for field in msg.fields:
        if field.name == "intensity":
            field.offset = 16
        elif field.name == "time":
            field.offset = 20
        elif field.name == "ring":
            field.offset = 24
    existing = {field.name for field in msg.fields}
    field_cls = type(msg.fields[0])
    if "time" not in existing:
        msg.fields.append(field_cls("time", 20, 7, 1))
    if "ring" not in existing:
        msg.fields.append(field_cls("ring", 24, 4, 1))
    msg.data = _velodyne_pointcloud_bytes(points)
    msg.is_dense = True
    return msg


def _image_to_dict(msg: Any, t: float) -> dict[str, Any]:
    channels = 1 if msg.encoding in {"mono8", "8UC1"} else 3
    image = np.asarray(msg.data, dtype=np.uint8).reshape(int(msg.height), int(msg.width), channels).copy()
    if channels == 1:
        image = image[:, :, 0]
    return {"t": t, "image": image}


def _dict_to_image(data: dict[str, Any], msg: Any) -> Any:
    image = np.asarray(data["image"], dtype=np.uint8)
    msg.height = int(image.shape[0])
    msg.width = int(image.shape[1])
    channels = 1 if image.ndim == 2 else int(image.shape[2])
    msg.step = int(msg.width * channels)
    msg.data = image.reshape(-1)
    return msg


def _imu_to_dict(msg: Any, t: float) -> dict[str, Any]:
    return {
        "t": t,
        "gyro": [msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z],
        "accel": [msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z],
    }


def _dict_to_imu(data: dict[str, Any], msg: Any) -> Any:
    gyro = np.asarray(data["gyro"], dtype=float)
    accel = np.asarray(data["accel"], dtype=float)
    msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z = [float(x) for x in gyro]
    msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z = [float(x) for x in accel]
    return msg


def _gps_to_dict(msg: Any, t: float) -> dict[str, Any]:
    return {"t": t, "latitude": msg.latitude, "longitude": msg.longitude, "altitude": msg.altitude}


def _dict_to_gps(data: dict[str, Any], msg: Any) -> Any:
    msg.latitude = float(data["latitude"])
    msg.longitude = float(data["longitude"])
    msg.altitude = float(data["altitude"])
    return msg


def _to_perturbation_dict(msg: Any, msgtype: str, t: float) -> dict[str, Any]:
    if msgtype == "sensor_msgs/msg/PointCloud2":
        return _pointcloud_to_dict(msg, t)
    if msgtype == "sensor_msgs/msg/Image":
        return _image_to_dict(msg, t)
    if msgtype == "sensor_msgs/msg/Imu":
        return _imu_to_dict(msg, t)
    if msgtype == "sensor_msgs/msg/NavSatFix":
        return _gps_to_dict(msg, t)
    return {"t": t}


def _from_perturbation_dict(data: dict[str, Any], msg: Any, msgtype: str) -> Any:
    if msgtype == "sensor_msgs/msg/PointCloud2":
        return _dict_to_pointcloud(data, msg)
    if msgtype == "sensor_msgs/msg/Image":
        return _dict_to_image(data, msg)
    if msgtype == "sensor_msgs/msg/Imu":
        return _dict_to_imu(data, msg)
    if msgtype == "sensor_msgs/msg/NavSatFix":
        return _dict_to_gps(data, msg)
    return msg


def perturb_bag(input_bag: Path, output_bag: Path, perturbation_yaml: Path, summary_path: Path) -> None:
    spec = yaml.safe_load(perturbation_yaml.read_text())
    chains = build_chain(spec)
    typestore = get_typestore(Stores.ROS2_HUMBLE)

    if output_bag.exists():
        shutil.rmtree(output_bag)
    output_bag.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    counts: dict[str, dict[str, int]] = {}
    with Reader(input_bag) as reader:
        start_ns = int(reader.start_time)
        with Writer(output_bag, version=8) as writer:
            connections = {
                conn.id: writer.add_connection(
                    conn.topic,
                    conn.msgtype,
                    typestore=typestore,
                    offered_qos_profiles=getattr(conn, "offered_qos_profiles", ()),
                )
                for conn in reader.connections
            }
            for conn, timestamp, raw in reader.messages():
                topic_counts = counts.setdefault(conn.topic, {"in": 0, "out": 0, "dropped": 0})
                topic_counts["in"] += 1
                sensor = _sensor_key(conn.topic, conn.msgtype)
                if sensor is None:
                    writer.write(connections[conn.id], timestamp, raw)
                    topic_counts["out"] += 1
                    continue

                msg = typestore.deserialize_cdr(raw, conn.msgtype)
                t = _message_time_s(msg, timestamp, start_ns)
                data = _to_perturbation_dict(msg, conn.msgtype, t)
                data = apply_chain(data, chains.get("global", []))
                data = apply_chain(data, chains.get(sensor, []))
                if data is None:
                    topic_counts["dropped"] += 1
                    continue

                out_timestamp = start_ns + int(float(data.get("t", t)) * 1_000_000_000)
                _set_stamp(msg, out_timestamp)
                msg = _from_perturbation_dict(data, msg, conn.msgtype)
                writer.write(connections[conn.id], out_timestamp, typestore.serialize_cdr(msg, conn.msgtype))
                topic_counts["out"] += 1

    summary = {
        "input_bag": str(input_bag),
        "output_bag": str(output_bag),
        "perturbation_yaml": str(perturbation_yaml),
        "active_chains": {sensor: len(chain) for sensor, chain in chains.items()},
        "topics": counts,
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")


def run_offline_demo(perturbation_yaml: Path, output: Path) -> None:
    """Small non-ROS path used by CI/local smoke tests."""
    spec = yaml.safe_load(perturbation_yaml.read_text())
    chains = build_chain(spec)
    sample = {
        "lidar": {"t": 0.0, "points": [[1.0, 0.0, 0.0, 1.0], [30.0, 0.0, 0.0, 0.5]]},
        "camera": {"t": 0.0, "image": [[80, 90], [100, 110]]},
        "imu": {"t": 0.0, "gyro": [0.0, 0.0, 0.0], "accel": [0.0, 0.0, 9.8]},
        "gps": {"t": 0.0, "latitude": 49.0, "longitude": 8.0},
    }
    result = {sensor: apply_chain(msg, chains.get(sensor, [])) for sensor, msg in sample.items()}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, default=lambda value: value.tolist()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-bag", "--input_bag", type=Path)
    parser.add_argument("--perturbation-yaml", "--perturbation_yaml", required=True)
    parser.add_argument("--output", default="/results/perturbation_injector_demo.json")
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()

    output = Path(args.output)
    perturbation_yaml = Path(args.perturbation_yaml)
    if args.input_bag:
        summary = args.summary or output.with_suffix(".summary.json")
        perturb_bag(Path(args.input_bag), output, perturbation_yaml, summary)
    else:
        run_offline_demo(perturbation_yaml, output)


if __name__ == "__main__":
    main()
