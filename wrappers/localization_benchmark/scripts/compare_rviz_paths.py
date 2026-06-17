#!/usr/bin/env python3
"""Publish selected benchmark result CSVs into RViz with per-run colors.

This visualizer scans timestamped result folders such as:

  data/results/rtab_map/per_0_rtab_map_20260616_120000/trajectory.csv

It can compare one algorithm across perturbations/GPS modes, one perturbation
across algorithms, or a hand-filtered subset. The trajectory CSV is the source
of path geometry; metrics.json is used when available for GPS/source/config
labels in the RViz legend.
"""
import argparse
import csv
import glob
import hashlib
import json
import math
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

rospy = None
Point = None
PoseStamped = None
Path = None
Marker = None
MarkerArray = None

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

GT_COLOR = (0.05, 1.00, 0.25, 1.0)
PALETTE = [
    (1.00, 0.20, 0.20, 1.0),
    (0.15, 0.55, 1.00, 1.0),
    (1.00, 0.72, 0.10, 1.0),
    (0.75, 0.35, 1.00, 1.0),
    (0.10, 0.90, 1.00, 1.0),
    (1.00, 0.40, 0.85, 1.0),
    (0.75, 1.00, 0.18, 1.0),
    (1.00, 0.48, 0.08, 1.0),
    (0.45, 0.85, 0.45, 1.0),
    (0.95, 0.95, 0.95, 1.0),
    (0.55, 0.35, 1.00, 1.0),
    (0.95, 0.25, 0.55, 1.0),
]


@dataclass
class RunCase:
    algo: str
    per: int
    gps_mode: str
    gps_source: str
    rtk_mode: str
    result_dir: str
    csv_path: str
    metrics_path: str
    timestamp: str
    label: str
    color: Tuple[float, float, float, float]
    rows: Optional[List[dict]] = None


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))


def resolve_path(path: str) -> str:
    if os.path.isabs(path):
        if path.startswith("/data/") and not os.path.exists(path):
            return os.path.join(repo_root(), "data", path[len("/data/"):])
        return path
    cwd_path = os.path.abspath(path)
    if os.path.exists(cwd_path):
        return cwd_path
    return os.path.join(repo_root(), path)


def parse_algos(value: str) -> List[str]:
    value = (value or "all").strip().lower()
    if value in {"all", "*"}:
        return list(ALL_ALGOS)
    out = []
    for token in re.split(r"[, ]+", value):
        token = token.strip()
        if not token:
            continue
        key = ALGO_CANONICAL.get(token)
        if not key:
            raise SystemExit("Unknown algorithm '{}'. Use all or one of: {}".format(token, ", ".join(ALL_ALGOS)))
        if key not in out:
            out.append(key)
    return out


def parse_pers(value: str) -> Optional[List[int]]:
    value = (value or "").strip().lower()
    if not value or value in {"all", "*"}:
        return None
    out = []
    for token in re.split(r"[, ]+", value):
        if not token:
            continue
        if "-" in token:
            start_s, end_s = token.split("-", 1)
            start, end = int(start_s), int(end_s)
            step = 1 if end >= start else -1
            out.extend(range(start, end + step, step))
        else:
            out.append(int(token))
    clean = []
    for per in out:
        if per < 0:
            raise SystemExit("Invalid --per value: {}".format(per))
        if per not in clean:
            clean.append(per)
    return clean


def dms_to_deg(degrees: float, minutes: float, seconds: float) -> float:
    sign = -1.0 if degrees < 0 else 1.0
    return sign * (abs(degrees) + minutes / 60.0 + seconds / 3600.0)


def ecef_from_lla(lat_deg: float, lon_deg: float, height: float) -> Tuple[float, float, float]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat = math.sin(lat)
    normal = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    return (
        (normal + height) * math.cos(lat) * math.cos(lon),
        (normal + height) * math.cos(lat) * math.sin(lon),
        (normal * (1.0 - WGS84_E2) + height) * sin_lat,
    )


def enu_from_ecef_delta(dx: float, dy: float, dz: float, ref_lat_deg: float, ref_lon_deg: float) -> Tuple[float, float, float]:
    lat = math.radians(ref_lat_deg)
    lon = math.radians(ref_lon_deg)
    sin_lat, cos_lat = math.sin(lat), math.cos(lat)
    sin_lon, cos_lon = math.sin(lon), math.cos(lon)
    east = -sin_lon * dx + cos_lon * dy
    north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
    up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
    return east, north, up


def rotate_xy(x: float, y: float, yaw_offset_rad: float) -> Tuple[float, float]:
    c = math.cos(yaw_offset_rad)
    s = math.sin(yaw_offset_rad)
    return c * x - s * y, s * x + c * y


def normalize_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def load_ground_truth(path: str, yaw_offset_deg: float) -> List[dict]:
    path = resolve_path(path)
    if not os.path.isfile(path):
        return []
    if path.lower().endswith(".csv"):
        out = []
        rows = []
        yaw_offset_rad = math.radians(yaw_offset_deg)
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames and "x_m" in reader.fieldnames:
                for row in reader:
                    try:
                        yaw = float(row.get("yaw_rad", "nan"))
                        if not math.isfinite(yaw):
                            yaw = 0.0
                        rows.append({
                            "stamp": float(row.get("timestamp_s") or (float(row["timestamp_ns"]) * 1.0e-9)),
                            "x": float(row["x_m"]),
                            "y": float(row["y_m"]),
                            "z": float(row.get("z_m", 0.0) or 0.0),
                            "yaw": yaw,
                        })
                    except (KeyError, TypeError, ValueError):
                        continue
                rows.sort(key=lambda r: r["stamp"])
                if not rows:
                    return []
                ref = rows[0]
                for row in rows:
                    x, y = rotate_xy(row["x"] - ref["x"], row["y"] - ref["y"], yaw_offset_rad)
                    yaw = normalize_angle(row["yaw"] - ref["yaw"] + yaw_offset_rad)
                    out.append({
                        "stamp": row["stamp"],
                        "x": x,
                        "y": y,
                        "z": row["z"] - ref["z"],
                        "qx": 0.0,
                        "qy": 0.0,
                        "qz": math.sin(0.5 * yaw),
                        "qw": math.cos(0.5 * yaw),
                    })
                out.sort(key=lambda r: r["stamp"])
                return out
    raw = []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) < 20:
                continue
            try:
                raw.append({
                    "stamp": float(parts[0]),
                    "lat": dms_to_deg(float(parts[3]), float(parts[4]), float(parts[5])),
                    "lon": dms_to_deg(float(parts[6]), float(parts[7]), float(parts[8])),
                    "h": float(parts[9]),
                    "heading": float(parts[18]),
                })
            except ValueError:
                continue
    if not raw:
        return []
    ref = raw[0]
    ref_ecef = ecef_from_lla(ref["lat"], ref["lon"], ref["h"])
    heading = math.radians(ref["heading"])
    forward_e, forward_n = math.sin(heading), math.cos(heading)
    right_e, right_n = math.cos(heading), -math.sin(heading)
    yaw_offset_rad = math.radians(yaw_offset_deg)
    out = []
    for row in raw:
        ecef = ecef_from_lla(row["lat"], row["lon"], row["h"])
        east, north, up = enu_from_ecef_delta(
            ecef[0] - ref_ecef[0], ecef[1] - ref_ecef[1], ecef[2] - ref_ecef[2], ref["lat"], ref["lon"]
        )
        x = east * right_e + north * right_n
        y = east * forward_e + north * forward_n
        x, y = rotate_xy(x, y, yaw_offset_rad)
        out.append({"stamp": row["stamp"], "x": x, "y": y, "z": up, "qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0})
    return out


def load_csv_trajectory(path: str) -> List[dict]:
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


def downsample(rows: Sequence[dict], max_points: int) -> List[dict]:
    if max_points <= 0 or len(rows) <= max_points:
        return list(rows)
    step = max(1, int(math.ceil(float(len(rows)) / float(max_points))))
    out = list(rows[::step])
    if rows[-1] is not out[-1]:
        out.append(rows[-1])
    return out


def load_metrics(path: str) -> Dict:
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def parse_result_dir(algo: str, path: str) -> Optional[Tuple[int, str]]:
    name = os.path.basename(path.rstrip("/"))
    latest = re.fullmatch(r"per_(\d+)", name)
    if latest:
        return int(latest.group(1)), "latest"
    prefix = "per_"
    marker = "_{}_".format(algo)
    if not name.startswith(prefix) or marker not in name:
        return None
    per_s = name[len(prefix):name.index(marker)]
    if not per_s.isdigit():
        return None
    timestamp = name[name.index(marker) + len(marker):] or "unknown_time"
    return int(per_s), timestamp


def color_for_key(key: str) -> Tuple[float, float, float, float]:
    digest = hashlib.sha1(key.encode("utf-8")).digest()
    return PALETTE[digest[0] % len(PALETTE)]


def build_label(algo: str, per: int, gps_mode: str, gps_source: str, timestamp: str, metrics: Dict) -> str:
    rmse = (metrics.get("overall") or {}).get("position_rmse_m")
    rmse_text = "rmse n/a" if rmse is None else "rmse {:.2f}m".format(float(rmse))
    return "{} per_{} gps:{} src:{} {} {}".format(
        DISPLAY_NAMES.get(algo, algo), per, gps_mode, gps_source, rmse_text, timestamp
    )


def discover_runs(results_root: str, algos: List[str], pers: Optional[List[int]], gps_filter: str, all_runs: bool) -> List[RunCase]:
    root = resolve_path(results_root)
    selected = []
    for algo in algos:
        algo_dir = os.path.join(root, algo)
        if not os.path.isdir(algo_dir):
            continue
        candidates = []
        for result_dir in sorted(glob.glob(os.path.join(algo_dir, "per_*"))):
            if not os.path.isdir(result_dir):
                continue
            parsed = parse_result_dir(algo, result_dir)
            if parsed is None:
                continue
            per, timestamp = parsed
            if pers is not None and per not in pers:
                continue
            csv_path = os.path.join(result_dir, "trajectory.csv")
            if not os.path.isfile(csv_path):
                continue
            metrics_path = os.path.join(result_dir, "metrics.json")
            metrics = load_metrics(metrics_path)
            gps_mode = str(metrics.get("gps_mode") or "unknown").lower()
            gps_source = str(metrics.get("gps_source") or "unknown").lower()
            rtk_mode = str(metrics.get("rtk_mode") or "unknown").lower()
            if gps_filter != "all" and gps_mode != gps_filter:
                continue
            label = build_label(algo, per, gps_mode, gps_source, timestamp, metrics)
            candidates.append(RunCase(
                algo=algo,
                per=per,
                gps_mode=gps_mode,
                gps_source=gps_source,
                rtk_mode=rtk_mode,
                result_dir=result_dir,
                csv_path=csv_path,
                metrics_path=metrics_path,
                timestamp=timestamp,
                label=label,
                color=color_for_key("{}:{}:{}:{}".format(algo, per, gps_mode, timestamp)),
            ))
        if all_runs:
            selected.extend(candidates)
        else:
            newest_by_config: Dict[Tuple[str, int, str], RunCase] = {}
            for run in candidates:
                # Prefer timestamped evaluated folders over the per_N latest alias.
                key = (run.algo, run.per, run.gps_mode)
                old = newest_by_config.get(key)
                if old is None or run.timestamp > old.timestamp or old.timestamp == "latest":
                    newest_by_config[key] = run
            selected.extend(newest_by_config.values())
    selected.sort(key=lambda r: (r.algo, r.per, r.gps_mode, r.timestamp))
    return selected


def marker_color(marker: Marker, rgba: Tuple[float, float, float, float]) -> None:
    marker.color.r, marker.color.g, marker.color.b, marker.color.a = rgba


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


def make_line(ns: str, marker_id: int, rows: Sequence[dict], frame_id: str, color, width: float) -> Marker:
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
        p.x, p.y, p.z = row["x"], row["y"], row["z"]
        m.points.append(p)
    return m


def make_sphere(ns: str, marker_id: int, row: dict, frame_id: str, color, scale: float) -> Marker:
    m = Marker()
    m.header.frame_id = frame_id
    m.header.stamp = rospy.Time.now()
    m.ns = ns
    m.id = marker_id
    m.type = Marker.SPHERE
    m.action = Marker.ADD
    m.pose.position.x, m.pose.position.y, m.pose.position.z = row["x"], row["y"], row["z"]
    m.pose.orientation.w = 1.0
    m.scale.x = m.scale.y = m.scale.z = scale
    marker_color(m, color)
    return m


def make_cube(ns: str, marker_id: int, x: float, y: float, z: float, sx: float, sy: float, sz: float, frame_id: str, color) -> Marker:
    m = Marker()
    m.header.frame_id = frame_id
    m.header.stamp = rospy.Time.now()
    m.ns = ns
    m.id = marker_id
    m.type = Marker.CUBE
    m.action = Marker.ADD
    m.pose.position.x, m.pose.position.y, m.pose.position.z = x, y, z
    m.pose.orientation.w = 1.0
    m.scale.x, m.scale.y, m.scale.z = sx, sy, sz
    marker_color(m, color)
    return m


def make_text(ns: str, marker_id: int, x: float, y: float, z: float, text: str, frame_id: str, color, scale: float) -> Marker:
    m = Marker()
    m.header.frame_id = frame_id
    m.header.stamp = rospy.Time.now()
    m.ns = ns
    m.id = marker_id
    m.type = Marker.TEXT_VIEW_FACING
    m.action = Marker.ADD
    m.pose.position.x, m.pose.position.y, m.pose.position.z = x, y, z
    m.pose.orientation.w = 1.0
    m.scale.z = scale
    marker_color(m, color)
    m.text = text
    return m


def bounds(rows_list: Iterable[Sequence[dict]]) -> Tuple[float, float, float]:
    xs, ys, zs = [], [], []
    for rows in rows_list:
        for row in rows:
            xs.append(row["x"])
            ys.append(row["y"])
            zs.append(row["z"])
    if not xs:
        return 0.0, 0.0, 8.0
    return min(xs), max(ys), max(zs) + 10.0


def sanitize_topic_token(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_")


def build_markers(runs: List[RunCase], gt: List[dict], frame_id: str, max_points: int, line_width: float) -> MarkerArray:
    arr = MarkerArray()
    marker_id = 0
    if gt:
        ds = downsample(gt, max_points)
        arr.markers.append(make_line("compare_gt", marker_id, ds, frame_id, GT_COLOR, line_width * 1.45)); marker_id += 1
        arr.markers.append(make_sphere("compare_gt", marker_id, ds[0], frame_id, GT_COLOR, line_width * 8.0)); marker_id += 1
        arr.markers.append(make_text("compare_gt", marker_id, ds[-1]["x"], ds[-1]["y"], ds[-1]["z"] + 4.0, "GT", frame_id, GT_COLOR, 4.0)); marker_id += 1

    loaded_rows = [run.rows or [] for run in runs]
    legend_x, legend_y, legend_z = bounds([gt] + loaded_rows)
    legend_rows = ["GT  ground truth"]

    for idx, run in enumerate(runs, start=1):
        rows = run.rows or []
        if not rows:
            continue
        ds = downsample(rows, max_points)
        ns = "compare_{}_{}_{}".format(run.algo, run.per, sanitize_topic_token(run.gps_mode))
        arr.markers.append(make_line(ns, marker_id, ds, frame_id, run.color, line_width)); marker_id += 1
        arr.markers.append(make_sphere(ns, marker_id, ds[0], frame_id, run.color, line_width * 5.0)); marker_id += 1
        arr.markers.append(make_sphere(ns, marker_id, ds[-1], frame_id, run.color, line_width * 6.5)); marker_id += 1
        arr.markers.append(make_text(ns, marker_id, ds[-1]["x"], ds[-1]["y"], ds[-1]["z"] + 3.0, "{}".format(idx), frame_id, run.color, 3.0)); marker_id += 1
        legend_rows.append("{:02d}  {}".format(idx, run.label))

    row_gap = 4.2
    height = max(8.0, row_gap * (len(legend_rows) + 1))
    width = 78.0
    arr.markers.append(make_cube(
        "compare_legend", marker_id, legend_x + width * 0.5, legend_y + 8.0, legend_z,
        width, 2.0, height, frame_id, (0.0, 0.0, 0.0, 0.55)
    )); marker_id += 1
    arr.markers.append(make_text(
        "compare_legend", marker_id, legend_x, legend_y + 8.5, legend_z + height * 0.5,
        "compare_rviz legend\n" + "\n".join(legend_rows), frame_id, (1.0, 1.0, 1.0, 1.0), 2.8
    )); marker_id += 1
    for idx, run in enumerate(runs, start=1):
        z = legend_z + height * 0.5 - row_gap * (idx + 1)
        arr.markers.append(make_cube("compare_legend_colors", marker_id, legend_x - 4.0, legend_y + 8.7, z, 2.8, 1.2, 2.8, frame_id, run.color)); marker_id += 1
    return arr


def main() -> int:
    parser = argparse.ArgumentParser(description="Open filtered benchmark trajectory comparisons in RViz")
    parser.add_argument("--algo", default="all", help="all, one algorithm, or comma-separated list")
    parser.add_argument("--per", default="", help="optional per filter, e.g. 0, 1-6, or all")
    parser.add_argument("--gps", default="all", choices=["all", "on", "off", "unknown"], help="GPS mode filter")
    parser.add_argument("--all-runs", action="store_true", help="show every timestamped rerun instead of latest per algo/per/GPS")
    parser.add_argument("--results-root", default="/data/results")
    parser.add_argument("--gt", default="/data/UrbanNav_TST_GT_raw.txt")
    parser.add_argument("--frame-id", default="camera_init")
    parser.add_argument("--yaw-offset-deg", type=float, default=float(os.environ.get("GT_YAW_OFFSET_DEG", "0.0")))
    parser.add_argument("--max-points", type=int, default=12000)
    parser.add_argument("--line-width", type=float, default=0.38)
    parser.add_argument("--rate", type=float, default=2.0)
    parser.add_argument("--list", action="store_true", help="list matching runs and exit")
    args = parser.parse_args()

    algos = parse_algos(args.algo)
    pers = parse_pers(args.per)
    runs = discover_runs(args.results_root, algos, pers, args.gps, args.all_runs)

    if args.list:
        for run in runs:
            print("{}\t{}".format(run.label, run.csv_path))
        return 0

    global rospy, Point, PoseStamped, Path, Marker, MarkerArray
    import rospy as _rospy
    from geometry_msgs.msg import Point as _Point, PoseStamped as _PoseStamped
    from nav_msgs.msg import Path as _Path
    from visualization_msgs.msg import Marker as _Marker, MarkerArray as _MarkerArray
    rospy = _rospy
    Point = _Point
    PoseStamped = _PoseStamped
    Path = _Path
    Marker = _Marker
    MarkerArray = _MarkerArray

    rospy.init_node("compare_rviz_paths", anonymous=False)

    for run in runs:
        run.rows = load_csv_trajectory(run.csv_path)
    runs = [run for run in runs if run.rows]
    gt = load_ground_truth(args.gt, args.yaw_offset_deg)

    if not runs and not gt:
        rospy.logerr("Nothing to publish. Check --algo, --per, --gps, --results-root, and --gt.")
        return 2
    if not runs:
        rospy.logwarn("No matching result trajectories were loaded; publishing GT only.")

    gt_path = make_path(downsample(gt, args.max_points), args.frame_id) if gt else None
    run_paths = []
    path_publishers = []
    if gt_path:
        gt_pub = rospy.Publisher("/compare_rviz/ground_truth/path", Path, queue_size=1, latch=True)
        old_gt_pub = rospy.Publisher("/ground_truth_path", Path, queue_size=1, latch=True)
    else:
        gt_pub = old_gt_pub = None

    for idx, run in enumerate(runs, start=1):
        token = sanitize_topic_token("{}_per_{}_gps_{}_{}".format(run.algo, run.per, run.gps_mode, idx))
        topic = "/compare_rviz/{}/path".format(token)
        path_publishers.append((rospy.Publisher(topic, Path, queue_size=1, latch=True), run))
        run_paths.append((run, make_path(downsample(run.rows or [], args.max_points), args.frame_id)))
        rospy.loginfo("Loaded %s from %s", run.label, run.csv_path)

    marker_pub = rospy.Publisher("/compare_rviz/markers", MarkerArray, queue_size=1, latch=True)
    marker_array = build_markers(runs, gt, args.frame_id, args.max_points, args.line_width)
    rospy.loginfo("Publishing %d result trajectories plus GT in RViz", len(runs))

    rate = rospy.Rate(max(0.2, args.rate))
    while not rospy.is_shutdown():
        now = rospy.Time.now()
        if gt_path is not None:
            gt_path.header.stamp = now
            gt_pub.publish(gt_path)
            old_gt_pub.publish(gt_path)
        for (pub, run), (path_run, path) in zip(path_publishers, run_paths):
            path.header.stamp = now
            pub.publish(path)
        for marker in marker_array.markers:
            marker.header.stamp = now
        marker_pub.publish(marker_array)
        rate.sleep()
    return 0


if __name__ == "__main__":
    sys.exit(main())
