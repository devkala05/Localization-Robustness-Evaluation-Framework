#!/usr/bin/env python3
"""Evaluate one localization run and write all run-local artifacts.

Output files are written inside the timestamped result directory that already
contains trajectory.csv.  The evaluator intentionally keeps all analysis local
so data/results/analysis can stay reserved for plot.sh/RViz helper files only.
"""
import argparse
import csv
import json
import math
import os
from bisect import bisect_left
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import yaml


WGS84_A = 6378137.0
WGS84_E2 = 6.69437999014e-3
MAX_MATCH_DT_SEC = 0.75
CLOSE_COMPONENT_RATIO = 0.90


# ----------------------------- geometry / loading -----------------------------
def dms_to_deg(degrees, minutes, seconds):
    sign = -1.0 if degrees < 0 else 1.0
    return sign * (abs(degrees) + minutes / 60.0 + seconds / 3600.0)


def ecef_from_lla(lat_deg, lon_deg, height):
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


def enu_from_ecef_delta(dx, dy, dz, ref_lat_deg, ref_lon_deg):
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


def rotate_xy(x, y, yaw_offset_rad):
    c = math.cos(yaw_offset_rad)
    s = math.sin(yaw_offset_rad)
    return c * x - s * y, s * x + c * y


def normalize_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def angle_diff(a, b):
    return normalize_angle(a - b)


def load_csv_ground_truth(path, yaw_offset_deg=0.0):
    rows = []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "x_m" not in reader.fieldnames:
            return []
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
    yaw_offset_rad = math.radians(yaw_offset_deg)
    ref = rows[0]
    out = []
    for row in rows:
        x, y = rotate_xy(row["x"] - ref["x"], row["y"] - ref["y"], yaw_offset_rad)
        out.append({
            "stamp": row["stamp"],
            "x": x,
            "y": y,
            "z": row["z"] - ref["z"],
            "yaw": normalize_angle(row["yaw"] - ref["yaw"] + yaw_offset_rad),
        })
    return out


def load_ground_truth(path, yaw_offset_deg=0.0):
    if path and path.lower().endswith(".csv"):
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
                pass
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


def load_trajectory(path):
    out = []
    if not path or not os.path.isfile(path):
        return out
    with open(path, "r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            try:
                out.append({
                    "stamp": float(row["stamp"]),
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                    "z": float(row["z"]),
                    "yaw": float(row["yaw"]),
                })
            except (KeyError, TypeError, ValueError):
                continue
    out.sort(key=lambda r: r["stamp"])
    return out


def nearest(sample, gt, gt_stamps):
    i = bisect_left(gt_stamps, sample["stamp"])
    candidates = []
    if i < len(gt):
        candidates.append(gt[i])
    if i > 0:
        candidates.append(gt[i - 1])
    if not candidates:
        return None
    return min(candidates, key=lambda g: abs(g["stamp"] - sample["stamp"]))


# ----------------------------- metrics / reports -----------------------------
def rmse(values):
    values = [v for v in values if v is not None and math.isfinite(v)]
    if not values:
        return None
    return math.sqrt(sum(v * v for v in values) / len(values))


def mean_abs(values):
    values = [abs(v) for v in values if v is not None and math.isfinite(v)]
    if not values:
        return None
    return sum(values) / len(values)


def max_abs(values):
    values = [abs(v) for v in values if v is not None and math.isfinite(v)]
    if not values:
        return None
    return max(values)


def matched_error_rows(samples, gt, max_dt=MAX_MATCH_DT_SEC):
    gt_stamps = [g["stamp"] for g in gt]
    rows = []
    for sample in samples:
        ref = nearest(sample, gt, gt_stamps)
        if ref is None:
            continue
        dt = sample["stamp"] - ref["stamp"]
        if abs(dt) > max_dt:
            continue
        dx = sample["x"] - ref["x"]
        dy = sample["y"] - ref["y"]
        dz = sample["z"] - ref["z"]
        yaw = angle_diff(sample["yaw"], ref["yaw"])
        rows.append({
            "stamp": sample["stamp"],
            "time_from_start_s": 0.0,
            "gt_stamp": ref["stamp"],
            "match_dt_s": dt,
            "output_x_m": sample["x"],
            "output_y_m": sample["y"],
            "output_z_m": sample["z"],
            "output_yaw_rad": sample["yaw"],
            "gt_x_m": ref["x"],
            "gt_y_m": ref["y"],
            "gt_z_m": ref["z"],
            "gt_yaw_rad": ref["yaw"],
            "x_error_m": dx,
            "y_error_m": dy,
            "z_error_m": dz,
            "yaw_error_rad": yaw,
            "yaw_error_deg": math.degrees(yaw),
            "position_error_m": math.sqrt(dx * dx + dy * dy + dz * dz),
        })
    if rows:
        t0 = rows[0]["stamp"]
        for row in rows:
            row["time_from_start_s"] = row["stamp"] - t0
    return rows


def _relative_rows(rows):
    if not rows:
        return []
    first = rows[0]
    x0 = first["x_error_m"]
    y0 = first["y_error_m"]
    z0 = first["z_error_m"]
    yaw0 = first["yaw_error_rad"]
    out = []
    for row in rows:
        x = row["x_error_m"] - x0
        y = row["y_error_m"] - y0
        z = row["z_error_m"] - z0
        yaw = angle_diff(row["yaw_error_rad"], yaw0)
        copy = dict(row)
        copy.update({
            "x_error_m": x,
            "y_error_m": y,
            "z_error_m": z,
            "yaw_error_rad": yaw,
            "yaw_error_deg": math.degrees(yaw),
            "position_error_m": math.sqrt(x * x + y * y + z * z),
        })
        out.append(copy)
    return out


def dominant_components(metrics):
    # Dominance uses display units: metres for xyz and degrees for yaw.  This is
    # intentionally human-oriented because the report answers "which component"
    # dominated each scene, not a mathematically unitless normalized score.
    values = {
        "x": metrics.get("x_rmse_m"),
        "y": metrics.get("y_rmse_m"),
        "z": metrics.get("z_rmse_m"),
        "yaw": metrics.get("yaw_rmse_deg"),
    }
    valid = {k: float(v) for k, v in values.items() if v is not None and math.isfinite(float(v))}
    if not valid:
        return []
    highest = max(valid.values())
    if highest <= 0.0:
        return [max(valid, key=valid.get)]
    return [k for k, v in sorted(valid.items(), key=lambda item: item[1], reverse=True) if v >= highest * CLOSE_COMPONENT_RATIO]


def metrics_from_errors(rows):
    if not rows:
        return {
            "samples": 0,
            "x_rmse_m": None,
            "y_rmse_m": None,
            "z_rmse_m": None,
            "yaw_rmse_rad": None,
            "yaw_rmse_deg": None,
            "position_rmse_m": None,
            "position_max_m": None,
            "dominant_components": [],
            "worst_component": None,
        }
    metrics = {
        "samples": len(rows),
        "x_rmse_m": rmse([r["x_error_m"] for r in rows]),
        "y_rmse_m": rmse([r["y_error_m"] for r in rows]),
        "z_rmse_m": rmse([r["z_error_m"] for r in rows]),
        "yaw_rmse_rad": rmse([r["yaw_error_rad"] for r in rows]),
        "yaw_rmse_deg": rmse([r["yaw_error_deg"] for r in rows]),
        "position_rmse_m": rmse([r["position_error_m"] for r in rows]),
        "position_max_m": max([r["position_error_m"] for r in rows]),
        "x_mae_m": mean_abs([r["x_error_m"] for r in rows]),
        "y_mae_m": mean_abs([r["y_error_m"] for r in rows]),
        "z_mae_m": mean_abs([r["z_error_m"] for r in rows]),
        "yaw_mae_deg": mean_abs([r["yaw_error_deg"] for r in rows]),
        "x_max_abs_m": max_abs([r["x_error_m"] for r in rows]),
        "y_max_abs_m": max_abs([r["y_error_m"] for r in rows]),
        "z_max_abs_m": max_abs([r["z_error_m"] for r in rows]),
        "yaw_max_abs_deg": max_abs([r["yaw_error_deg"] for r in rows]),
    }
    metrics["dominant_components"] = dominant_components(metrics)
    metrics["worst_component"] = metrics["dominant_components"][0] if metrics["dominant_components"] else None
    return metrics


def metrics_for_samples(samples, gt):
    return metrics_from_errors(matched_error_rows(samples, gt))


def robustness_score(metrics):
    if not metrics:
        return None
    pos = metrics.get("position_rmse_m")
    yaw = metrics.get("yaw_rmse_rad")
    if pos is None and yaw is None:
        return None
    return float(pos or 0.0) + 10.0 * float(yaw or 0.0)


def filter_error_rows(rows, start, end):
    return [r for r in rows if start <= r["stamp"] <= end]


def load_yaml_list(path, key):
    if not path or not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get(key, []) or []


def safe_name(value):
    text = str(value).strip().lower().replace(" ", "_")
    return "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in text).strip("_") or "unnamed"


def format_metric(value, suffix=""):
    if value is None:
        return "n/a"
    return f"{float(value):.4f}{suffix}"


def format_time(value):
    if value is None:
        return "n/a"
    return f"{float(value):.6f}"


def ranked_by_position(reports, metric_key="relative_metrics"):
    rows = []
    for key, item in reports.items():
        metrics = item.get(metric_key) or item.get("metrics") or {}
        value = metrics.get("position_rmse_m")
        if value is not None:
            rows.append((key, item, value))
    return sorted(rows, key=lambda item: item[2], reverse=True)


# ----------------------------- writing artifacts -----------------------------
def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_error_csv(out_dir, rows):
    fieldnames = [
        "stamp", "time_from_start_s", "gt_stamp", "match_dt_s",
        "output_x_m", "output_y_m", "output_z_m", "output_yaw_rad",
        "gt_x_m", "gt_y_m", "gt_z_m", "gt_yaw_rad",
        "x_error_m", "y_error_m", "z_error_m", "yaw_error_rad", "yaw_error_deg", "position_error_m",
    ]
    return write_csv(os.path.join(out_dir, "error_timeseries.csv"), fieldnames, rows)


def component_rows(reports, metric_key="relative_metrics"):
    rows = []
    for key, report in reports.items():
        metrics = report.get(metric_key) or report.get("metrics") or {}
        abs_metrics = report.get("absolute_metrics") or {}
        if metrics.get("samples", 0) <= 0:
            rows.append({
                "key": key,
                "label": report.get("label", key),
                "type": report.get("type", "unknown"),
                "start": report.get("start"),
                "end": report.get("end"),
                "samples": 0,
                "dominant_components": "",
            })
            continue
        rows.append({
            "key": key,
            "label": report.get("label", key),
            "type": report.get("type", "unknown"),
            "sensor": report.get("sensor", ""),
            "perturbation_type": report.get("perturbation_type", ""),
            "start": report.get("start"),
            "end": report.get("end"),
            "samples": metrics.get("samples", 0),
            "relative_position_rmse_m": metrics.get("position_rmse_m"),
            "relative_position_max_m": metrics.get("position_max_m"),
            "relative_x_rmse_m": metrics.get("x_rmse_m"),
            "relative_y_rmse_m": metrics.get("y_rmse_m"),
            "relative_z_rmse_m": metrics.get("z_rmse_m"),
            "relative_yaw_rmse_deg": metrics.get("yaw_rmse_deg"),
            "dominant_components": ",".join(metrics.get("dominant_components") or []),
            "absolute_position_rmse_m": abs_metrics.get("position_rmse_m"),
            "absolute_x_rmse_m": abs_metrics.get("x_rmse_m"),
            "absolute_y_rmse_m": abs_metrics.get("y_rmse_m"),
            "absolute_z_rmse_m": abs_metrics.get("z_rmse_m"),
            "absolute_yaw_rmse_deg": abs_metrics.get("yaw_rmse_deg"),
        })
    return rows


def write_window_csv(out_dir, filename, rows):
    fieldnames = [
        "key", "label", "type", "sensor", "perturbation_type", "start", "end", "samples",
        "relative_position_rmse_m", "relative_position_max_m",
        "relative_x_rmse_m", "relative_y_rmse_m", "relative_z_rmse_m", "relative_yaw_rmse_deg",
        "dominant_components",
        "absolute_position_rmse_m", "absolute_x_rmse_m", "absolute_y_rmse_m", "absolute_z_rmse_m", "absolute_yaw_rmse_deg",
    ]
    return write_csv(os.path.join(out_dir, filename), fieldnames, rows)


def get_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except Exception:
        return None


def write_trajectory_plot(out_dir, gt, run, baseline):
    plt = get_matplotlib()
    if plt is None or not run:
        return None
    path = os.path.join(out_dir, "trajectory_xy.png")
    plt.figure(figsize=(9, 7))
    if gt:
        plt.plot([s["x"] for s in gt], [s["y"] for s in gt], label="ground truth", linewidth=1.5)
    if baseline:
        plt.plot([s["x"] for s in baseline], [s["y"] for s in baseline], label="baseline", linewidth=1.0)
    plt.plot([s["x"] for s in run], [s["y"] for s in run], label="algorithm output", linewidth=1.2)
    plt.axis("equal")
    plt.grid(True)
    plt.xlabel("x m")
    plt.ylabel("y m")
    plt.title("Trajectory XY")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def write_error_plot(out_dir, rows):
    plt = get_matplotlib()
    if plt is None or not rows:
        return None
    path = os.path.join(out_dir, "error_over_time.png")
    times = [r["time_from_start_s"] for r in rows]
    plt.figure(figsize=(11, 7))
    plt.plot(times, [r["x_error_m"] for r in rows], label="x error m", linewidth=1.0)
    plt.plot(times, [r["y_error_m"] for r in rows], label="y error m", linewidth=1.0)
    plt.plot(times, [r["z_error_m"] for r in rows], label="z error m", linewidth=1.0)
    plt.plot(times, [r["position_error_m"] for r in rows], label="position error m", linewidth=1.2)
    plt.xlabel("seconds from first matched output")
    plt.ylabel("error")
    plt.title("Error over time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def write_yaw_error_plot(out_dir, rows):
    plt = get_matplotlib()
    if plt is None or not rows:
        return None
    path = os.path.join(out_dir, "yaw_error_over_time.png")
    times = [r["time_from_start_s"] for r in rows]
    plt.figure(figsize=(11, 5))
    plt.plot(times, [r["yaw_error_deg"] for r in rows], label="yaw error deg", linewidth=1.1)
    plt.xlabel("seconds from first matched output")
    plt.ylabel("yaw error deg")
    plt.title("Yaw error over time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def write_segment_position_bar(out_dir, segment_reports):
    plt = get_matplotlib()
    if plt is None:
        return None
    items = [(k, v) for k, v in segment_reports.items() if (v.get("relative_metrics") or {}).get("samples", 0) > 0]
    if not items:
        return None
    path = os.path.join(out_dir, "segment_position_rmse_bar.png")
    labels = [v.get("name", k) for k, v in items]
    values = [(v.get("relative_metrics") or {}).get("position_rmse_m") or 0.0 for _, v in items]
    x = list(range(len(items)))
    plt.figure(figsize=(max(10, len(items) * 0.75), 6))
    plt.bar(x, values, label="segment-relative position RMSE m")
    plt.xticks(x, labels, rotation=35, ha="right")
    plt.ylabel("RMSE m")
    plt.title("Segment-local drift / relative position error")
    plt.grid(True, axis="y")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def write_segment_component_bar(out_dir, segment_reports):
    plt = get_matplotlib()
    if plt is None:
        return None
    items = [(k, v) for k, v in segment_reports.items() if (v.get("relative_metrics") or {}).get("samples", 0) > 0]
    if not items:
        return None
    path = os.path.join(out_dir, "segment_component_rmse_bar.png")
    labels = [v.get("name", k) for k, v in items]
    x = list(range(len(items)))
    width = 0.22
    x_values = [(v.get("relative_metrics") or {}).get("x_rmse_m") or 0.0 for _, v in items]
    y_values = [(v.get("relative_metrics") or {}).get("y_rmse_m") or 0.0 for _, v in items]
    z_values = [(v.get("relative_metrics") or {}).get("z_rmse_m") or 0.0 for _, v in items]
    plt.figure(figsize=(max(11, len(items) * 0.9), 6))
    plt.bar([i - width for i in x], x_values, width=width, label="x RMSE m")
    plt.bar(x, y_values, width=width, label="y RMSE m")
    plt.bar([i + width for i in x], z_values, width=width, label="z RMSE m")
    plt.xticks(x, labels, rotation=35, ha="right")
    plt.ylabel("RMSE m")
    plt.title("Segment-local component RMSE")
    plt.grid(True, axis="y")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def write_perturbation_bar(out_dir, reports):
    plt = get_matplotlib()
    if plt is None:
        return None
    items = [(k, v) for k, v in reports.items() if (v.get("relative_metrics") or {}).get("samples", 0) > 0]
    if not items:
        return None
    path = os.path.join(out_dir, "perturbation_window_rmse_bar.png")
    labels = [v.get("name", k) for k, v in items]
    values = [(v.get("relative_metrics") or {}).get("position_rmse_m") or 0.0 for _, v in items]
    x = list(range(len(items)))
    plt.figure(figsize=(max(10, len(items) * 0.8), 6))
    plt.bar(x, values, label="window-relative position RMSE m")
    plt.xticks(x, labels, rotation=35, ha="right")
    plt.ylabel("RMSE m")
    plt.title("Perturbation-window relative error")
    plt.grid(True, axis="y")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def write_segment_error_csvs(out_dir, segment_reports):
    seg_dir = os.path.join(out_dir, "segment_error_timeseries")
    os.makedirs(seg_dir, exist_ok=True)
    written = []
    fieldnames = [
        "stamp", "time_from_start_s", "x_error_m", "y_error_m", "z_error_m",
        "yaw_error_rad", "yaw_error_deg", "position_error_m",
        "relative_x_error_m", "relative_y_error_m", "relative_z_error_m",
        "relative_yaw_error_rad", "relative_yaw_error_deg", "relative_position_error_m",
    ]
    for key, report in segment_reports.items():
        rows = report.get("error_rows") or []
        rel_rows = report.get("relative_error_rows") or []
        if not rows:
            continue
        combined = []
        for row, rel in zip(rows, rel_rows):
            combined.append({
                "stamp": row["stamp"],
                "time_from_start_s": row["stamp"] - rows[0]["stamp"],
                "x_error_m": row["x_error_m"],
                "y_error_m": row["y_error_m"],
                "z_error_m": row["z_error_m"],
                "yaw_error_rad": row["yaw_error_rad"],
                "yaw_error_deg": row["yaw_error_deg"],
                "position_error_m": row["position_error_m"],
                "relative_x_error_m": rel["x_error_m"],
                "relative_y_error_m": rel["y_error_m"],
                "relative_z_error_m": rel["z_error_m"],
                "relative_yaw_error_rad": rel["yaw_error_rad"],
                "relative_yaw_error_deg": rel["yaw_error_deg"],
                "relative_position_error_m": rel["position_error_m"],
            })
        path = os.path.join(seg_dir, f"{safe_name(key)}.csv")
        write_csv(path, fieldnames, combined)
        written.append(path)
    return written


def metric_summary_line(metrics):
    dominant = ", ".join(metrics.get("dominant_components") or []) or "n/a"
    return (
        f"pos={format_metric(metrics.get('position_rmse_m'), ' m')}, "
        f"x={format_metric(metrics.get('x_rmse_m'), ' m')}, "
        f"y={format_metric(metrics.get('y_rmse_m'), ' m')}, "
        f"z={format_metric(metrics.get('z_rmse_m'), ' m')}, "
        f"yaw={format_metric(metrics.get('yaw_rmse_deg'), ' deg')}, "
        f"dominant={dominant}, samples={metrics.get('samples', 0)}"
    )


def report_markdown(report, generated_files):
    overall = report.get("overall") or {}
    lines = []
    lines.append("# Localization Run Analysis")
    lines.append("")
    if report.get("algorithm_note"):
        lines.append(f"**Algorithm note:** {report['algorithm_note']}")
        lines.append("")
    lines.append("## Run summary")
    lines.append("")
    lines.append(f"- GPS mode: `{report.get('gps_mode', 'off')}`")
    lines.append(f"- GPS source: `{report.get('gps_source', 'none')}`")
    lines.append(f"- RTK mode: `{report.get('rtk_mode', 'auto')}`")
    lines.append(f"- Samples compared: **{overall.get('samples', 0)}**")
    lines.append(f"- Robustness score, lower is better: **{format_metric(report.get('robustness_score_lower_is_better'))}**")
    lines.append(f"- Overall position RMSE: **{format_metric(overall.get('position_rmse_m'), ' m')}**")
    lines.append(f"- Overall max position error: **{format_metric(overall.get('position_max_m'), ' m')}**")
    lines.append(f"- Overall dominant component(s): **{', '.join(overall.get('dominant_components') or []) or 'n/a'}**")
    lines.append("")
    lines.append("## Time ranges")
    lines.append("")
    rr = report.get("run_time_range") or {}
    gr = report.get("ground_truth_time_range") or {}
    lines.append(f"- Run CSV: `{format_time(rr.get('start'))}` → `{format_time(rr.get('end'))}`")
    lines.append(f"- Ground truth: `{format_time(gr.get('start'))}` → `{format_time(gr.get('end'))}`")
    lines.append("")
    lines.append("> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.")
    lines.append("")
    lines.append("## Segment-wise analysis")
    lines.append("")
    lines.append("| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |")
    lines.append("|---:|---|---|---|---|---|")
    for idx, (key, segment) in enumerate(report.get("segments", {}).items(), start=1):
        rel = segment.get("relative_metrics") or {}
        abs_m = segment.get("absolute_metrics") or {}
        lines.append(
            f"| {idx} | {segment.get('name', key)} | {segment.get('type', 'unknown')} | "
            f"{format_time(segment.get('start'))} → {format_time(segment.get('end'))} | "
            f"{metric_summary_line(rel)} | {metric_summary_line(abs_m)} |"
        )
    ranked = ranked_by_position(report.get("segments", {}), "relative_metrics")
    lines.append("")
    if ranked:
        _, top_segment, _ = ranked[0]
        top = top_segment.get("relative_metrics") or {}
        lines.append(
            f"**Most affected segment:** `{top_segment.get('name', 'n/a')}` "
            f"with relative position RMSE {format_metric(top.get('position_rmse_m'), ' m')} "
            f"and dominant component(s): {', '.join(top.get('dominant_components') or []) or 'n/a'}."
        )
    else:
        lines.append("**Most affected segment:** n/a, no segment overlapped the trajectory timestamps.")
    lines.append("")
    lines.append("## Perturbation-window analysis")
    lines.append("")
    windows = report.get("perturbation_windows", {})
    if windows:
        lines.append("| # | Window | Sensor/type | Time window | Relative RMSE summary |")
        lines.append("|---:|---|---|---|---|")
        for idx, (key, window) in enumerate(windows.items(), start=1):
            rel = window.get("relative_metrics") or {}
            lines.append(
                f"| {idx} | {window.get('name', key)} | {window.get('sensor', 'unknown')}/{window.get('perturbation_type', 'unknown')} | "
                f"{format_time(window.get('start'))} → {format_time(window.get('end'))} | {metric_summary_line(rel)} |"
            )
        ranked_windows = ranked_by_position(windows, "relative_metrics")
        lines.append("")
        if ranked_windows:
            _, top_window, _ = ranked_windows[0]
            top = top_window.get("relative_metrics") or {}
            lines.append(
                f"**Most affected perturbation window:** `{top_window.get('name', 'n/a')}` "
                f"with relative position RMSE {format_metric(top.get('position_rmse_m'), ' m')} "
                f"and dominant component(s): {', '.join(top.get('dominant_components') or []) or 'n/a'}."
            )
    else:
        lines.append("No perturbation windows configured for this case.")
    lines.append("")
    lines.append("## Generated files")
    lines.append("")
    for label, path in generated_files:
        if path:
            lines.append(f"- **{label}:** `{os.path.basename(path) if os.path.dirname(path) == report.get('out_dir') else path}`")
    return "\n".join(lines) + "\n"


# ----------------------------------- main -----------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gt", required=True)
    parser.add_argument("--run-csv", required=True)
    parser.add_argument("--baseline-csv")
    parser.add_argument("--segments", required=True)
    parser.add_argument("--perturbations")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--gt-yaw-offset-deg", type=float, default=float(os.environ.get("GT_YAW_OFFSET_DEG", 0.0)))
    parser.add_argument("--algorithm-note", default=os.environ.get("ALGO_NOTES", ""))
    parser.add_argument("--gps-mode", default=os.environ.get("GPS_ENABLE", "off"))
    parser.add_argument("--gps-source", default=os.environ.get("GPS_SOURCE", "none"))
    parser.add_argument("--rtk-mode", default=os.environ.get("RTK_MODE", "auto"))
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    gt = load_ground_truth(args.gt, args.gt_yaw_offset_deg)
    run = load_trajectory(args.run_csv)
    baseline = load_trajectory(args.baseline_csv) if args.baseline_csv else []
    segments = load_yaml_list(args.segments, "segments")
    perturbations = load_yaml_list(args.perturbations, "perturbations")
    errors = matched_error_rows(run, gt)

    report = {
        "out_dir": args.out_dir,
        "algorithm_note": args.algorithm_note or "",
        "gps_mode": args.gps_mode,
        "gps_source": args.gps_source,
        "rtk_mode": args.rtk_mode,
        "overall": metrics_from_errors(errors),
        "segments_yaml": args.segments,
        "perturbations_yaml": args.perturbations,
        "segments": {},
        "perturbation_windows": {},
        "run_time_range": {"start": run[0]["stamp"] if run else None, "end": run[-1]["stamp"] if run else None},
        "ground_truth_time_range": {"start": gt[0]["stamp"] if gt else None, "end": gt[-1]["stamp"] if gt else None},
    }

    for idx, segment in enumerate(segments, start=1):
        try:
            start = float(segment["start"])
            end = float(segment["end"])
        except (KeyError, TypeError, ValueError):
            continue
        name = segment.get("name", f"segment_{idx}")
        key = f"{idx:02d}_{safe_name(name)}"
        rows = filter_error_rows(errors, start, end)
        rel_rows = _relative_rows(rows)
        report["segments"][key] = {
            "name": name,
            "label": f"{idx:02d} {name}",
            "type": segment.get("type", "unknown"),
            "description": segment.get("description", ""),
            "start": start,
            "end": end,
            "absolute_metrics": metrics_from_errors(rows),
            "relative_metrics": metrics_from_errors(rel_rows),
            # Keep raw rows only until CSV writing, then strip them before JSON.
            "error_rows": rows,
            "relative_error_rows": rel_rows,
        }

    for idx, perturbation in enumerate(perturbations, start=1):
        try:
            start = float(perturbation["start"])
            end = float(perturbation["end"])
        except (KeyError, TypeError, ValueError):
            continue
        name = perturbation.get("name", f"perturbation_{idx}")
        key = f"{idx:02d}_{safe_name(name)}"
        rows = filter_error_rows(errors, start, end)
        rel_rows = _relative_rows(rows)
        report["perturbation_windows"][key] = {
            "name": name,
            "label": f"{idx:02d} {name}",
            "sensor": perturbation.get("sensor", "unknown"),
            "perturbation_type": perturbation.get("type", "unknown"),
            "start": start,
            "end": end,
            "absolute_metrics": metrics_from_errors(rows),
            "relative_metrics": metrics_from_errors(rel_rows),
        }

    report["robustness_score_lower_is_better"] = robustness_score(report["overall"])

    generated = []
    generated.append(("trajectory CSV", args.run_csv))
    generated.append(("error over time CSV", write_error_csv(args.out_dir, errors)))
    generated.append(("segment metrics CSV", write_window_csv(args.out_dir, "segment_metrics.csv", component_rows(report["segments"]))))
    generated.append(("perturbation window metrics CSV", write_window_csv(args.out_dir, "perturbation_window_metrics.csv", component_rows(report["perturbation_windows"]))))
    generated.append(("segment per-window error CSV directory", os.path.join(args.out_dir, "segment_error_timeseries")))
    write_segment_error_csvs(args.out_dir, report["segments"])

    generated.append(("trajectory XY plot", write_trajectory_plot(args.out_dir, gt, run, baseline)))
    generated.append(("error over time plot", write_error_plot(args.out_dir, errors)))
    generated.append(("yaw error over time plot", write_yaw_error_plot(args.out_dir, errors)))
    generated.append(("segment position RMSE bar graph", write_segment_position_bar(args.out_dir, report["segments"])))
    generated.append(("segment component RMSE bar graph", write_segment_component_bar(args.out_dir, report["segments"])))
    generated.append(("perturbation window RMSE bar graph", write_perturbation_bar(args.out_dir, report["perturbation_windows"])))

    # JSON should be compact enough to inspect; do not embed every per-segment time series.
    json_report = json.loads(json.dumps(report, default=str))
    for section in ("segments",):
        for item in json_report.get(section, {}).values():
            item.pop("error_rows", None)
            item.pop("relative_error_rows", None)
    json_report["generated_files"] = [{"label": label, "path": path} for label, path in generated if path]

    json_path = os.path.join(args.out_dir, "metrics.json")
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(json_report, handle, indent=2)
    generated.append(("machine-readable metrics JSON", json_path))

    md_text = report_markdown(json_report, generated)
    md_path = os.path.join(args.out_dir, "analysis.md")
    txt_path = os.path.join(args.out_dir, "analysis.txt")
    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write(md_text)
    with open(txt_path, "w", encoding="utf-8") as handle:
        handle.write(md_text)

    print(json_path)


if __name__ == "__main__":
    main()
