#!/usr/bin/env python3
"""Publish saved benchmark CSV trajectories into RViz.

This is an offline visualizer: it does not play the bag and does not run any
localization algorithm. It reads data/results/<algo>/per_<N>/trajectory.csv and
publishes Path + MarkerArray topics so RViz can compare all saved trajectories
against the UrbanNav ground truth.
"""
import argparse
import csv
import math
import os
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import rospy
from geometry_msgs.msg import Point, PoseStamped
from nav_msgs.msg import Path
from visualization_msgs.msg import Marker, MarkerArray

WGS84_A = 6378137.0
WGS84_E2 = 6.69437999014e-3

ALGO_CANONICAL = {
    "fastlio2": "fast_lio2", "fast_lio2": "fast_lio2", "fast-lio2": "fast_lio2",
    "lvisam": "lvi_sam", "lvi_sam": "lvi_sam", "lvi-sam": "lvi_sam",
    "fastlivo2": "fast_livo2", "fast_livo2": "fast_livo2", "fast-livo2": "fast_livo2",
    "rtabmap": "rtab_map", "rtab_map": "rtab_map", "rtab-map": "rtab_map",
    "adaptive_w_lvio": "adaptive_w_lvio", "adaptive-w-lvio": "adaptive_w_lvio",
    "orbslam3": "orb_slam3", "orb_slam3": "orb_slam3", "orb-slam3": "orb_slam3", "orb": "orb_slam3",
    "r3live": "r3live", "r3-live": "r3live",
}
ALL_ALGOS = ["fast_lio2", "lvi_sam", "fast_livo2", "rtab_map", "adaptive_w_lvio", "orb_slam3", "r3live"]
DISPLAY_NAMES = {
    "fast_lio2": "FAST-LIO2",
    "lvi_sam": "LVI-SAM",
    "fast_livo2": "FAST-LIVO2",
    "rtab_map": "RTAB-Map",
    "adaptive_w_lvio": "Adaptive-W LVIO",
    "orb_slam3": "ORB-SLAM3",
    "r3live": "R3LIVE",
}
# Result folder IDs used by the production codebase.
RESULT_ID = {key: key for key in ALL_ALGOS}

COLORS = {
    "gt": (0.10, 1.00, 0.25, 1.0),
    "fast_lio2": (1.00, 0.72, 0.10, 1.0),
    "lvi_sam": (0.20, 0.55, 1.00, 1.0),
    "fast_livo2": (1.00, 0.20, 0.20, 1.0),
    "rtab_map": (0.75, 0.35, 1.00, 1.0),
    "adaptive_w_lvio": (0.10, 0.90, 1.00, 1.0),
    "orb_slam3": (1.00, 0.40, 0.85, 1.0),
    "r3live": (0.80, 1.00, 0.10, 1.0),
    "missing": (0.80, 0.80, 0.80, 1.0),
}


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))


def resolve_path(path: str) -> str:
    if not path:
        return path
    if os.path.isabs(path):
        return path
    # Prefer current working dir, then repository root.
    cwd_path = os.path.abspath(path)
    if os.path.exists(cwd_path):
        return cwd_path
    return os.path.join(repo_root(), path)


def dms_to_deg(degrees: float, minutes: float, seconds: float) -> float:
    sign = -1.0 if degrees < 0 else 1.0
    return sign * (abs(degrees) + minutes / 60.0 + seconds / 3600.0)


def ecef_from_lla(lat_deg: float, lon_deg: float, height: float) -> Tuple[float, float, float]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    normal = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    return (
        (normal + height) * cos_lat * math.cos(lon),
        (normal + height) * cos_lat * math.sin(lon),
        (normal * (1.0 - WGS84_E2) + height) * sin_lat,
    )


def enu_from_ecef_delta(dx: float, dy: float, dz: float, ref_lat_deg: float, ref_lon_deg: float) -> Tuple[float, float, float]:
    lat = math.radians(ref_lat_deg)
    lon = math.radians(ref_lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)
    east = -sin_lon * dx + cos_lon * dy
    north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
    up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
    return east, north, up


def rotate_xy(x: float, y: float, yaw_offset_rad: float) -> Tuple[float, float]:
    c = math.cos(yaw_offset_rad)
    s = math.sin(yaw_offset_rad)
    return c * x - s * y, s * x + c * y


def parse_algos(value: str, results_root: str, per: int) -> List[str]:
    value = (value or "all").strip().lower()
    if value in {"all", "*"}:
        available = []
        for algo in ALL_ALGOS:
            if os.path.isfile(trajectory_csv(results_root, algo, per)):
                available.append(algo)
        return available or list(ALL_ALGOS)
    out = []
    for token in value.replace("/", ",").replace(" ", ",").split(","):
        token = token.strip()
        if not token:
            continue
        key = ALGO_CANONICAL.get(token)
        if key is None:
            raise SystemExit("Unknown algorithm '{}'. Use all or one of: {}".format(token, ", ".join(ALL_ALGOS)))
        if key not in out:
            out.append(key)
    return out


def trajectory_csv(results_root: str, algo: str, per: int) -> str:
    return os.path.join(resolve_path(results_root), RESULT_ID[algo], "per_{}".format(per), "trajectory.csv")


def load_csv_trajectory(path: str) -> List[dict]:
    path = resolve_path(path)
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                rows.append({
                    "stamp": float(row.get("stamp", len(rows))),
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                    "z": float(row.get("z", 0.0) or 0.0),
                    "qx": float(row.get("qx", 0.0) or 0.0),
                    "qy": float(row.get("qy", 0.0) or 0.0),
                    "qz": float(row.get("qz", 0.0) or 0.0),
                    "qw": float(row.get("qw", 1.0) or 1.0),
                })
            except (KeyError, TypeError, ValueError):
                continue
    rows.sort(key=lambda r: r["stamp"])
    return rows


def quaternion_yaw(qx: float, qy: float, qz: float, qw: float) -> float:
    return math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))


def yaw_quaternion(yaw: float) -> Tuple[float, float, float, float]:
    return 0.0, 0.0, math.sin(0.5 * yaw), math.cos(0.5 * yaw)


def load_ground_truth(path: str, yaw_offset_deg: float = 0.0) -> List[dict]:
    """Read UrbanNav INS text or E2O TUM and normalize to the initial body frame."""
    path = resolve_path(path)
    if not os.path.isfile(path):
        return []
    raw = []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            try:
                if len(parts) == 8:
                    v = [float(x) for x in parts]
                    raw.append({"format": "tum", "stamp": v[0], "x": v[1], "y": v[2], "z": v[3],
                                "yaw": quaternion_yaw(v[4], v[5], v[6], v[7])})
                elif len(parts) >= 20:
                    raw.append({"format": "urbannav", "stamp": float(parts[0]),
                                "lat": dms_to_deg(float(parts[3]), float(parts[4]), float(parts[5])),
                                "lon": dms_to_deg(float(parts[6]), float(parts[7]), float(parts[8])),
                                "h": float(parts[9]), "heading": float(parts[18])})
            except ValueError:
                continue
    if not raw:
        return []
    raw.sort(key=lambda r: r["stamp"])
    yaw_offset_rad = math.radians(yaw_offset_deg)
    if raw[0]["format"] == "tum":
        raw = [r for r in raw if r["format"] == "tum"]
        ref = raw[0]
        angle = -ref["yaw"] + yaw_offset_rad
        out = []
        for row in raw:
            x, y = rotate_xy(row["x"] - ref["x"], row["y"] - ref["y"], angle)
            yaw = math.atan2(math.sin(row["yaw"] - ref["yaw"] + yaw_offset_rad),
                             math.cos(row["yaw"] - ref["yaw"] + yaw_offset_rad))
            qx, qy, qz, qw = yaw_quaternion(yaw)
            out.append({"stamp": row["stamp"], "x": x, "y": y, "z": row["z"] - ref["z"],
                        "qx": qx, "qy": qy, "qz": qz, "qw": qw})
        return out
    raw = [r for r in raw if r["format"] == "urbannav"]
    ref = raw[0]
    ref_ecef = ecef_from_lla(ref["lat"], ref["lon"], ref["h"])
    heading = math.radians(ref["heading"])
    forward_e, forward_n = math.sin(heading), math.cos(heading)
    right_e, right_n = math.cos(heading), -math.sin(heading)
    out = []
    for row in raw:
        ecef = ecef_from_lla(row["lat"], row["lon"], row["h"])
        east, north, up = enu_from_ecef_delta(
            ecef[0] - ref_ecef[0], ecef[1] - ref_ecef[1], ecef[2] - ref_ecef[2], ref["lat"], ref["lon"]
        )
        x = east * right_e + north * right_n
        y = east * forward_e + north * forward_n
        x, y = rotate_xy(x, y, yaw_offset_rad)
        out.append({"stamp": row["stamp"], "x": x, "y": y, "z": up,
                    "qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0})
    return out

def downsample(rows: Sequence[dict], max_points: int) -> List[dict]:
    if max_points <= 0 or len(rows) <= max_points:
        return list(rows)
    step = max(1, int(math.ceil(float(len(rows)) / float(max_points))))
    out = list(rows[::step])
    if rows[-1] is not out[-1]:
        out.append(rows[-1])
    return out


def make_path(rows: Sequence[dict], frame_id: str) -> Path:
    msg = Path()
    msg.header.frame_id = frame_id
    stamp = rospy.Time.now()
    msg.header.stamp = stamp
    for row in rows:
        pose = PoseStamped()
        pose.header.frame_id = frame_id
        pose.header.stamp = stamp
        pose.pose.position.x = row["x"]
        pose.pose.position.y = row["y"]
        pose.pose.position.z = row["z"]
        pose.pose.orientation.x = row.get("qx", 0.0)
        pose.pose.orientation.y = row.get("qy", 0.0)
        pose.pose.orientation.z = row.get("qz", 0.0)
        pose.pose.orientation.w = row.get("qw", 1.0)
        msg.poses.append(pose)
    return msg


def marker_color(marker: Marker, rgba: Tuple[float, float, float, float]) -> None:
    marker.color.r = rgba[0]
    marker.color.g = rgba[1]
    marker.color.b = rgba[2]
    marker.color.a = rgba[3]


def make_line_marker(ns: str, marker_id: int, rows: Sequence[dict], frame_id: str, color: Tuple[float, float, float, float], width: float) -> Marker:
    m = Marker()
    m.header.frame_id = frame_id
    m.header.stamp = rospy.Time.now()
    m.ns = ns
    m.id = marker_id
    m.type = Marker.LINE_STRIP
    m.action = Marker.ADD
    m.pose.orientation.w = 1.0
    m.scale.x = width
    marker_color(m, color)
    for row in rows:
        p = Point()
        p.x = row["x"]
        p.y = row["y"]
        p.z = row["z"]
        m.points.append(p)
    return m


def make_sphere(ns: str, marker_id: int, row: dict, frame_id: str, color: Tuple[float, float, float, float], scale: float) -> Marker:
    m = Marker()
    m.header.frame_id = frame_id
    m.header.stamp = rospy.Time.now()
    m.ns = ns
    m.id = marker_id
    m.type = Marker.SPHERE
    m.action = Marker.ADD
    m.pose.position.x = row["x"]
    m.pose.position.y = row["y"]
    m.pose.position.z = row["z"]
    m.pose.orientation.w = 1.0
    m.scale.x = scale
    m.scale.y = scale
    m.scale.z = scale
    marker_color(m, color)
    return m


def make_text(ns: str, marker_id: int, row: dict, text: str, frame_id: str, color: Tuple[float, float, float, float], scale: float, dz: float = 2.0) -> Marker:
    m = Marker()
    m.header.frame_id = frame_id
    m.header.stamp = rospy.Time.now()
    m.ns = ns
    m.id = marker_id
    m.type = Marker.TEXT_VIEW_FACING
    m.action = Marker.ADD
    m.pose.position.x = row["x"]
    m.pose.position.y = row["y"]
    m.pose.position.z = row["z"] + dz
    m.pose.orientation.w = 1.0
    m.scale.z = scale
    marker_color(m, color)
    m.text = text
    return m


def build_marker_array(trajs: Dict[str, List[dict]], gt: List[dict], frame_id: str, width: float, max_points: int, per: int) -> MarkerArray:
    arr = MarkerArray()
    marker_id = 0
    if gt:
        ds = downsample(gt, max_points)
        arr.markers.append(make_line_marker("offline_gt", marker_id, ds, frame_id, COLORS["gt"], width * 1.35)); marker_id += 1
        arr.markers.append(make_sphere("offline_gt", marker_id, ds[0], frame_id, COLORS["gt"], width * 8.0)); marker_id += 1
        arr.markers.append(make_text("offline_gt", marker_id, ds[-1], "GT", frame_id, COLORS["gt"], 4.0)); marker_id += 1
    legend_x = 0.0
    legend_y = 0.0
    legend_z = 8.0
    if gt:
        legend_x = gt[0]["x"]
        legend_y = gt[0]["y"]
        legend_z = gt[0]["z"] + 8.0
    legend_rows = []
    for algo, rows in trajs.items():
        if not rows:
            continue
        ds = downsample(rows, max_points)
        color = COLORS.get(algo, (1.0, 1.0, 1.0, 1.0))
        arr.markers.append(make_line_marker("offline_{}".format(algo), marker_id, ds, frame_id, color, width)); marker_id += 1
        arr.markers.append(make_sphere("offline_{}".format(algo), marker_id, ds[0], frame_id, color, width * 5.5)); marker_id += 1
        arr.markers.append(make_sphere("offline_{}".format(algo), marker_id, ds[-1], frame_id, color, width * 7.0)); marker_id += 1
        arr.markers.append(make_text("offline_{}".format(algo), marker_id, ds[-1], DISPLAY_NAMES.get(algo, algo), frame_id, color, 3.6)); marker_id += 1
        legend_rows.append(DISPLAY_NAMES.get(algo, algo))
    if legend_rows:
        fake = {"x": legend_x, "y": legend_y, "z": legend_z}
        text = "Offline trajectory compare | per_{}\nGT + {}".format(per, ", ".join(legend_rows))
        arr.markers.append(make_text("offline_legend", marker_id, fake, text, frame_id, (1.0, 1.0, 1.0, 1.0), 4.5, dz=0.0)); marker_id += 1
    return arr


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish saved benchmark trajectories into RViz")
    parser.add_argument("--per", type=int, required=True, help="Perturbation/run id, e.g. 0")
    parser.add_argument("--algo", default="all", help="all or comma-separated names")
    parser.add_argument("--dataset", choices=("e2o", "urbannav"), default=os.environ.get("DATASET", "e2o"))
    parser.add_argument("--results-root", default="", help="Results root containing <algo>/per_N/trajectory.csv")
    parser.add_argument("--gt", default="", help="UrbanNav INS text or E2O TUM ground truth")
    parser.add_argument("--frame-id", default="camera_init")
    parser.add_argument("--yaw-offset-deg", type=float, default=float(os.environ.get("GT_YAW_OFFSET_DEG", "0.0")))
    parser.add_argument("--rate", type=float, default=2.0)
    parser.add_argument("--max-points", type=int, default=12000)
    parser.add_argument("--line-width", type=float, default=0.35)
    args = parser.parse_args()
    if not args.results_root:
        args.results_root = "/data/results/{}".format(args.dataset)
    if not args.gt:
        args.gt = ("/data/e2o/ground_truth/one_full_loop_gt.tum"
                   if args.dataset == "e2o" else "/data/UrbanNav_TST_GT_raw.txt")

    rospy.init_node("offline_trajectory_rviz", anonymous=False)

    algos = parse_algos(args.algo, args.results_root, args.per)
    gt = load_ground_truth(args.gt, args.yaw_offset_deg)
    if not gt:
        rospy.logwarn("No GT loaded from %s", args.gt)

    trajs = {}
    missing = []
    for algo in algos:
        csv_path = trajectory_csv(args.results_root, algo, args.per)
        rows = load_csv_trajectory(csv_path)
        if rows:
            trajs[algo] = rows
            rospy.loginfo("Loaded %s: %d poses from %s", DISPLAY_NAMES.get(algo, algo), len(rows), csv_path)
        else:
            missing.append((algo, csv_path))
            rospy.logwarn("Missing/empty trajectory for %s: %s", DISPLAY_NAMES.get(algo, algo), csv_path)

    if not trajs and not gt:
        rospy.logerr("Nothing to publish. Check --per, --algo, --results-root and --gt.")
        return 2

    path_publishers = {}
    if gt:
        path_publishers["gt"] = rospy.Publisher("/ground_truth_path", Path, queue_size=1, latch=True)
        path_publishers["gt_offline"] = rospy.Publisher("/offline/ground_truth/path", Path, queue_size=1, latch=True)
    for algo in trajs:
        path_publishers[algo] = rospy.Publisher("/offline/{}/path".format(algo), Path, queue_size=1, latch=True)
    marker_pub = rospy.Publisher("/offline/trajectory_markers", MarkerArray, queue_size=1, latch=True)

    gt_path = make_path(downsample(gt, args.max_points), args.frame_id) if gt else None
    algo_paths = {algo: make_path(downsample(rows, args.max_points), args.frame_id) for algo, rows in trajs.items()}
    marker_array = build_marker_array(trajs, gt, args.frame_id, args.line_width, args.max_points, args.per)

    rospy.loginfo("Publishing offline RViz comparison for per_%d. Loaded: %s", args.per, ", ".join(DISPLAY_NAMES.get(a, a) for a in trajs))
    if missing:
        rospy.logwarn("Missing algorithms: %s", ", ".join(DISPLAY_NAMES.get(a, a) for a, _ in missing))

    rate = rospy.Rate(max(0.2, args.rate))
    while not rospy.is_shutdown():
        now = rospy.Time.now()
        if gt_path is not None:
            gt_path.header.stamp = now
            path_publishers["gt"].publish(gt_path)
            path_publishers["gt_offline"].publish(gt_path)
        for algo, path in algo_paths.items():
            path.header.stamp = now
            path_publishers[algo].publish(path)
        for marker in marker_array.markers:
            marker.header.stamp = now
        marker_pub.publish(marker_array)
        rate.sleep()
    return 0


if __name__ == "__main__":
    sys.exit(main())
