#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore


def stamp_to_float(stamp) -> float:
    return float(stamp.sec) + float(stamp.nanosec) * 1e-9


def convert(input_bag: Path, output: Path, topic: str) -> int:
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    rows = []
    with Reader(input_bag) as reader:
        for connection, _, raw in reader.messages():
            if connection.topic != topic:
                continue
            msg = typestore.deserialize_cdr(raw, connection.msgtype)
            pose = msg.pose.pose
            rows.append(
                (
                    stamp_to_float(msg.header.stamp),
                    pose.position.x,
                    pose.position.y,
                    pose.position.z,
                    pose.orientation.x,
                    pose.orientation.y,
                    pose.orientation.z,
                    pose.orientation.w,
                )
            )

    if not rows:
        raise RuntimeError(f"no messages found on {topic} in {input_bag}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as handle:
        for row in rows:
            handle.write(" ".join(f"{float(value):.9f}" for value in row) + "\n")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-bag", "--input_bag", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--topic", default="/localization/odometry")
    args = parser.parse_args()
    count = convert(args.input_bag, args.output, args.topic)
    print(f"Wrote {count} poses from {args.topic} to {args.output}")


if __name__ == "__main__":
    main()
