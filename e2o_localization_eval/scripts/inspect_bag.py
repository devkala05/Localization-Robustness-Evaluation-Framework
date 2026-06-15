#!/usr/bin/env python3
"""Inspect ROS1 bag topics and report possible ground-truth candidates."""
import argparse
import collections
import os
import sys

try:
    import rosbag
except Exception as exc:  # pragma: no cover
    print("ERROR: rosbag Python module is unavailable. Run this inside ./run.sh inspect.", file=sys.stderr)
    raise

GT_TYPES = {
    "nav_msgs/Odometry",
    "geometry_msgs/PoseStamped",
    "geometry_msgs/PoseWithCovarianceStamped",
    "nav_msgs/Path",
    "sensor_msgs/NavSatFix",
    "tf2_msgs/TFMessage",
}

EXPECTED = [
    "/camera/color/image_raw",
    "/lidar102/velodyne_points",
    "/lidar103/velodyne_points",
    "/lidar104/velodyne_points",
    "/merged/velodyne_points",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bag", required=True)
    ap.add_argument("--sample-images", action="store_true", default=True)
    args = ap.parse_args()
    if not os.path.exists(args.bag):
        raise FileNotFoundError(args.bag)

    with rosbag.Bag(args.bag, "r") as bag:
        info = bag.get_type_and_topic_info()
        start = bag.get_start_time()
        end = bag.get_end_time()
        print("\n=== BAG SUMMARY ===")
        print(f"bag:      {args.bag}")
        print(f"duration: {end - start:.3f} sec")
        print(f"start:    {start:.9f}")
        print(f"end:      {end:.9f}")
        print("\n=== TOPICS ===")
        rows = []
        for topic, meta in sorted(info.topics.items()):
            rows.append((topic, meta.msg_type, meta.message_count, meta.frequency or 0.0))
        for topic, typ, count, freq in rows:
            print(f"{topic:45s} {count:8d} msgs  {freq:8.3f} Hz  {typ}")

        print("\n=== EXPECTED e2o TOPICS ===")
        for topic in EXPECTED:
            if topic in info.topics:
                meta = info.topics[topic]
                print(f"OK   {topic:35s} {meta.message_count:8d} msgs  {meta.msg_type}")
            else:
                print(f"MISS {topic}")

        print("\n=== IMAGE/LIDAR FIRST MESSAGE DETAILS ===")
        for topic in EXPECTED:
            if topic not in info.topics:
                continue
            try:
                for _topic, msg, t in bag.read_messages(topics=[topic]):
                    frame = getattr(getattr(msg, "header", None), "frame_id", "")
                    stamp = getattr(getattr(msg, "header", None), "stamp", None)
                    stamp_s = stamp.to_sec() if stamp else t.to_sec()
                    if hasattr(msg, "height") and hasattr(msg, "width"):
                        extra = f"width={msg.width} height={msg.height} encoding={getattr(msg, 'encoding', '')}"
                    elif hasattr(msg, "point_step"):
                        extra = f"point_step={msg.point_step} row_step={msg.row_step} height={msg.height} width={msg.width}"
                    else:
                        extra = ""
                    print(f"{topic:35s} frame='{frame}' stamp={stamp_s:.9f} {extra}")
                    break
            except Exception as exc:
                print(f"{topic:35s} sample failed: {exc}")

        print("\n=== GROUND-TRUTH CANDIDATES ===")
        candidates = []
        for topic, meta in sorted(info.topics.items()):
            name = topic.lower()
            typ = meta.msg_type
            score = 0
            if typ in GT_TYPES:
                score += 10
            for word in ["gt", "ground", "truth", "odom", "pose", "ins", "gps", "gnss", "novatel", "rtk", "tf"]:
                if word in name:
                    score += 2
            if score > 0 and typ in GT_TYPES:
                candidates.append((score, topic, typ, meta.message_count))
        if not candidates:
            print("No pose/odometry/GPS/TF ground-truth candidate topics found in this bag.")
            print("The metadata you supplied lists only Image and PointCloud2 topics, so this is expected unless hidden topics exist.")
        else:
            for score, topic, typ, count in sorted(candidates, reverse=True):
                print(f"score={score:2d} {topic:45s} {count:8d} msgs  {typ}")
            print("\nUse one of these with: ./run.sh gt --gt-topic /topic/name")


if __name__ == "__main__":
    main()
