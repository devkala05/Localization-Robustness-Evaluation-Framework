#!/usr/bin/env python3
"""Extract a reference trajectory from a ROS1 bag into TUM format.

This script never invents ground truth. It extracts only from an existing pose,
odometry, GPS, path, or selected TF topic inside the bag.
"""
import argparse
import bisect
import math
import os
import sys

try:
    import rosbag
except Exception:
    print("ERROR: rosbag Python module unavailable. Run via ./run.sh gt.", file=sys.stderr)
    raise

SUPPORTED = {
    "nav_msgs/Odometry",
    "geometry_msgs/PoseStamped",
    "geometry_msgs/PoseWithCovarianceStamped",
    "nav_msgs/Path",
    "sensor_msgs/NavSatFix",
    "tf2_msgs/TFMessage",
}
PREFERRED_WORDS = ["ground_truth", "ground", "truth", "gt", "rtk", "ins", "novatel", "gps", "gnss", "odom", "pose"]


def q_identity():
    return (0.0, 0.0, 0.0, 1.0)


def pose_to_row(stamp, pose):
    p, q = pose.position, pose.orientation
    return (stamp, p.x, p.y, p.z, q.x, q.y, q.z, q.w)


def navsat_to_enu(lat, lon, alt, origin):
    # Lightweight local tangent approximation, enough for initial plotting.
    # For final scoring from GNSS, prefer surveyed ENU conversion or pyproj.
    lat0, lon0, alt0 = origin
    R = 6378137.0
    dlat = math.radians(lat - lat0)
    dlon = math.radians(lon - lon0)
    mean_lat = math.radians((lat + lat0) * 0.5)
    x = R * dlon * math.cos(mean_lat)
    y = R * dlat
    z = alt - alt0
    return x, y, z


def topic_candidates(bag):
    info = bag.get_type_and_topic_info()
    cands = []
    for topic, meta in info.topics.items():
        if meta.msg_type not in SUPPORTED:
            continue
        score = 10 if meta.msg_type != "tf2_msgs/TFMessage" else 5
        low = topic.lower()
        for i, word in enumerate(PREFERRED_WORDS):
            if word in low:
                score += 20 - i
        cands.append((score, topic, meta.msg_type, meta.message_count))
    return sorted(cands, reverse=True)


def choose_auto(cands):
    # Avoid selecting /tf automatically unless no other candidate exists.
    non_tf = [c for c in cands if c[2] != "tf2_msgs/TFMessage"]
    return (non_tf or cands)[0] if cands else None


def read_orientation_rows(bag, topic):
    rows = []
    for _topic, msg, bag_time in bag.read_messages(topics=[topic]):
        stamp = msg.header.stamp.to_sec() or bag_time.to_sec()
        q = msg.orientation
        quat = (q.x, q.y, q.z, q.w)
        if all(math.isfinite(v) for v in quat) and any(abs(v) > 1e-12 for v in quat):
            rows.append((stamp, *quat))
    rows.sort(key=lambda x: x[0])
    return rows


def nearest_orientation(stamp, orientation_rows, orientation_times, max_dt):
    if not orientation_rows:
        return q_identity()
    idx = bisect.bisect_left(orientation_times, stamp)
    candidates = []
    if idx < len(orientation_rows):
        candidates.append(orientation_rows[idx])
    if idx > 0:
        candidates.append(orientation_rows[idx - 1])
    nearest = min(candidates, key=lambda row: abs(row[0] - stamp))
    if max_dt > 0 and abs(nearest[0] - stamp) > max_dt:
        return q_identity()
    return nearest[1], nearest[2], nearest[3], nearest[4]


def extract(args):
    rows = []
    gps_origin = None
    seen_path_stamps = set()
    with rosbag.Bag(args.bag, "r") as bag:
        info = bag.get_type_and_topic_info()
        orientation_rows = []
        orientation_times = []
        if args.orientation_topic:
            if args.orientation_topic not in info.topics:
                print(f"ERROR: requested orientation topic not found: {args.orientation_topic}", file=sys.stderr)
                return 6
            if info.topics[args.orientation_topic].msg_type != "sensor_msgs/Imu":
                print("ERROR: --orientation-topic must be sensor_msgs/Imu", file=sys.stderr)
                return 7
            orientation_rows = read_orientation_rows(bag, args.orientation_topic)
            orientation_times = [row[0] for row in orientation_rows]
            print(f"Loaded {len(orientation_rows)} IMU orientations from {args.orientation_topic}")
        if args.gt_topic == "auto":
            cands = topic_candidates(bag)
            chosen = choose_auto(cands)
            if not chosen:
                print("ERROR: no extractable ground-truth candidate topic found.", file=sys.stderr)
                print("Run './run.sh inspect' to confirm the bag topics. The known metadata only lists camera/lidar topics.", file=sys.stderr)
                return 2
            _, topic, typ, _ = chosen
            print(f"Auto-selected GT candidate: {topic} [{typ}]")
        else:
            topic = args.gt_topic
            if topic not in info.topics:
                print(f"ERROR: requested topic not found: {topic}", file=sys.stderr)
                return 3
            typ = info.topics[topic].msg_type
            if typ not in SUPPORTED:
                print(f"ERROR: unsupported topic type for GT extraction: {typ}", file=sys.stderr)
                return 4

        for _topic, msg, bag_time in bag.read_messages(topics=[topic]):
            typ = info.topics[topic].msg_type
            if typ == "nav_msgs/Odometry":
                stamp = msg.header.stamp.to_sec() or bag_time.to_sec()
                rows.append(pose_to_row(stamp, msg.pose.pose))
            elif typ == "geometry_msgs/PoseStamped":
                stamp = msg.header.stamp.to_sec() or bag_time.to_sec()
                rows.append(pose_to_row(stamp, msg.pose))
            elif typ == "geometry_msgs/PoseWithCovarianceStamped":
                stamp = msg.header.stamp.to_sec() or bag_time.to_sec()
                rows.append(pose_to_row(stamp, msg.pose.pose))
            elif typ == "nav_msgs/Path":
                for ps in msg.poses:
                    stamp = ps.header.stamp.to_sec() or msg.header.stamp.to_sec() or bag_time.to_sec()
                    key = round(stamp, 9)
                    if key in seen_path_stamps:
                        continue
                    seen_path_stamps.add(key)
                    rows.append(pose_to_row(stamp, ps.pose))
            elif typ == "sensor_msgs/NavSatFix":
                if not math.isfinite(msg.latitude) or not math.isfinite(msg.longitude):
                    continue
                alt = msg.altitude if math.isfinite(msg.altitude) else 0.0
                if gps_origin is None:
                    gps_origin = (msg.latitude, msg.longitude, alt)
                x, y, z = navsat_to_enu(msg.latitude, msg.longitude, alt, gps_origin)
                stamp = msg.header.stamp.to_sec() or bag_time.to_sec()
                qx, qy, qz, qw = nearest_orientation(
                    stamp,
                    orientation_rows,
                    orientation_times,
                    args.orientation_max_dt,
                )
                rows.append((stamp, x, y, z, qx, qy, qz, qw))
            elif typ == "tf2_msgs/TFMessage":
                for tr in msg.transforms:
                    if args.tf_parent and tr.header.frame_id != args.tf_parent:
                        continue
                    if args.tf_child and tr.child_frame_id != args.tf_child:
                        continue
                    if not args.tf_parent and not args.tf_child:
                        continue
                    stamp = tr.header.stamp.to_sec() or bag_time.to_sec()
                    p, q = tr.transform.translation, tr.transform.rotation
                    rows.append((stamp, p.x, p.y, p.z, q.x, q.y, q.z, q.w))

    rows.sort(key=lambda x: x[0])
    # Deduplicate exact timestamps.
    clean = []
    last_t = None
    for row in rows:
        if last_t is not None and abs(row[0] - last_t) < 1e-9:
            continue
        clean.append(row)
        last_t = row[0]
    if not clean:
        print("ERROR: selected topic produced no valid poses.", file=sys.stderr)
        if typ == "tf2_msgs/TFMessage":
            print("For /tf extraction, pass --tf-parent and --tf-child.", file=sys.stderr)
        return 5

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(f"# extracted_from_bag {os.path.basename(args.bag)}\n")
        f.write(f"# source_topic {topic}\n")
        f.write("# format: timestamp tx ty tz qx qy qz qw\n")
        for row in clean:
            f.write("{:.9f} {:.9f} {:.9f} {:.9f} {:.9f} {:.9f} {:.9f} {:.9f}\n".format(*row))
    print(f"Wrote {len(clean)} poses to {args.output}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bag", required=True)
    ap.add_argument("--gt-topic", default="auto", help="auto or exact topic name")
    ap.add_argument("--output", required=True)
    ap.add_argument("--tf-parent", default="", help="Required when extracting from /tf")
    ap.add_argument("--tf-child", default="", help="Required when extracting from /tf")
    ap.add_argument("--orientation-topic", default="", help="Optional sensor_msgs/Imu topic used for NavSatFix orientation")
    ap.add_argument("--orientation-max-dt", type=float, default=0.05, help="Max seconds between GPS and IMU orientation; <=0 disables the limit")
    args = ap.parse_args()
    sys.exit(extract(args))


if __name__ == "__main__":
    main()
