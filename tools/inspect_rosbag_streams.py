#!/usr/bin/env python3
"""Stream selected ROS bag topics and emit observed timing/frame metadata."""
from __future__ import annotations

import argparse
import json

import rosbag


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bag")
    parser.add_argument("topics", nargs="+")
    args = parser.parse_args()
    requested = set(args.topics)
    report = {
        topic: {
            "count": 0,
            "start_timestamp_s": None,
            "end_timestamp_s": None,
            "non_monotonic_timestamps": 0,
            "frame_ids": [],
        }
        for topic in args.topics
    }
    previous = {topic: None for topic in args.topics}
    frames = {topic: set() for topic in args.topics}
    with rosbag.Bag(args.bag, "r") as bag:
        for topic, message, bag_stamp in bag.read_messages(topics=list(requested)):
            item = report[topic]
            header = getattr(message, "header", None)
            stamp = getattr(header, "stamp", None)
            stamp_s = stamp.to_sec() if stamp is not None and stamp.to_sec() > 0.0 else bag_stamp.to_sec()
            item["count"] += 1
            if item["start_timestamp_s"] is None:
                item["start_timestamp_s"] = stamp_s
            item["end_timestamp_s"] = stamp_s
            if previous[topic] is not None and stamp_s < previous[topic]:
                item["non_monotonic_timestamps"] += 1
            previous[topic] = stamp_s
            frame_id = getattr(header, "frame_id", "") if header is not None else ""
            if frame_id:
                frames[topic].add(frame_id)
    for topic, item in report.items():
        item["frame_ids"] = sorted(frames[topic])
        start, end = item["start_timestamp_s"], item["end_timestamp_s"]
        item["approx_frequency_hz"] = item["count"] / (end - start) if start is not None and end > start else None
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
