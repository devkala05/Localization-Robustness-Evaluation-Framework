#!/usr/bin/env python3
"""Publish latest saved benchmark trajectories into RViz.

Canonical result layout:
  /data/results/<dataset>/<algo>/<with_gps|without_gps>/per_<0..6>/<YYYY-MM-DD_HH-MM-SS>/trajectory.csv

For every requested dataset/algo/gps/per combination this script picks only the
latest timestamp folder, so repeated runs never create duplicate plots in RViz.
"""
import argparse
import csv
import math
import os
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import rospy
from geometry_msgs.msg import Point, PoseStamped
from nav_msgs.msg import Path
from visualization_msgs.msg import Marker, MarkerArray

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

WGS84_A = 6378137.0
WGS84_E2 = 6.69437999014e-3

ALGO_CANONICAL = {
    "fastlio2": "fast_lio2", "fast_lio2": "fast_lio2", "fast-lio2": "fast_lio2",
    "lvisam": "lvi_sam", "lvi_sam": "lvi_sam", "lvi-sam": "lvi_sam",
    "fastlivo2": "fast_livo2", "fast_livo2": "fast_livo2", "fast-livo2": "fast_livo2",
    "rtabmap": "rtab_map", "rtab_map": "rtab_map", "rtab-map": "rtab_map",
    "adaptive": "adaptive_w_lvio", "adaptive_w_lvio": "adaptive_w_lvio", "adaptive-w-lvio": "adaptive_w_lvio",
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
ALL_DATASETS = ["e2o", "urbannav"]
ALL_GPS = ["without_gps", "with_gps"]
GPS_ALIASES = {
    "off": "without_gps", "false": "without_gps", "0": "without_gps", "no": "without_gps", "without": "without_gps", "without_gps": "without_gps", "gps_off": "without_gps",
    "on": "with_gps", "true": "with_gps", "1": "with_gps", "yes": "with_gps", "with": "with_gps", "with_gps": "with_gps", "gps_on": "with_gps",
}
BASE_COLORS = {
    "fast_lio2": (1.00, 0.72, 0.10, 1.0),
    "lvi_sam": (0.20, 0.55, 1.00, 1.0),
    "fast_livo2": (1.00, 0.20, 0.20, 1.0),
    "rtab_map": (0.75, 0.35, 1.00, 1.0),
    "adaptive_w_lvio": (0.10, 0.90, 1.00, 1.0),
    "orb_slam3": (1.00, 0.40, 0.85, 1.0),
    "r3live": (0.80, 1.00, 0.10, 1.0),
}
GT_COLORS = {
    "e2o": (0.10, 1.00, 0.25, 1.0),
    "urbannav": (0.15, 0.90, 1.00, 1.0),
}


@dataclass(frozen=True)
class RunSelection:
    dataset: str
    algo: str
    gps: str
    per: int
    stamp: str
    csv_path: str

    @property
    def label(self) -> str:
        gps_label = "GPS" if self.gps == "with_gps" else "noGPS"
        return f"{self.dataset} {DISPLAY_NAMES.get(self.algo, self.algo)} {gps_label} per_{self.per}"

    @property
    def topic_key(self) -> str:
        return f"{self.dataset}/{self.algo}/{self.gps}/per_{self.per}"


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))


def resolve_path(path: str) -> str:
    if not path:
        return path
    if os.path.isabs(path):
        return path
    cwd_path = os.path.abspath(path)
    if os.path.exists(cwd_path):
        return cwd_path
    return os.path.join(repo_root(), path)


def split_tokens(value: str) -> List[str]:
    return [x.strip() for x in (value or "all").replace("/", ",").replace(" ", ",").split(",") if x.strip()]


def parse_datasets(value: str) -> List[str]:
    value = (value or "all").strip().lower()
    if value in {"all", "*"}:
        return list(ALL_DATASETS)
    out: List[str] = []
    aliases = {"e20": "e2o", "urban": "urbannav"}
    for token in split_tokens(value):
        key = aliases.get(token.lower(), token.lower())
        if key not in ALL_DATASETS:
            raise SystemExit(f"Unknown dataset '{token}'. Use all, e2o, or urbannav.")
        if key not in out:
            out.append(key)
    return out


def parse_algos(value: str) -> List[str]:
    value = (value or "all").strip().lower()
    if value in {"all", "*"}:
        return list(ALL_ALGOS)
    out: List[str] = []
    for token in split_tokens(value):
        key = ALGO_CANONICAL.get(token.lower())
        if key is None:
            raise SystemExit("Unknown algorithm '{}'. Use all or one of: {}".format(token, ", ".join(ALL_ALGOS)))
        if key not in out:
            out.append(key)
    return out


def parse_gps(value: str) -> List[str]:
    value = (value or "all").strip().lower()
    if value in {"all", "*"}:
        return list(ALL_GPS)
    out: List[str] = []
    for token in split_tokens(value):
        key = GPS_ALIASES.get(token.lower())
        if key is None:
            raise SystemExit("Unknown GPS filter '{}'. Use all, on, off, with_gps, or without_gps.".format(token))
        if key not in out:
            out.append(key)
    return out


def parse_pers(value: str) -> List[int]:
    value = (value or "all").strip().lower()
    if value in {"all", "*"}:
        return list(range(7))
    out: List[int] = []
    for token in split_tokens(value):
        token = token.lower().replace("per_", "")
        if not token.isdigit() or not (0 <= int(token) <= 6):
            raise SystemExit("Unknown perturbation '{}'. Use all or 0..6.".format(token))
        p = int(token)
        if p not in out:
            out.append(p)
    return out


def latest_run_dir(per_dir: str) -> Optional[str]:
    if not os.path.isdir(per_dir):
        return None
    candidates = []
    for name in os.listdir(per_dir):
        full = os.path.join(per_dir, name)
        if os.path.isdir(full) and os.path.isfile(os.path.join(full, "trajectory.csv")):
            candidates.append(full)
    if not candidates:
        return None
    # Timestamp names are lexicographically sortable: YYYY-MM-DD_HH-MM-SS.
    candidates.sort(key=lambda p: (os.path.basename(p), os.path.getmtime(p)))
    return candidates[-1]


def discover_runs(results_root: str, datasets: Sequence[str], algos: Sequence[str], gps_modes: Sequence[str], pers: Sequence[int]) -> Tuple[List[RunSelection], List[str]]:
    root = resolve_path(results_root)
    selected: List[RunSelection] = []
    missing: List[str] = []
    for dataset in datasets:
        for algo in algos:
            for gps in gps_modes:
                for per in pers:
                    per_dir = os.path.join(root, dataset, algo, gps, f"per_{per}")
                    latest = latest_run_dir(per_dir)
                    if latest:
                        selected.append(RunSelection(dataset, algo, gps, per, os.path.basename(latest), os.path.join(latest, "trajectory.csv")))
                    else:
                        missing.append(os.path.join(per_dir, "<timestamp>", "trajectory.csv"))
    selected.sort(key=lambda r: (r.dataset, r.algo, r.gps, r.per))
    return selected, missing


def dms_to_deg(degrees: float, minutes: float, seconds: float) -> float:
    sign = -1.0 if degrees < 0 else 1.0
    return sign * (abs(degrees) + minutes / 60.0 + seconds / 3600.0)


def ecef_from_lla(lat_deg: float, lon_deg: float, height: float) -> Tuple[float, float, float]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    normal = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    return ((normal + height) * cos_lat * math.cos(lon), (normal + height) * cos_lat * math.sin(lon), (normal * (1.0 - WGS84_E2) + height) * sin_lat)


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


def load_csv_trajectory(path: str) -> List[dict]:
    path = resolve_path(path)
    if not os.path.isfile(path):
        return []
    rows: List[dict] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                rows.append({
                    "stamp": float(row.get("stamp", len(rows)) or len(rows)),
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


def load_ground_truth(path: str, yaw_offset_deg: float = 0.0) -> List[dict]:
    path = resolve_path(path)
    if not os.path.isfile(path):
        return []
    if path.lower().endswith(".csv"):
        out: List[dict] = []
        yaw_offset_rad = math.radians(yaw_offset_deg)
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames and "x_m" in reader.fieldnames:
                for row in reader:
                    try:
                        yaw = float(row.get("yaw_rad", "nan"))
                        if not math.isfinite(yaw):
                            yaw = 0.0
                        yaw += yaw_offset_rad
                        x, y = rotate_xy(float(row["x_m"]), float(row["y_m"]), yaw_offset_rad)
                        out.append({"stamp": float(row.get("stamp", len(out)) or len(out)), "x": x, "y": y, "z": float(row.get("z_m", 0.0) or 0.0), "qx": 0.0, "qy": 0.0, "qz": math.sin(0.5 * yaw), "qw": math.cos(0.5 * yaw)})
                    except (KeyError, TypeError, ValueError):
                        continue
            elif reader.fieldnames and {"stamp", "x", "y"}.issubset(set(reader.fieldnames)):
                for row in reader:
                    try:
                        x, y = rotate_xy(float(row["x"]), float(row["y"]), yaw_offset_rad)
                        out.append({"stamp": float(row.get("stamp", len(out)) or len(out)), "x": x, "y": y, "z": float(row.get("z", 0.0) or 0.0), "qx": float(row.get("qx", 0.0) or 0.0), "qy": float(row.get("qy", 0.0) or 0.0), "qz": float(row.get("qz", 0.0) or 0.0), "qw": float(row.get("qw", 1.0) or 1.0)})
                    except (KeyError, TypeError, ValueError):
                        continue
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
    forward_e = math.sin(heading)
    forward_n = math.cos(heading)
    right_e = math.cos(heading)
    right_n = -math.sin(heading)
    yaw_offset_rad = math.radians(yaw_offset_deg)
    out = []
    for row in raw:
        ecef = ecef_from_lla(row["lat"], row["lon"], row["h"])
        east, north, up = enu_from_ecef_delta(ecef[0] - ref_ecef[0], ecef[1] - ref_ecef[1], ecef[2] - ref_ecef[2], ref["lat"], ref["lon"])
        x = east * right_e + north * right_n
        y = east * forward_e + north * forward_n
        x, y = rotate_xy(x, y, yaw_offset_rad)
        out.append({"stamp": row["stamp"], "x": x, "y": y, "z": up, "qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0})
    return out


def load_dataset_gt(dataset_config_dir: str, dataset: str, override: str = "") -> Tuple[str, float]:
    if override:
        return override, 0.0
    cfg_path = os.path.join(resolve_path(dataset_config_dir), f"{dataset}.yaml")
    if yaml is None or not os.path.isfile(cfg_path):
        defaults = {
            "e2o": "/workspace/data/gt_one_full_loop_fastlivo2_lidar103.csv",
            "urbannav": "/data/UrbanNav_TST_GT_raw.txt",
        }
        return defaults.get(dataset, ""), 0.0
    with open(cfg_path, "r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle) or {}
    d = cfg.get("dataset") or {}
    return d.get("ground_truth_path", ""), float(d.get("gt_yaw_offset_deg", 0.0) or 0.0)


def downsample(rows: Sequence[dict], max_points: int) -> List[dict]:
    if max_points <= 0 or len(rows) <= max_points:
        return list(rows)
    step = max(1, int(math.ceil(float(len(rows)) / float(max_points))))
    out = list(rows[::step])
    if rows and rows[-1] is not out[-1]:
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
    marker.color.r, marker.color.g, marker.color.b, marker.color.a = rgba


def vary_color(base: Tuple[float, float, float, float], dataset: str, gps: str, per: int) -> Tuple[float, float, float, float]:
    r, g, b, a = base
    # Small deterministic brightness variation so gps/per variants remain visible.
    factor = 0.72 + 0.04 * (per % 7)
    if gps == "with_gps":
        factor += 0.14
    if dataset == "e2o":
        factor += 0.05
    return (min(1.0, r * factor), min(1.0, g * factor), min(1.0, b * factor), a)


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
        p.x, p.y, p.z = row["x"], row["y"], row["z"]
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
    m.pose.position.x, m.pose.position.y, m.pose.position.z = row["x"], row["y"], row["z"]
    m.pose.orientation.w = 1.0
    m.scale.x = m.scale.y = m.scale.z = scale
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
    m.pose.position.x, m.pose.position.y, m.pose.position.z = row["x"], row["y"], row["z"] + dz
    m.pose.orientation.w = 1.0
    m.scale.z = scale
    marker_color(m, color)
    m.text = text
    return m


def build_marker_array(run_rows: Dict[RunSelection, List[dict]], gt_rows: Dict[str, List[dict]], frame_id: str, width: float, max_points: int) -> MarkerArray:
    arr = MarkerArray()
    marker_id = 0
    legend_lines = []
    legend_origin = {"x": 0.0, "y": 0.0, "z": 8.0}

    for dataset, rows in gt_rows.items():
        if not rows:
            continue
        ds = downsample(rows, max_points)
        color = GT_COLORS.get(dataset, (0.10, 1.00, 0.25, 1.0))
        arr.markers.append(make_line_marker(f"offline_gt_{dataset}", marker_id, ds, frame_id, color, width * 1.45)); marker_id += 1
        arr.markers.append(make_sphere(f"offline_gt_{dataset}", marker_id, ds[0], frame_id, color, width * 8.0)); marker_id += 1
        arr.markers.append(make_text(f"offline_gt_{dataset}", marker_id, ds[-1], f"GT {dataset}", frame_id, color, 3.8)); marker_id += 1
        if legend_origin["x"] == 0.0 and legend_origin["y"] == 0.0:
            legend_origin = {"x": ds[0]["x"], "y": ds[0]["y"], "z": ds[0]["z"] + 10.0}

    for run, rows in run_rows.items():
        if not rows:
            continue
        ds = downsample(rows, max_points)
        color = vary_color(BASE_COLORS.get(run.algo, (1.0, 1.0, 1.0, 1.0)), run.dataset, run.gps, run.per)
        ns = "offline_" + run.topic_key.replace("/", "_")
        arr.markers.append(make_line_marker(ns, marker_id, ds, frame_id, color, width)); marker_id += 1
        arr.markers.append(make_sphere(ns, marker_id, ds[0], frame_id, color, width * 4.5)); marker_id += 1
        arr.markers.append(make_sphere(ns, marker_id, ds[-1], frame_id, color, width * 6.0)); marker_id += 1
        if len(run_rows) <= 35:
            arr.markers.append(make_text(ns, marker_id, ds[-1], run.label, frame_id, color, 2.7)); marker_id += 1
        legend_lines.append(run.label)

    if legend_lines:
        max_show = 30
        shown = legend_lines[:max_show]
        more = len(legend_lines) - len(shown)
        text = "Latest trajectory plots only\n" + "\n".join(shown)
        if more > 0:
            text += f"\n... +{more} more"
        arr.markers.append(make_text("offline_legend", marker_id, legend_origin, text, frame_id, (1.0, 1.0, 1.0, 1.0), 3.0, dz=0.0)); marker_id += 1
    return arr


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish latest saved benchmark trajectories into RViz")
    parser.add_argument("--results-root", default="/data/results", help="Root containing analysis/, e2o/, urbannav/")
    parser.add_argument("--dataset", default="all", help="all, e2o, urbannav")
    parser.add_argument("--algo", default="all", help="all or comma-separated names")
    parser.add_argument("--per", default="all", help="all, 0..6, or comma-separated")
    parser.add_argument("--gps", default="all", help="all, on/off, with_gps/without_gps")
    parser.add_argument("--dataset-config-dir", default="/workspace/wrappers/localization_benchmark/config/datasets")
    parser.add_argument("--gt-e2o", default="", help="Override E2O GT path")
    parser.add_argument("--gt-urbannav", default="", help="Override UrbanNav GT path")
    parser.add_argument("--frame-id", default="camera_init")
    parser.add_argument("--rate", type=float, default=2.0)
    parser.add_argument("--max-points", type=int, default=12000)
    parser.add_argument("--line-width", type=float, default=0.35)
    parser.add_argument("--print-selected", action="store_true")
    args = parser.parse_args()

    datasets = parse_datasets(args.dataset)
    algos = parse_algos(args.algo)
    gps_modes = parse_gps(args.gps)
    pers = parse_pers(args.per)
    runs, missing = discover_runs(args.results_root, datasets, algos, gps_modes, pers)

    rospy.init_node("offline_trajectory_rviz", anonymous=False)
    if not runs:
        rospy.logerr("No trajectory.csv files found for requested filters under %s", resolve_path(args.results_root))
        for m in missing[:30]:
            rospy.logwarn("missing: %s", m)
        return 2

    run_rows: Dict[RunSelection, List[dict]] = {}
    for run in runs:
        rows = load_csv_trajectory(run.csv_path)
        if not rows:
            rospy.logwarn("Empty trajectory: %s", run.csv_path)
            continue
        run_rows[run] = rows
        rospy.loginfo("Selected latest %s -> %s", run.label, run.csv_path)
        if args.print_selected:
            print(f"{run.label}: {run.csv_path}")

    gt_rows: Dict[str, List[dict]] = {}
    for dataset in datasets:
        override = args.gt_e2o if dataset == "e2o" else args.gt_urbannav if dataset == "urbannav" else ""
        gt_path, yaw = load_dataset_gt(args.dataset_config_dir, dataset, override)
        gt = load_ground_truth(gt_path, yaw)
        if gt:
            gt_rows[dataset] = gt
            rospy.loginfo("Loaded GT %s: %d poses from %s", dataset, len(gt), gt_path)
        else:
            rospy.logwarn("No GT loaded for %s from %s", dataset, gt_path)

    if not run_rows and not gt_rows:
        rospy.logerr("Nothing to publish after loading CSV/GT files.")
        return 2

    path_publishers: Dict[str, rospy.Publisher] = {}
    for dataset in gt_rows:
        topic = f"/offline/gt/{dataset}/path"
        path_publishers[f"gt/{dataset}"] = rospy.Publisher(topic, Path, queue_size=1, latch=True)
    if gt_rows:
        path_publishers["ground_truth_path"] = rospy.Publisher("/ground_truth_path", Path, queue_size=1, latch=True)
    for run in run_rows:
        path_publishers[run.topic_key] = rospy.Publisher("/offline/{}/path".format(run.topic_key), Path, queue_size=1, latch=True)
    marker_pub = rospy.Publisher("/offline/trajectory_markers", MarkerArray, queue_size=1, latch=True)

    gt_paths = {dataset: make_path(downsample(rows, args.max_points), args.frame_id) for dataset, rows in gt_rows.items()}
    run_paths = {run: make_path(downsample(rows, args.max_points), args.frame_id) for run, rows in run_rows.items()}
    marker_array = build_marker_array(run_rows, gt_rows, args.frame_id, args.line_width, args.max_points)

    rospy.loginfo("Publishing %d latest run(s). Missing combinations: %d", len(run_rows), len(missing))
    rate = rospy.Rate(max(0.2, args.rate))
    while not rospy.is_shutdown():
        now = rospy.Time.now()
        first_gt = True
        for dataset, path in gt_paths.items():
            path.header.stamp = now
            path_publishers[f"gt/{dataset}"].publish(path)
            if first_gt and "ground_truth_path" in path_publishers:
                path_publishers["ground_truth_path"].publish(path)
                first_gt = False
        for run, path in run_paths.items():
            path.header.stamp = now
            path_publishers[run.topic_key].publish(path)
        for marker in marker_array.markers:
            marker.header.stamp = now
        marker_pub.publish(marker_array)
        rate.sleep()
    return 0


if __name__ == "__main__":
    sys.exit(main())
