#!/usr/bin/env python3
"""Inspect the selected public sequences without loading them into memory."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shlex
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def human_bytes(value: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    number = float(value)
    for unit in units:
        if number < 1024.0 or unit == units[-1]:
            return f"{number:.2f} {unit}"
        number /= 1024.0
    raise AssertionError


def tree_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def first_last_csv(path: Path, stamp_field: str, divisor: float = 1.0):
    first = last = None
    count = 0
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            stamp = float(row[stamp_field]) / divisor
            first = stamp if first is None else first
            last = stamp
            count += 1
    return first, last, count


def inspect_boreas(config: dict, sequence: Path) -> dict:
    streams = {}
    bounds = []
    for name, suffix, divisor in (("lidar", ".bin", 1e6), ("camera", ".png", 1e6)):
        files = sorted((sequence / name).glob(f"*{suffix}"))
        if files:
            start, end = int(files[0].stem) / divisor, int(files[-1].stem) / divisor
            bounds.extend((start, end))
        else:
            start = end = None
        streams[name] = {"count": len(files), "start_timestamp_s": start,
                         "end_timestamp_s": end, "frame_id": config["sensors"][name]["frame_id"]}
    imu_path = sequence / config["sensors"]["imu"]["file"]
    if imu_path.is_file():
        start, end, count = first_last_csv(imu_path, "time", 1e9)
        bounds.extend((start, end))
    else:
        start = end = None; count = 0
    streams["imu"] = {"count": count, "start_timestamp_s": start,
                      "end_timestamp_s": end, "frame_id": config["sensors"]["imu"]["frame_id"]}
    overall_start, overall_end = (min(bounds), max(bounds)) if bounds else (None, None)
    for stream in streams.values():
        span = (stream["end_timestamp_s"] - stream["start_timestamp_s"]
                if stream["start_timestamp_s"] is not None else 0.0)
        stream["approx_frequency_hz"] = stream["count"] / span if span > 0 else None
    return {
        "dataset": config["dataset"], "sequence": config["sequence"],
        "path": str(sequence.resolve()), "file_size_bytes": tree_bytes(sequence),
        "file_size": human_bytes(tree_bytes(sequence)),
        "start_timestamp_s": overall_start, "end_timestamp_s": overall_end,
        "duration_sec": overall_end - overall_start if bounds else None,
        "available_sensors": sorted(streams), "topics": {
            "/dataset/lidar": "sensor_msgs/PointCloud2",
            "/dataset/imu": "sensor_msgs/Imu", "/dataset/camera": "sensor_msgs/Image"},
        "streams": streams,
        "calibration_files": sorted(str(item.relative_to(sequence)) for item in
                                    (sequence / "calib").glob("*")),
        "ground_truth": str(sequence / config["sensors"]["ground_truth"]["file"]),
        "ground_truth_available": (sequence / config["sensors"]["ground_truth"]["file"]).is_file(),
    }


def rosbag_yaml(bag: Path):
    command = ["rosbag", "info", "--yaml", str(bag)]
    try:
        return yaml.safe_load(subprocess.check_output(command, text=True))
    except FileNotFoundError:
        command = ["docker", "run", "--rm", "-v", f"{bag.parent}:/bags:ro",
                   "ros:noetic-ros-base-focal", "bash", "-lc",
                   f"source /opt/ros/noetic/setup.bash && rosbag info --yaml /bags/{bag.name}"]
        return yaml.safe_load(subprocess.check_output(command, text=True))


def rosbag_stream_details(bag: Path, topics: list[str]) -> dict:
    helper = ROOT / "tools" / "inspect_rosbag_streams.py"
    if importlib.util.find_spec("rosbag") is not None:
        command = ["python3", str(helper), str(bag), *topics]
        return json.loads(subprocess.check_output(command, text=True))
    else:
        # The host normally has no ROS Python packages. The existing fusion
        # image contains rosbag plus the UrbanLoco NovAtel message definitions.
        invocation = " ".join(shlex.quote(value) for value in
                              ["/workspace/tools/inspect_rosbag_streams.py",
                               f"/bags/{bag.name}", *topics])
        command = ["docker", "run", "--rm", "-v", f"{ROOT}:/workspace:ro",
                   "-v", f"{bag.parent}:/bags:ro", "e2o-localization-fusion:latest",
                   "bash", "-lc",
                   f"source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && python3 {invocation}"]
        return json.loads(subprocess.check_output(command, text=True))
def inspect_urban(config: dict, bag: Path, calibration: Path) -> dict:
    info = rosbag_yaml(bag)
    configured = {item["name"]: item for item in config["topics"].values()}
    observed = rosbag_stream_details(bag, list(configured))
    streams = {}
    topics = {}
    for topic in info.get("topics", []):
        topics[topic["topic"]] = topic["type"]
        if topic["topic"] in configured:
            details = observed[topic["topic"]]
            streams[topic["topic"]] = {**details, "type": topic["type"]}
    return {
        "dataset": config["dataset"], "sequence": config["sequence"],
        "path": str(bag.resolve()), "file_size_bytes": bag.stat().st_size,
        "file_size": human_bytes(bag.stat().st_size), "duration_sec": info.get("duration"),
        "start_timestamp_s": info.get("start"), "end_timestamp_s": info.get("end"),
        "available_sensors": sorted(config["topics"]), "topics": topics, "streams": streams,
        "calibration_files": [str(calibration.resolve())],
        "ground_truth": config["topics"]["ground_truth"]["name"],
        "ground_truth_available": config["topics"]["ground_truth"]["name"] in topics,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=("urbanloco", "boreas_rt"))
    parser.add_argument("--sequence", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    config_path = ROOT / "configs" / "datasets" / args.dataset / args.sequence / "sequence.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if args.dataset == "urbanloco":
        base = ROOT / "data" / "datasets" / "urbanloco" / args.sequence
        report = inspect_urban(config, base / config["source"]["filename"],
                               base / config["calibration"]["source"])
    else:
        base = ROOT / "data" / "datasets" / "boreas_rt" / config["display_name"]
        report = inspect_boreas(config, base)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(yaml.safe_dump(report, sort_keys=False).rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
