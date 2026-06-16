#!/usr/bin/env python3
"""Offline trajectory plotting and robustness analysis for the UrbanNav benchmark.

This script intentionally has no ROS dependency. It reads saved trajectory.csv files from
/data/results or ./data/results and compares them with the UrbanNav GT text file.
"""
import argparse
import csv
import json
import math
import os
import sys
import webbrowser
from bisect import bisect_left
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

WGS84_A = 6378137.0
WGS84_E2 = 6.69437999014e-3

ALGO_CANONICAL = {
    "fastlio2": "fast_lio2",
    "fast_lio2": "fast_lio2",
    "fast-lio2": "fast_lio2",
    "lvisam": "lvi_sam",
    "lvi_sam": "lvi_sam",
    "lvi-sam": "lvi_sam",
    "fastlivo2": "fast_livo2",
    "fast_livo2": "fast_livo2",
    "fast-livo2": "fast_livo2",
    "rtabmap": "rtab_map",
    "rtab_map": "rtab_map",
    "rtab-map": "rtab_map",
    "adaptive-w-lvio": "adaptive_w_lvio",
    "orbslam3": "orb_slam3",
    "orb_slam3": "orb_slam3",
    "orb-slam3": "orb_slam3",
    "orb": "orb_slam3",
    "r3live": "r3live",
    "r3-live": "r3live",
}

DISPLAY_NAMES = {
    "fast_lio2": "FAST-LIO2",
    "lvi_sam": "LVI-SAM",
    "fast_livo2": "FAST-LIVO2",
    "rtab_map": "RTAB-Map",
    "adaptive_w_lvio": "Adaptive-W LVIO",
    "orb_slam3": "ORB-SLAM3",
    "r3live": "R3LIVE",
}

ALL_ALGOS = [
    "fast_lio2",
    "lvi_sam",
    "fast_livo2",
    "rtab_map",
    "adaptive_w_lvio",
    "orb_slam3",
    "r3live",
]

# Existing recorder output IDs are same as canonical keys in this production repo.
RESULT_ID = {key: key for key in ALL_ALGOS}

DATASET_ALIASES = {
    "e2o": "e2o",
    "e20": "e2o",
    "e2o/urban": "e2o",
    "e20/urban": "e2o",
    "one_full_loop": "e2o",
    "e2o_one_full_loop": "e2o",
    "urbannav": "urbannav",
    "urban": "urbannav",
    "urbannav_hk_tst": "urbannav",
    "urbannav_hk_tst_20210517": "urbannav",
}


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))


def abs_from_root(path: str) -> str:
    if not path:
        return path
    if os.path.isabs(path):
        return path
    return os.path.join(repo_root(), path)


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


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


def normalize_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def csv_value(row: dict, *names: str, default=None):
    for name in names:
        if row.get(name) not in (None, ""):
            return row[name]
    return default


def yaw_from_csv_row(row: dict) -> float:
    raw = csv_value(row, "yaw_rad")
    if raw not in (None, ""):
        yaw = float(raw)
        if math.isfinite(yaw):
            return yaw
    qx = float(csv_value(row, "qx", default=0.0) or 0.0)
    qy = float(csv_value(row, "qy", default=0.0) or 0.0)
    qz = float(csv_value(row, "qz", default=0.0) or 0.0)
    qw = float(csv_value(row, "qw", default=1.0) or 1.0)
    return math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))


def load_csv_ground_truth(path: str, yaw_offset_deg: float = 0.0) -> List[dict]:
    path = abs_from_root(path)
    if not os.path.isfile(path):
        return []
    out = []
    rows = []
    yaw_offset_rad = math.radians(yaw_offset_deg)
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        if not ({"timestamp", "pos_x", "pos_y"}.issubset(fields) or {"x_m", "y_m"}.issubset(fields)):
            return []
        for row in reader:
            try:
                stamp_raw = csv_value(row, "timestamp_s", "timestamp")
                rows.append({
                    "stamp": float(stamp_raw) if stamp_raw not in (None, "") else float(row["timestamp_ns"]) * 1.0e-9,
                    "x": float(csv_value(row, "x_m", "pos_x")),
                    "y": float(csv_value(row, "y_m", "pos_y")),
                    "z": float(csv_value(row, "z_m", "pos_z", default=0.0) or 0.0),
                    "yaw": yaw_from_csv_row(row),
                })
            except (KeyError, TypeError, ValueError):
                continue
    rows.sort(key=lambda r: r["stamp"])
    if not rows:
        return []
    ref = rows[0]
    for row in rows:
        x, y = rotate_xy(row["x"] - ref["x"], row["y"] - ref["y"], yaw_offset_rad)
        out.append({
            "stamp": row["stamp"],
            "x": x,
            "y": y,
            "z": row["z"] - ref["z"],
            "yaw": normalize_angle(row["yaw"] - ref["yaw"] + yaw_offset_rad),
        })
    out.sort(key=lambda r: r["stamp"])
    return out


def apply_dataset_defaults(args) -> None:
    dataset = DATASET_ALIASES.get(str(getattr(args, "dataset", "") or "").strip().lower())
    if dataset != "e2o":
        return
    if getattr(args, "gt", "") == "data/UrbanNav_TST_GT_raw.txt":
        args.gt = "data/odometry.csv"
    if getattr(args, "results_root", "") == "data/results":
        args.results_root = "data/results/e2o"


def load_ground_truth(path: str, yaw_offset_deg: float = 0.0) -> List[dict]:
    path = abs_from_root(path)
    if not os.path.isfile(path):
        return []
    if path.lower().endswith(".csv"):
        csv_gt = load_csv_ground_truth(path, yaw_offset_deg)
        if csv_gt:
            return csv_gt
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
        east, north, up = enu_from_ecef_delta(
            ecef[0] - ref_ecef[0],
            ecef[1] - ref_ecef[1],
            ecef[2] - ref_ecef[2],
            ref["lat"],
            ref["lon"],
        )
        x = east * right_e + north * right_n
        y = east * forward_e + north * forward_n
        x, y = rotate_xy(x, y, yaw_offset_rad)
        out.append({
            "stamp": row["stamp"],
            "x": x,
            "y": y,
            "z": up,
            "yaw": normalize_angle(math.radians(row["heading"] - ref["heading"] + yaw_offset_deg)),
        })
    return out


def load_traj(path: str) -> List[dict]:
    path = abs_from_root(path)
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                rows.append({
                    "stamp": float(row["stamp"]),
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                    "z": float(row["z"]),
                    "yaw": float(row.get("yaw", 0.0) or 0.0),
                })
            except (KeyError, TypeError, ValueError):
                continue
    rows.sort(key=lambda r: r["stamp"])
    return rows


def load_yaml_list(path: str, key: str) -> List[dict]:
    if yaml is None:
        return []
    path = abs_from_root(path)
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get(key, []) or []


def parse_algos(value: str, results_root: str, per: Optional[int] = None) -> List[str]:
    value = (value or "all").strip().lower()
    if value in {"all", "*"}:
        if per is None:
            return list(ALL_ALGOS)
        available = []
        for algo in ALL_ALGOS:
            if os.path.isfile(trajectory_path(results_root, algo, per)):
                available.append(algo)
        return available or list(ALL_ALGOS)
    algos = []
    for token in value.replace("/", ",").replace(" ", ",").split(","):
        token = token.strip()
        if not token:
            continue
        key = ALGO_CANONICAL.get(token)
        if not key:
            raise SystemExit(f"Unknown algorithm '{token}'. Use all or one of: {', '.join(DISPLAY_NAMES)}")
        if key not in algos:
            algos.append(key)
    return algos


def parse_pers(value: str) -> List[int]:
    value = (value or "all").strip().lower()
    if value in {"all", "*"}:
        return list(range(7))
    out = []
    for token in value.replace(" ", ",").split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            start = int(a)
            end = int(b)
            step = 1 if end >= start else -1
            out.extend(range(start, end + step, step))
        else:
            out.append(int(token))
    dedup = []
    for p in out:
        if p < 0 or p > 99:
            raise SystemExit(f"Invalid per value: {p}")
        if p not in dedup:
            dedup.append(p)
    return dedup


def trajectory_path(results_root: str, algo: str, per: int, csv_name: str = "trajectory.csv") -> str:
    return os.path.join(abs_from_root(results_root), RESULT_ID[algo], f"per_{per}", csv_name)


def nearest(sample: dict, refs: List[dict], ref_stamps: List[float], max_dt: float) -> Optional[dict]:
    if not refs:
        return None
    i = bisect_left(ref_stamps, sample["stamp"])
    candidates = []
    if i < len(refs):
        candidates.append(refs[i])
    if i > 0:
        candidates.append(refs[i - 1])
    if not candidates:
        return None
    best = min(candidates, key=lambda g: abs(g["stamp"] - sample["stamp"]))
    if abs(best["stamp"] - sample["stamp"]) > max_dt:
        return None
    return best


def percentile(values: List[float], pct: float) -> Optional[float]:
    if not values:
        return None
    vals = sorted(values)
    k = (len(vals) - 1) * pct / 100.0
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return vals[int(k)]
    return vals[f] * (c - k) + vals[c] * (k - f)


def rmse(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return math.sqrt(sum(v * v for v in values) / len(values))


def filter_time(samples: List[dict], start: float, end: float) -> List[dict]:
    return [s for s in samples if start <= s["stamp"] <= end]


def error_rows(samples: List[dict], gt: List[dict], max_dt: float = 0.75) -> List[dict]:
    if not gt:
        return []
    stamps = [g["stamp"] for g in gt]
    out = []
    for s in samples:
        g = nearest(s, gt, stamps, max_dt)
        if g is None:
            continue
        dx = s["x"] - g["x"]
        dy = s["y"] - g["y"]
        dz = s["z"] - g["z"]
        yaw = normalize_angle(s.get("yaw", 0.0) - g.get("yaw", 0.0))
        out.append({
            "stamp": s["stamp"],
            "gt_stamp": g["stamp"],
            "dt_to_gt": s["stamp"] - g["stamp"],
            "x_error_m": dx,
            "y_error_m": dy,
            "z_error_m": dz,
            "yaw_error_rad": yaw,
            "position_error_m": math.sqrt(dx * dx + dy * dy + dz * dz),
        })
    return out


def metrics(samples: List[dict], gt: Optional[List[dict]] = None, max_dt: float = 0.75) -> dict:
    rows = error_rows(samples, gt or [], max_dt) if gt else []
    if rows:
        pos = [r["position_error_m"] for r in rows]
        return {
            "samples": len(rows),
            "position_rmse_m": rmse(pos),
            "position_mean_m": sum(pos) / len(pos),
            "position_median_m": percentile(pos, 50),
            "position_p95_m": percentile(pos, 95),
            "position_max_m": max(pos),
            "x_rmse_m": rmse([r["x_error_m"] for r in rows]),
            "y_rmse_m": rmse([r["y_error_m"] for r in rows]),
            "z_rmse_m": rmse([r["z_error_m"] for r in rows]),
            "yaw_rmse_rad": rmse([r["yaw_error_rad"] for r in rows]),
        }
    return {
        "samples": len(samples),
        "position_rmse_m": None,
        "position_mean_m": None,
        "position_median_m": None,
        "position_p95_m": None,
        "position_max_m": None,
        "x_rmse_m": None,
        "y_rmse_m": None,
        "z_rmse_m": None,
        "yaw_rmse_rad": None,
    }


def jump_events(samples: List[dict], algo: str, per: int, jump_distance: float, jump_speed: float) -> List[dict]:
    events = []
    for prev, cur in zip(samples, samples[1:]):
        dt = cur["stamp"] - prev["stamp"]
        if dt <= 1e-6:
            continue
        dx = cur["x"] - prev["x"]
        dy = cur["y"] - prev["y"]
        dz = cur["z"] - prev["z"]
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        speed = dist / dt
        if dist >= jump_distance or speed >= jump_speed:
            events.append({
                "algo": algo,
                "per": per,
                "stamp": cur["stamp"],
                "dt_s": dt,
                "step_m": dist,
                "speed_mps": speed,
                "x": cur["x"],
                "y": cur["y"],
                "z": cur["z"],
                "reason": "distance" if dist >= jump_distance else "speed",
            })
    return events


def delta_vs_baseline(run: List[dict], baseline: List[dict], max_dt: float = 0.75) -> List[dict]:
    if not run or not baseline:
        return []
    stamps = [b["stamp"] for b in baseline]
    out = []
    for s in run:
        b = nearest(s, baseline, stamps, max_dt)
        if b is None:
            continue
        dx = s["x"] - b["x"]
        dy = s["y"] - b["y"]
        dz = s["z"] - b["z"]
        out.append({
            "stamp": s["stamp"],
            "baseline_stamp": b["stamp"],
            "delta_x_m": dx,
            "delta_y_m": dy,
            "delta_z_m": dz,
            "delta_position_m": math.sqrt(dx * dx + dy * dy + dz * dz),
            "delta_yaw_rad": normalize_angle(s.get("yaw", 0.0) - b.get("yaw", 0.0)),
        })
    return out


def delta_metrics(rows: List[dict]) -> dict:
    if not rows:
        return {
            "delta_samples": 0,
            "delta_rmse_m": None,
            "delta_mean_m": None,
            "delta_p95_m": None,
            "delta_max_m": None,
            "delta_yaw_rmse_rad": None,
        }
    vals = [r["delta_position_m"] for r in rows]
    return {
        "delta_samples": len(rows),
        "delta_rmse_m": rmse(vals),
        "delta_mean_m": sum(vals) / len(vals),
        "delta_p95_m": percentile(vals, 95),
        "delta_max_m": max(vals),
        "delta_yaw_rmse_rad": rmse([r["delta_yaw_rad"] for r in rows]),
    }


def write_csv(path: str, rows: List[dict], fieldnames: Optional[List[str]] = None) -> None:
    ensure_dir(os.path.dirname(path))
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: str, data) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def fmt(value, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def import_matplotlib(show: bool = False):
    import matplotlib
    if not show or not os.environ.get("DISPLAY"):
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def plot_xy(path: str, trajectories: Dict[str, List[dict]], gt: List[dict], title: str) -> Optional[str]:
    if not trajectories and not gt:
        return None
    plt = import_matplotlib(False)
    plt.figure(figsize=(11, 9))
    if gt:
        plt.plot([p["x"] for p in gt], [p["y"] for p in gt], label="GT", linewidth=2.2)
    for algo, samples in trajectories.items():
        if samples:
            plt.plot([p["x"] for p in samples], [p["y"] for p in samples], label=DISPLAY_NAMES.get(algo, algo), linewidth=1.2)
    plt.title(title)
    plt.xlabel("x m")
    plt.ylabel("y m")
    plt.axis("equal")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def plot_3d_static(path: str, trajectories: Dict[str, List[dict]], gt: List[dict], title: str) -> Optional[str]:
    if not trajectories and not gt:
        return None
    plt = import_matplotlib(False)
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection="3d")
    if gt:
        ax.plot([p["x"] for p in gt], [p["y"] for p in gt], [p["z"] for p in gt], label="GT", linewidth=2.0)
    for algo, samples in trajectories.items():
        if samples:
            ax.plot([p["x"] for p in samples], [p["y"] for p in samples], [p["z"] for p in samples], label=DISPLAY_NAMES.get(algo, algo), linewidth=1.1)
    ax.set_title(title)
    ax.set_xlabel("x m")
    ax.set_ylabel("y m")
    ax.set_zlabel("z m")
    ax.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def show_3d_matplotlib(trajectories: Dict[str, List[dict]], gt: List[dict], title: str) -> None:
    if not os.environ.get("DISPLAY"):
        print("No DISPLAY found; not opening a GUI plot. Saved static plot instead.")
        return
    plt = import_matplotlib(True)
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")
    if gt:
        ax.plot([p["x"] for p in gt], [p["y"] for p in gt], [p["z"] for p in gt], label="GT", linewidth=2.2)
    for algo, samples in trajectories.items():
        if samples:
            ax.plot([p["x"] for p in samples], [p["y"] for p in samples], [p["z"] for p in samples], label=DISPLAY_NAMES.get(algo, algo), linewidth=1.2)
    ax.set_title(title)
    ax.set_xlabel("x m")
    ax.set_ylabel("y m")
    ax.set_zlabel("z m")
    ax.legend()
    plt.show()


def plot_bars(path: str, rows: List[dict], key: str, title: str, ylabel: str) -> Optional[str]:
    rows = [r for r in rows if r.get(key) is not None]
    if not rows:
        return None
    plt = import_matplotlib(False)
    labels = [r.get("label") or r.get("algo") or r.get("case") for r in rows]
    values = [r.get(key) or 0.0 for r in rows]
    plt.figure(figsize=(max(10, len(rows) * 1.1), 6))
    plt.bar(range(len(rows)), values)
    plt.xticks(range(len(rows)), labels, rotation=30, ha="right")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, axis="y")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def plot_error_time(path: str, error_by_algo: Dict[str, List[dict]], title: str) -> Optional[str]:
    if not any(error_by_algo.values()):
        return None
    t0 = min(rows[0]["stamp"] for rows in error_by_algo.values() if rows)
    plt = import_matplotlib(False)
    plt.figure(figsize=(12, 7))
    for algo, rows in error_by_algo.items():
        if rows:
            plt.plot([r["stamp"] - t0 for r in rows], [r["position_error_m"] for r in rows], label=DISPLAY_NAMES.get(algo, algo), linewidth=1.1)
    plt.xlabel("seconds from first compared sample")
    plt.ylabel("position error m")
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def plot_multi_paths(path: str, per_trajs: Dict[int, List[dict]], gt: List[dict], title: str) -> Optional[str]:
    if not per_trajs and not gt:
        return None
    plt = import_matplotlib(False)
    plt.figure(figsize=(11, 9))
    if gt:
        plt.plot([p["x"] for p in gt], [p["y"] for p in gt], label="GT", linewidth=2.0)
    for per, samples in sorted(per_trajs.items()):
        if samples:
            plt.plot([p["x"] for p in samples], [p["y"] for p in samples], label=f"per_{per}", linewidth=1.1)
    plt.title(title)
    plt.xlabel("x m")
    plt.ylabel("y m")
    plt.axis("equal")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def default_out_dir(*parts: str) -> str:
    return os.path.join(repo_root(), "data", "analysis", *parts)


def load_runs(results_root: str, algos: List[str], per: int, csv_name: str) -> Tuple[Dict[str, List[dict]], List[str]]:
    data = {}
    missing = []
    for algo in algos:
        path = trajectory_path(results_root, algo, per, csv_name)
        traj = load_traj(path)
        if traj:
            data[algo] = traj
        else:
            missing.append(path)
    return data, missing


def algo_summary_rows(trajs: Dict[str, List[dict]], gt: List[dict], per: int, jump_distance: float, jump_speed: float, max_dt: float) -> Tuple[List[dict], List[dict], Dict[str, List[dict]]]:
    rows = []
    jumps = []
    errors = {}
    for algo, samples in trajs.items():
        m = metrics(samples, gt, max_dt)
        algo_jumps = jump_events(samples, algo, per, jump_distance, jump_speed)
        jumps.extend(algo_jumps)
        errors[algo] = error_rows(samples, gt, max_dt) if gt else []
        rows.append({
            "algo": algo,
            "label": DISPLAY_NAMES.get(algo, algo),
            "per": per,
            "trajectory_samples": len(samples),
            "samples_compared_to_gt": m.get("samples"),
            "position_rmse_m": m.get("position_rmse_m"),
            "position_mean_m": m.get("position_mean_m"),
            "position_median_m": m.get("position_median_m"),
            "position_p95_m": m.get("position_p95_m"),
            "position_max_m": m.get("position_max_m"),
            "x_rmse_m": m.get("x_rmse_m"),
            "y_rmse_m": m.get("y_rmse_m"),
            "z_rmse_m": m.get("z_rmse_m"),
            "yaw_rmse_rad": m.get("yaw_rmse_rad"),
            "sudden_change_count": len(algo_jumps),
            "max_step_m": max([j["step_m"] for j in algo_jumps], default=0.0),
            "max_step_speed_mps": max([j["speed_mps"] for j in algo_jumps], default=0.0),
        })
    rows.sort(key=lambda r: (float("inf") if r.get("position_rmse_m") is None else r["position_rmse_m"]))
    return rows, jumps, errors


def segment_rows(trajs: Dict[str, List[dict]], gt: List[dict], segments: List[dict], per: int, jump_distance: float, jump_speed: float, max_dt: float) -> Tuple[List[dict], List[dict]]:
    rows = []
    type_accum = defaultdict(list)
    for idx, seg in enumerate(segments, start=1):
        try:
            start = float(seg["start"])
            end = float(seg["end"])
        except Exception:
            continue
        name = seg.get("name", f"segment_{idx}")
        typ = seg.get("type", "unknown")
        per_seg_rows = []
        for algo, samples in trajs.items():
            subset = filter_time(samples, start, end)
            m = metrics(subset, gt, max_dt)
            j = jump_events(subset, algo, per, jump_distance, jump_speed)
            row = {
                "segment_index": idx,
                "segment_name": name,
                "segment_type": typ,
                "start": start,
                "end": end,
                "algo": algo,
                "label": DISPLAY_NAMES.get(algo, algo),
                "samples": m.get("samples"),
                "position_rmse_m": m.get("position_rmse_m"),
                "position_max_m": m.get("position_max_m"),
                "position_p95_m": m.get("position_p95_m"),
                "yaw_rmse_rad": m.get("yaw_rmse_rad"),
                "sudden_change_count": len(j),
            }
            rows.append(row)
            per_seg_rows.append(row)
            type_accum[(typ, algo)].append(row)
        valid = [r for r in per_seg_rows if r.get("position_rmse_m") is not None]
        worst = max(valid, key=lambda r: r["position_rmse_m"], default=None)
        for row in per_seg_rows:
            row["worst_in_segment"] = bool(worst and row["algo"] == worst["algo"])
    type_rows = []
    for (typ, algo), vals in type_accum.items():
        vals = [v for v in vals if v.get("position_rmse_m") is not None]
        if not vals:
            continue
        type_rows.append({
            "segment_type": typ,
            "algo": algo,
            "label": DISPLAY_NAMES.get(algo, algo),
            "segments_count": len(vals),
            "avg_position_rmse_m": sum(v["position_rmse_m"] for v in vals) / len(vals),
            "max_position_rmse_m": max(v["position_max_m"] or 0.0 for v in vals),
            "total_sudden_change_count": sum(v["sudden_change_count"] for v in vals),
        })
    # mark worst by type
    for typ in sorted({r["segment_type"] for r in type_rows}):
        candidates = [r for r in type_rows if r["segment_type"] == typ]
        worst = max(candidates, key=lambda r: r["avg_position_rmse_m"], default=None)
        for r in candidates:
            r["worst_for_segment_type"] = bool(worst and r["algo"] == worst["algo"])
    return rows, type_rows


def perturbation_rows(trajs: Dict[str, List[dict]], gt: List[dict], per_yaml: str, per: int, jump_distance: float, jump_speed: float, max_dt: float) -> List[dict]:
    perturbations = load_yaml_list(per_yaml, "perturbations")
    rows = []
    for idx, item in enumerate(perturbations, start=1):
        try:
            start = float(item["start"])
            end = float(item["end"])
        except Exception:
            continue
        name = item.get("name", f"perturbation_{idx}")
        ptype = item.get("type", "unknown")
        sensor = item.get("sensor", "unknown")
        window_rows = []
        for algo, samples in trajs.items():
            subset = filter_time(samples, start, end)
            m = metrics(subset, gt, max_dt)
            j = jump_events(subset, algo, per, jump_distance, jump_speed)
            row = {
                "perturbation_index": idx,
                "perturbation_name": name,
                "sensor": sensor,
                "perturbation_type": ptype,
                "start": start,
                "end": end,
                "algo": algo,
                "label": DISPLAY_NAMES.get(algo, algo),
                "samples": m.get("samples"),
                "position_rmse_m": m.get("position_rmse_m"),
                "position_max_m": m.get("position_max_m"),
                "position_p95_m": m.get("position_p95_m"),
                "yaw_rmse_rad": m.get("yaw_rmse_rad"),
                "sudden_change_count": len(j),
            }
            rows.append(row)
            window_rows.append(row)
        valid = [r for r in window_rows if r.get("position_rmse_m") is not None]
        worst = max(valid, key=lambda r: r["position_rmse_m"], default=None)
        for row in window_rows:
            row["worst_in_perturbation_window"] = bool(worst and row["algo"] == worst["algo"])
    return rows


def write_report(path: str, per: int, algo_rows: List[dict], segment_rows_: List[dict], type_rows: List[dict], perturb_rows: List[dict], jump_rows: List[dict], missing: List[str]) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"Trajectory comparison report: per_{per}\n")
        handle.write("=" * 42 + "\n\n")
        if missing:
            handle.write("Missing trajectory CSVs:\n")
            for p in missing:
                handle.write(f"- {p}\n")
            handle.write("\n")
        handle.write("Overall ranking by position RMSE, lower is better:\n")
        for idx, row in enumerate(algo_rows, start=1):
            handle.write(
                f"{idx}. {row['label']} rmse={fmt(row.get('position_rmse_m'))} m "
                f"p95={fmt(row.get('position_p95_m'))} m max={fmt(row.get('position_max_m'))} m "
                f"jumps={row.get('sudden_change_count', 0)} samples={row.get('samples_compared_to_gt', 0)}\n"
            )
        handle.write("\nWorst by road segment type:\n")
        for typ in sorted({r["segment_type"] for r in type_rows}):
            candidates = [r for r in type_rows if r["segment_type"] == typ and r.get("worst_for_segment_type")]
            if candidates:
                r = candidates[0]
                handle.write(f"- {typ}: {r['label']} avg_rmse={fmt(r.get('avg_position_rmse_m'))} m jumps={r.get('total_sudden_change_count', 0)}\n")
        handle.write("\nWorst specific road windows:\n")
        for row in segment_rows_:
            if row.get("worst_in_segment"):
                handle.write(
                    f"- {row['segment_index']:02d} {row['segment_name']} ({row['segment_type']}): "
                    f"{row['label']} rmse={fmt(row.get('position_rmse_m'))} m max={fmt(row.get('position_max_m'))} m\n"
                )
        if perturb_rows:
            handle.write("\nWorst perturbation windows:\n")
            for row in perturb_rows:
                if row.get("worst_in_perturbation_window"):
                    handle.write(
                        f"- {row['perturbation_name']} [{row['sensor']}:{row['perturbation_type']}]: "
                        f"{row['label']} rmse={fmt(row.get('position_rmse_m'))} m max={fmt(row.get('position_max_m'))} m\n"
                    )
        handle.write(f"\nSudden change events: {len(jump_rows)}\n")
        worst_jumps = sorted(jump_rows, key=lambda r: r.get("step_m", 0.0), reverse=True)[:15]
        for row in worst_jumps:
            handle.write(
                f"- {DISPLAY_NAMES.get(row['algo'], row['algo'])} t={row['stamp']:.3f} "
                f"step={row['step_m']:.3f} m speed={row['speed_mps']:.3f} m/s reason={row['reason']}\n"
            )


def command_plot3d(args) -> int:
    algos = parse_algos(args.algo, args.results_root, args.per)
    trajs, missing = load_runs(args.results_root, algos, args.per, args.csv_name)
    gt = load_ground_truth(args.gt, args.gt_yaw_offset_deg) if args.gt else []
    out_dir = abs_from_root(args.out_dir or default_out_dir(f"per_{args.per}", "plot3d"))
    ensure_dir(out_dir)
    static_png = plot_3d_static(os.path.join(out_dir, "trajectory_3d.png"), trajs, gt, f"Trajectory 3D comparison per_{args.per}")
    xy_png = plot_xy(os.path.join(out_dir, "trajectory_xy.png"), trajs, gt, f"Trajectory XY comparison per_{args.per}")
    if not trajs and not gt:
        print("No trajectory CSVs and no GT were found. Nothing to plot.", file=sys.stderr)
        if missing:
            print("Missing CSVs:", file=sys.stderr)
            for m in missing:
                print(f"  {m}", file=sys.stderr)
        return 1
    print(f"Loaded algorithms: {', '.join(DISPLAY_NAMES.get(a, a) for a in trajs)}")
    if missing:
        print("Missing CSVs:")
        for m in missing:
            print(f"  {m}")
    if static_png:
        print(f"Saved: {static_png}")
    if xy_png:
        print(f"Saved: {xy_png}")
    if args.show:
        show_3d_matplotlib(trajs, gt, f"Trajectory 3D comparison per_{args.per}")
    return 0


def command_compare(args) -> int:
    algos = parse_algos(args.algo, args.results_root, args.per)
    trajs, missing = load_runs(args.results_root, algos, args.per, args.csv_name)
    gt = load_ground_truth(args.gt, args.gt_yaw_offset_deg)
    if not gt:
        print(f"ERROR: GT not found or empty: {abs_from_root(args.gt)}", file=sys.stderr)
        return 2
    out_dir = abs_from_root(args.out_dir or default_out_dir(f"per_{args.per}", "all_algos"))
    ensure_dir(out_dir)

    algo_rows, jump_rows, error_by_algo = algo_summary_rows(trajs, gt, args.per, args.jump_distance, args.jump_speed, args.max_dt)
    segments = load_yaml_list(args.segments, "segments")
    segment_cmp, type_cmp = segment_rows(trajs, gt, segments, args.per, args.jump_distance, args.jump_speed, args.max_dt)
    per_yaml = args.perturbations or os.path.join("wrappers/localization_benchmark/config/perturbations", f"per_{args.per}.yaml")
    perturb_cmp = perturbation_rows(trajs, gt, per_yaml, args.per, args.jump_distance, args.jump_speed, args.max_dt)

    write_csv(os.path.join(out_dir, "summary.csv"), algo_rows)
    write_csv(os.path.join(out_dir, "jump_events.csv"), jump_rows)
    write_csv(os.path.join(out_dir, "segment_comparison.csv"), segment_cmp)
    write_csv(os.path.join(out_dir, "segment_type_comparison.csv"), type_cmp)
    write_csv(os.path.join(out_dir, "perturbation_window_comparison.csv"), perturb_cmp)
    write_json(os.path.join(out_dir, "comparison_report.json"), {
        "per": args.per,
        "algorithms": list(trajs.keys()),
        "missing_csvs": missing,
        "summary": algo_rows,
        "segment_comparison": segment_cmp,
        "segment_type_comparison": type_cmp,
        "perturbation_window_comparison": perturb_cmp,
        "jump_events": jump_rows,
    })
    write_report(os.path.join(out_dir, "comparison_report.txt"), args.per, algo_rows, segment_cmp, type_cmp, perturb_cmp, jump_rows, missing)

    plot_xy(os.path.join(out_dir, "trajectory_xy_gt_algos.png"), trajs, gt, f"GT vs algorithms per_{args.per}")
    plot_3d_static(os.path.join(out_dir, "trajectory_3d_gt_algos.png"), trajs, gt, f"GT vs algorithms per_{args.per}")
    plot_error_time(os.path.join(out_dir, "position_error_over_time.png"), error_by_algo, f"Position error vs GT per_{args.per}")
    plot_bars(os.path.join(out_dir, "position_rmse_bar.png"), algo_rows, "position_rmse_m", f"Position RMSE per_{args.per}", "RMSE m")
    plot_bars(os.path.join(out_dir, "position_max_error_bar.png"), algo_rows, "position_max_m", f"Max position error per_{args.per}", "max error m")
    plot_bars(os.path.join(out_dir, "sudden_change_count_bar.png"), algo_rows, "sudden_change_count", f"Sudden changes per_{args.per}", "count")

    print(f"Saved comparison analysis to: {out_dir}")
    print(os.path.join(out_dir, "comparison_report.txt"))
    return 0


def command_per_compare(args) -> int:
    algos = parse_algos(args.algo, args.results_root, None)
    pers = parse_pers(args.per)
    gt = load_ground_truth(args.gt, args.gt_yaw_offset_deg)
    if not gt:
        print(f"WARNING: GT not found or empty: {abs_from_root(args.gt)}. GT metrics will be blank.")
    all_out_root = abs_from_root(args.out_dir or default_out_dir("per_compare"))
    ensure_dir(all_out_root)
    overall_index = []

    for algo in algos:
        per_trajs = {}
        missing = []
        for per in pers:
            path = trajectory_path(args.results_root, algo, per, args.csv_name)
            traj = load_traj(path)
            if traj:
                per_trajs[per] = traj
            else:
                missing.append(path)
        if not per_trajs:
            print(f"No trajectories found for {algo}")
            continue
        out_dir = ensure_dir(os.path.join(all_out_root, algo))
        baseline = per_trajs.get(0)
        summary = []
        delta_summary = []
        perturb_effects = []
        all_jumps = []
        errors_by_per = {}
        for per, samples in sorted(per_trajs.items()):
            m = metrics(samples, gt, args.max_dt) if gt else metrics(samples, [], args.max_dt)
            j = jump_events(samples, algo, per, args.jump_distance, args.jump_speed)
            all_jumps.extend(j)
            errors_by_per[f"per_{per}"] = error_rows(samples, gt, args.max_dt) if gt else []
            row = {
                "algo": algo,
                "label": DISPLAY_NAMES.get(algo, algo),
                "per": per,
                "trajectory_samples": len(samples),
                "samples_compared_to_gt": m.get("samples"),
                "position_rmse_m": m.get("position_rmse_m"),
                "position_mean_m": m.get("position_mean_m"),
                "position_p95_m": m.get("position_p95_m"),
                "position_max_m": m.get("position_max_m"),
                "yaw_rmse_rad": m.get("yaw_rmse_rad"),
                "sudden_change_count": len(j),
            }
            summary.append(row)
            if baseline and per != 0:
                drows = delta_vs_baseline(samples, baseline, args.max_dt)
                dm = delta_metrics(drows)
                dm.update({"algo": algo, "label": DISPLAY_NAMES.get(algo, algo), "per": per})
                delta_summary.append(dm)
                per_yaml = os.path.join("wrappers/localization_benchmark/config/perturbations", f"per_{per}.yaml")
                for idx, item in enumerate(load_yaml_list(per_yaml, "perturbations"), start=1):
                    try:
                        start = float(item["start"])
                        end = float(item["end"])
                    except Exception:
                        continue
                    win_rows = [r for r in drows if start <= r["stamp"] <= end]
                    wdm = delta_metrics(win_rows)
                    wdm.update({
                        "algo": algo,
                        "label": DISPLAY_NAMES.get(algo, algo),
                        "per": per,
                        "perturbation_index": idx,
                        "perturbation_name": item.get("name", f"perturbation_{idx}"),
                        "sensor": item.get("sensor", "unknown"),
                        "perturbation_type": item.get("type", "unknown"),
                        "start": start,
                        "end": end,
                    })
                    perturb_effects.append(wdm)
        write_csv(os.path.join(out_dir, "per_summary.csv"), summary)
        write_csv(os.path.join(out_dir, "per_delta_vs_per0.csv"), delta_summary)
        write_csv(os.path.join(out_dir, "perturbation_effects_vs_per0.csv"), perturb_effects)
        write_csv(os.path.join(out_dir, "jump_events.csv"), all_jumps)
        write_json(os.path.join(out_dir, "per_compare.json"), {
            "algo": algo,
            "pers": sorted(per_trajs.keys()),
            "missing_csvs": missing,
            "summary": summary,
            "delta_vs_per0": delta_summary,
            "perturbation_effects_vs_per0": perturb_effects,
            "jump_events": all_jumps,
        })
        write_per_report(os.path.join(out_dir, "per_compare_report.txt"), algo, summary, delta_summary, perturb_effects, all_jumps, missing)
        plot_multi_paths(os.path.join(out_dir, "per_xy_paths.png"), per_trajs, gt, f"{DISPLAY_NAMES.get(algo, algo)} per comparison")
        plot_bars(os.path.join(out_dir, "rmse_by_per.png"), [{**r, "label": f"per_{r['per']}"} for r in summary], "position_rmse_m", f"{DISPLAY_NAMES.get(algo, algo)} RMSE by perturbation", "RMSE m")
        plot_bars(os.path.join(out_dir, "max_error_by_per.png"), [{**r, "label": f"per_{r['per']}"} for r in summary], "position_max_m", f"{DISPLAY_NAMES.get(algo, algo)} max error by perturbation", "max error m")
        plot_bars(os.path.join(out_dir, "jump_count_by_per.png"), [{**r, "label": f"per_{r['per']}"} for r in summary], "sudden_change_count", f"{DISPLAY_NAMES.get(algo, algo)} sudden changes by perturbation", "count")
        plot_bars(os.path.join(out_dir, "delta_vs_per0_by_per.png"), [{**r, "label": f"per_{r['per']}"} for r in delta_summary], "delta_rmse_m", f"{DISPLAY_NAMES.get(algo, algo)} trajectory change vs per_0", "delta RMSE m")
        # Reuse error time plot helper with synthetic keys.
        plot_error_time(os.path.join(out_dir, "error_over_time_by_per.png"), {k: v for k, v in errors_by_per.items()}, f"{DISPLAY_NAMES.get(algo, algo)} error vs GT by perturbation")
        best = min([r for r in summary if r.get("position_rmse_m") is not None], key=lambda r: r["position_rmse_m"], default=None)
        worst = max([r for r in summary if r.get("position_rmse_m") is not None], key=lambda r: r["position_rmse_m"], default=None)
        overall_index.append({
            "algo": algo,
            "label": DISPLAY_NAMES.get(algo, algo),
            "found_pers": " ".join(str(p) for p in sorted(per_trajs)),
            "best_per": best.get("per") if best else None,
            "best_rmse_m": best.get("position_rmse_m") if best else None,
            "worst_per": worst.get("per") if worst else None,
            "worst_rmse_m": worst.get("position_rmse_m") if worst else None,
            "analysis_dir": out_dir,
        })
        print(f"Saved per comparison for {DISPLAY_NAMES.get(algo, algo)}: {out_dir}")
    write_csv(os.path.join(all_out_root, "per_compare_index.csv"), overall_index)
    return 0


def write_per_report(path: str, algo: str, summary: List[dict], delta_summary: List[dict], perturb_effects: List[dict], jumps: List[dict], missing: List[str]) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as handle:
        label = DISPLAY_NAMES.get(algo, algo)
        handle.write(f"Perturbation comparison report: {label}\n")
        handle.write("=" * (32 + len(label)) + "\n\n")
        if missing:
            handle.write("Missing trajectory CSVs:\n")
            for p in missing:
                handle.write(f"- {p}\n")
            handle.write("\n")
        handle.write("Runs ranked by GT RMSE, lower is better:\n")
        valid = sorted([r for r in summary if r.get("position_rmse_m") is not None], key=lambda r: r["position_rmse_m"])
        for r in valid:
            handle.write(
                f"- per_{r['per']}: rmse={fmt(r.get('position_rmse_m'))} m "
                f"p95={fmt(r.get('position_p95_m'))} m max={fmt(r.get('position_max_m'))} m jumps={r.get('sudden_change_count', 0)}\n"
            )
        if delta_summary:
            handle.write("\nChange from clean per_0 baseline:\n")
            for r in sorted(delta_summary, key=lambda x: x.get("delta_rmse_m") or -1.0, reverse=True):
                handle.write(
                    f"- per_{r['per']}: delta_rmse={fmt(r.get('delta_rmse_m'))} m "
                    f"delta_p95={fmt(r.get('delta_p95_m'))} m delta_max={fmt(r.get('delta_max_m'))} m samples={r.get('delta_samples', 0)}\n"
                )
        if perturb_effects:
            handle.write("\nPerturbation-window effect vs per_0:\n")
            for r in sorted(perturb_effects, key=lambda x: x.get("delta_rmse_m") or -1.0, reverse=True):
                handle.write(
                    f"- per_{r['per']} {r['perturbation_name']} [{r['sensor']}:{r['perturbation_type']}]: "
                    f"delta_rmse={fmt(r.get('delta_rmse_m'))} m delta_max={fmt(r.get('delta_max_m'))} m samples={r.get('delta_samples', 0)}\n"
                )
        handle.write(f"\nSudden change events: {len(jumps)}\n")
        for row in sorted(jumps, key=lambda r: r.get("step_m", 0.0), reverse=True)[:20]:
            handle.write(f"- per_{row['per']} t={row['stamp']:.3f} step={row['step_m']:.3f} m speed={row['speed_mps']:.3f} m/s\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="UrbanNav offline trajectory plot/analysis tools")
    sub = parser.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dataset", default=os.environ.get("DATASET", ""), help="Dataset defaults: urbannav or e2o")
    common.add_argument("--results-root", default="data/results", help="Root containing <algo>/per_N/trajectory.csv")
    common.add_argument("--gt", default="data/UrbanNav_TST_GT_raw.txt", help="UrbanNav GT text file")
    common.add_argument("--gt-yaw-offset-deg", type=float, default=float(os.environ.get("GT_YAW_OFFSET_DEG", "0.0")))
    common.add_argument("--csv-name", default="trajectory.csv", help="CSV filename inside each result folder")
    common.add_argument("--out-dir", default="")

    p = sub.add_parser("plot3d", parents=[common], help="Open/save GT + algorithm 3D trajectory plot")
    p.add_argument("--per", type=int, required=True)
    p.add_argument("--algo", default="all", help="all or comma-separated algo names")
    p.add_argument("--show", dest="show", action="store_true", default=True, help="Open a GUI 3D plot when DISPLAY is available")
    p.add_argument("--no-show", dest="show", action="store_false", help="Only save plots; do not open GUI")
    p.set_defaults(func=command_plot3d)

    c = sub.add_parser("compare", parents=[common], help="Save cross-algorithm GT comparison plots/reports for one per")
    c.add_argument("--per", type=int, required=True)
    c.add_argument("--algo", default="all")
    c.add_argument("--segments", default="wrappers/localization_benchmark/config/road_segments.yaml")
    c.add_argument("--perturbations", default="")
    c.add_argument("--max-dt", type=float, default=0.75)
    c.add_argument("--jump-distance", type=float, default=5.0, help="Consecutive pose step threshold in meters")
    c.add_argument("--jump-speed", type=float, default=35.0, help="Consecutive pose speed threshold in m/s")
    c.set_defaults(func=command_compare)

    pc = sub.add_parser("per_compare", parents=[common], help="Compare different perturbation runs of the same algorithm")
    pc.add_argument("--algo", default="all")
    pc.add_argument("--per", default="all", help="all, 1-6, or comma list like 0,2,4")
    pc.add_argument("--max-dt", type=float, default=0.75)
    pc.add_argument("--jump-distance", type=float, default=5.0)
    pc.add_argument("--jump-speed", type=float, default=35.0)
    pc.set_defaults(func=command_per_compare)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    apply_dataset_defaults(args)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
