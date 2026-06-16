#!/usr/bin/env python3
import argparse
import csv
import json
import math
import os
from bisect import bisect_left

import yaml


WGS84_A = 6378137.0
WGS84_E2 = 6.69437999014e-3


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
    ss = math.sin(yaw_offset_rad)
    return c * x - ss * y, ss * x + c * y


def normalize_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def csv_value(row, *names, default=None):
    for name in names:
        if row.get(name) not in (None, ""):
            return row[name]
    return default


def yaw_from_csv_row(row):
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


def load_csv_ground_truth(path, yaw_offset_deg=0.0):
    out = []
    rows = []
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
    yaw_offset_rad = math.radians(yaw_offset_deg)
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


def load_ground_truth(path, yaw_offset_deg=0.0):
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
            "yaw": math.radians(row["heading"] - ref["heading"] + yaw_offset_deg),
        })
    return out


def load_trajectory(path):
    out = []
    if not os.path.isfile(path):
        return out
    with open(path, "r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            out.append({
                "stamp": float(row["stamp"]),
                "x": float(row["x"]),
                "y": float(row["y"]),
                "z": float(row["z"]),
                "yaw": float(row["yaw"]),
            })
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


def angle_diff(a, b):
    return math.atan2(math.sin(a - b), math.cos(a - b))


def rmse(values):
    if not values:
        return None
    return math.sqrt(sum(v * v for v in values) / len(values))


def metrics_for(samples, gt):
    gt_stamps = [g["stamp"] for g in gt]
    ex, ey, ez, eyaw, epos = [], [], [], [], []
    for sample in samples:
        ref = nearest(sample, gt, gt_stamps)
        if ref is None or abs(ref["stamp"] - sample["stamp"]) > 0.75:
            continue
        dx = sample["x"] - ref["x"]
        dy = sample["y"] - ref["y"]
        dz = sample["z"] - ref["z"]
        ex.append(dx)
        ey.append(dy)
        ez.append(dz)
        eyaw.append(angle_diff(sample["yaw"], ref["yaw"]))
        epos.append(math.sqrt(dx * dx + dy * dy + dz * dz))
    components = {
        "x_rmse_m": rmse(ex),
        "y_rmse_m": rmse(ey),
        "z_rmse_m": rmse(ez),
        "yaw_rmse_rad": rmse(eyaw),
        "position_rmse_m": rmse(epos),
        "position_max_m": max(epos) if epos else None,
        "samples": len(epos),
    }
    comparable = {
        k: v for k, v in components.items()
        if (k.endswith("_m") or k.endswith("_rad")) and v is not None
    }
    components["worst_component"] = max(comparable, key=lambda k: comparable[k] or -1.0) if comparable else None
    return components


def error_series(samples, gt):
    gt_stamps = [g["stamp"] for g in gt]
    rows = []
    for sample in samples:
        ref = nearest(sample, gt, gt_stamps)
        if ref is None or abs(ref["stamp"] - sample["stamp"]) > 0.75:
            continue
        dx = sample["x"] - ref["x"]
        dy = sample["y"] - ref["y"]
        dz = sample["z"] - ref["z"]
        yaw = angle_diff(sample["yaw"], ref["yaw"])
        rows.append({
            "stamp": sample["stamp"],
            "x_error_m": dx,
            "y_error_m": dy,
            "z_error_m": dz,
            "yaw_error_rad": yaw,
            "position_error_m": math.sqrt(dx * dx + dy * dy + dz * dz),
        })
    return rows


def filter_time(samples, start, end):
    return [s for s in samples if start <= s["stamp"] <= end]


def load_yaml_list(path, key):
    if not path or not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return (yaml.safe_load(handle) or {}).get(key, []) or []


def component_rows(reports):
    rows = []
    for key, report in reports.items():
        metrics = report.get("metrics") or {}
        if metrics.get("samples", 0) <= 0:
            continue
        rows.append({
            "key": key,
            "label": report.get("label", key),
            "type": report.get("type", "unknown"),
            "sensor": report.get("sensor", ""),
            "perturbation_type": report.get("perturbation_type", ""),
            "start": report.get("start"),
            "end": report.get("end"),
            "x_rmse_m": metrics.get("x_rmse_m"),
            "y_rmse_m": metrics.get("y_rmse_m"),
            "z_rmse_m": metrics.get("z_rmse_m"),
            "yaw_rmse_rad": metrics.get("yaw_rmse_rad"),
            "position_rmse_m": metrics.get("position_rmse_m"),
            "position_max_m": metrics.get("position_max_m"),
            "worst_component": metrics.get("worst_component"),
            "samples": metrics.get("samples", 0),
        })
    return rows


def write_window_csv(out_dir, filename, rows):
    path = os.path.join(out_dir, filename)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "key", "label", "type", "sensor", "perturbation_type", "start", "end",
            "x_rmse_m", "y_rmse_m", "z_rmse_m", "yaw_rmse_rad",
            "position_rmse_m", "position_max_m", "worst_component", "samples",
        ])
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_plot(out_dir, name, baseline, run):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    if not run:
        return None
    path = os.path.join(out_dir, name)
    plt.figure(figsize=(9, 7))
    if baseline:
        plt.plot([s["x"] for s in baseline], [s["y"] for s in baseline], label="baseline", linewidth=1.4)
    plt.plot([s["x"] for s in run], [s["y"] for s in run], label="selected run", linewidth=1.2)
    plt.axis("equal")
    plt.grid(True)
    plt.legend()
    plt.xlabel("x m")
    plt.ylabel("y m")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path


def write_error_csv(out_dir, rows):
    path = os.path.join(out_dir, "error_timeseries.csv")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "stamp", "x_error_m", "y_error_m", "z_error_m", "yaw_error_rad", "position_error_m",
        ])
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_error_plot(out_dir, rows):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    if not rows:
        return None
    path = os.path.join(out_dir, "component_errors_over_time.png")
    t0 = rows[0]["stamp"]
    times = [r["stamp"] - t0 for r in rows]
    plt.figure(figsize=(11, 7))
    plt.plot(times, [r["x_error_m"] for r in rows], label="x error m", linewidth=1.0)
    plt.plot(times, [r["y_error_m"] for r in rows], label="y error m", linewidth=1.0)
    plt.plot(times, [r["z_error_m"] for r in rows], label="z error m", linewidth=1.0)
    plt.plot(times, [r["position_error_m"] for r in rows], label="position error m", linewidth=1.2)
    plt.xlabel("seconds from first localization output")
    plt.ylabel("error")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path


def write_segment_plot(out_dir, segment_reports):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    names = []
    pos = []
    yaw = []
    for name, report in segment_reports.items():
        metrics = report.get("metrics") or {}
        if metrics.get("position_rmse_m") is None:
            continue
        names.append(name)
        pos.append(metrics.get("position_rmse_m") or 0.0)
        yaw.append(metrics.get("yaw_rmse_rad") or 0.0)
    if not names:
        return None
    path = os.path.join(out_dir, "segment_rmse.png")
    x = range(len(names))
    plt.figure(figsize=(max(8, len(names) * 1.2), 6))
    plt.bar(x, pos, label="position RMSE m")
    plt.plot(list(x), yaw, color="tab:red", marker="o", label="yaw RMSE rad")
    plt.xticks(list(x), names, rotation=30, ha="right")
    plt.ylabel("RMSE")
    plt.grid(True, axis="y")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path


def write_component_bar_plot(out_dir, filename, title, rows):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    rows = [row for row in rows if row.get("position_rmse_m") is not None]
    if not rows:
        return None
    path = os.path.join(out_dir, filename)
    labels = [row["label"] for row in rows]
    x = range(len(rows))
    plt.figure(figsize=(max(10, len(rows) * 0.9), 7))
    plt.bar(x, [row.get("x_rmse_m") or 0.0 for row in rows], label="x RMSE m")
    plt.bar(x, [row.get("y_rmse_m") or 0.0 for row in rows], bottom=[row.get("x_rmse_m") or 0.0 for row in rows], label="y RMSE m")
    z_bottom = [(row.get("x_rmse_m") or 0.0) + (row.get("y_rmse_m") or 0.0) for row in rows]
    plt.bar(x, [row.get("z_rmse_m") or 0.0 for row in rows], bottom=z_bottom, label="z RMSE m")
    plt.plot(list(x), [row.get("position_rmse_m") or 0.0 for row in rows], color="black", marker="o", label="position RMSE m")
    plt.xticks(list(x), labels, rotation=35, ha="right")
    plt.ylabel("RMSE")
    plt.title(title)
    plt.grid(True, axis="y")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path


def robustness_score(metrics):
    if not metrics:
        return None
    pos = metrics.get("position_rmse_m")
    yaw = metrics.get("yaw_rmse_rad")
    if pos is None and yaw is None:
        return None
    return float(pos or 0.0) + 10.0 * float(yaw or 0.0)


def format_metric(value, suffix=""):
    if value is None:
        return "n/a"
    return f"{value:.6f}{suffix}"


def ranked_by_position(reports):
    return sorted(
        [
            item for item in reports.items()
            if ((item[1].get("metrics") or {}).get("position_rmse_m") is not None)
        ],
        key=lambda item: (item[1].get("metrics") or {}).get("position_rmse_m") or -1.0,
        reverse=True,
    )


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

    report = {
        "algorithm_note": args.algorithm_note or "",
        "gps_mode": args.gps_mode,
        "gps_source": args.gps_source,
        "rtk_mode": args.rtk_mode,
        "overall": metrics_for(run, gt),
        "segments": {},
        "perturbation_windows": {},
        "run_time_range": {
            "start": run[0]["stamp"] if run else None,
            "end": run[-1]["stamp"] if run else None,
        },
        "ground_truth_time_range": {
            "start": gt[0]["stamp"] if gt else None,
            "end": gt[-1]["stamp"] if gt else None,
        },
    }
    for idx, segment in enumerate(segments, start=1):
        start = float(segment["start"])
        end = float(segment["end"])
        name = segment.get("name", f"segment_{idx}")
        key = f"{idx:02d}_{name}"
        label = f"{idx:02d} {name}"
        report["segments"][key] = {
            "name": name,
            "label": label,
            "type": segment.get("type", "unknown"),
            "start": start,
            "end": end,
            "metrics": metrics_for(filter_time(run, start, end), gt),
        }
    for idx, perturbation in enumerate(perturbations, start=1):
        start = float(perturbation["start"])
        end = float(perturbation["end"])
        name = perturbation.get("name", f"perturbation_{idx}")
        key = f"{idx:02d}_{name}"
        label = f"{idx:02d} {name}"
        report["perturbation_windows"][key] = {
            "name": name,
            "label": label,
            "sensor": perturbation.get("sensor", "unknown"),
            "perturbation_type": perturbation.get("type", "unknown"),
            "start": start,
            "end": end,
            "metrics": metrics_for(filter_time(run, start, end), gt),
        }
    report["robustness_score_lower_is_better"] = robustness_score(report["overall"])

    plot = write_plot(args.out_dir, "trajectory_baseline_vs_run.png", baseline, run)
    if plot:
        report["trajectory_plot"] = plot
    errors = error_series(run, gt)
    report["error_timeseries_csv"] = write_error_csv(args.out_dir, errors)
    error_plot = write_error_plot(args.out_dir, errors)
    if error_plot:
        report["component_error_plot"] = error_plot
    segment_plot = write_segment_plot(args.out_dir, report["segments"])
    if segment_plot:
        report["segment_rmse_plot"] = segment_plot
    segment_rows = component_rows(report["segments"])
    perturbation_rows = component_rows(report["perturbation_windows"])
    report["segment_metrics_csv"] = write_window_csv(args.out_dir, "segment_metrics.csv", segment_rows)
    report["perturbation_window_metrics_csv"] = write_window_csv(
        args.out_dir,
        "perturbation_window_metrics.csv",
        perturbation_rows,
    )
    segment_component_plot = write_component_bar_plot(
        args.out_dir,
        "segment_component_rmse.png",
        "Road segment component RMSE",
        segment_rows,
    )
    if segment_component_plot:
        report["segment_component_rmse_plot"] = segment_component_plot
    perturbation_plot = write_component_bar_plot(
        args.out_dir,
        "perturbation_window_component_rmse.png",
        "Perturbation window component RMSE",
        perturbation_rows,
    )
    if perturbation_plot:
        report["perturbation_window_component_rmse_plot"] = perturbation_plot

    json_path = os.path.join(args.out_dir, "metrics.json")
    txt_path = os.path.join(args.out_dir, "analysis.txt")
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    with open(txt_path, "w", encoding="utf-8") as handle:
        overall = report["overall"] or {}
        handle.write("Localization run analysis\n")
        handle.write("=========================\n\n")
        if report.get("algorithm_note"):
            handle.write(f"Algorithm note: {report['algorithm_note']}\n\n")
        handle.write(f"GPS mode: {report.get('gps_mode', 'off')}\n")
        handle.write(f"GPS source: {report.get('gps_source', 'none')}\n")
        handle.write(f"RTK mode: {report.get('rtk_mode', 'auto')}\n\n")
        handle.write(f"Samples compared: {overall.get('samples', 0)}\n")
        handle.write(f"Robustness score, lower is better: {format_metric(report.get('robustness_score_lower_is_better'))}\n")
        handle.write(f"Overall position RMSE: {format_metric(overall.get('position_rmse_m'), ' m')}\n")
        handle.write(f"Overall position max: {format_metric(overall.get('position_max_m'), ' m')}\n")
        handle.write(f"Overall x RMSE: {format_metric(overall.get('x_rmse_m'), ' m')}\n")
        handle.write(f"Overall y RMSE: {format_metric(overall.get('y_rmse_m'), ' m')}\n")
        handle.write(f"Overall z RMSE: {format_metric(overall.get('z_rmse_m'), ' m')}\n")
        handle.write(f"Overall yaw RMSE: {format_metric(overall.get('yaw_rmse_rad'), ' rad')}\n")
        handle.write(f"Worst overall component: {overall.get('worst_component', 'n/a')}\n\n")
        run_range = report["run_time_range"]
        gt_range = report["ground_truth_time_range"]
        handle.write(f"Run CSV time range: {run_range.get('start')} to {run_range.get('end')}\n")
        handle.write(f"Ground truth time range: {gt_range.get('start')} to {gt_range.get('end')}\n")
        handle.write("If a scene/window shows zero samples, its timestamps do not overlap the run CSV time range.\n\n")
        handle.write("Road scene impact\n")
        handle.write("-----------------\n")
        scene_items = list(report["segments"].items())
        for key, segment in scene_items:
            metrics = segment.get("metrics") or {}
            handle.write(
                f"{segment.get('label', key)} ({segment.get('type', 'unknown')}, {segment.get('start')} to {segment.get('end')}): "
                f"position_rmse={format_metric(metrics.get('position_rmse_m'), ' m')}, "
                f"x_rmse={format_metric(metrics.get('x_rmse_m'), ' m')}, "
                f"y_rmse={format_metric(metrics.get('y_rmse_m'), ' m')}, "
                f"z_rmse={format_metric(metrics.get('z_rmse_m'), ' m')}, "
                f"yaw_rmse={format_metric(metrics.get('yaw_rmse_rad'), ' rad')}, "
                f"worst_component={metrics.get('worst_component', 'n/a')}, "
                f"samples={metrics.get('samples', 0)}\n"
            )
        handle.write("\nMost affected scene by position RMSE: ")
        ranked = ranked_by_position(report["segments"])
        if ranked:
            top_key, top_segment = ranked[0]
            top_metrics = top_segment.get("metrics") or {}
            handle.write(
                f"{top_segment.get('label', top_key)} "
                f"with {format_metric(top_metrics.get('position_rmse_m'), ' m')} "
                f"and worst component {top_metrics.get('worst_component', 'n/a')}\n"
            )
        else:
            handle.write("n/a\n")

        handle.write("\nPerturbation window impact\n")
        handle.write("--------------------------\n")
        if report["perturbation_windows"]:
            window_items = list(report["perturbation_windows"].items())
            for key, window in window_items:
                metrics = window.get("metrics") or {}
                handle.write(
                    f"{window.get('label', key)} "
                    f"({window.get('sensor', 'unknown')} {window.get('perturbation_type', 'unknown')}, "
                    f"{window.get('start')} to {window.get('end')}): "
                    f"position_rmse={format_metric(metrics.get('position_rmse_m'), ' m')}, "
                    f"x_rmse={format_metric(metrics.get('x_rmse_m'), ' m')}, "
                    f"y_rmse={format_metric(metrics.get('y_rmse_m'), ' m')}, "
                    f"z_rmse={format_metric(metrics.get('z_rmse_m'), ' m')}, "
                    f"yaw_rmse={format_metric(metrics.get('yaw_rmse_rad'), ' rad')}, "
                    f"worst_component={metrics.get('worst_component', 'n/a')}, "
                    f"samples={metrics.get('samples', 0)}\n"
                )
            ranked_perturbations = ranked_by_position(report["perturbation_windows"])
            if ranked_perturbations:
                top_key, top_window = ranked_perturbations[0]
                top_metrics = top_window.get("metrics") or {}
                handle.write(
                    f"\nMost affected perturbation window: {top_window.get('label', top_key)} "
                    f"with {format_metric(top_metrics.get('position_rmse_m'), ' m')} "
                    f"and worst component {top_metrics.get('worst_component', 'n/a')}\n"
                )
            else:
                handle.write("\nMost affected perturbation window: n/a, no perturbation windows overlapped the run CSV time range.\n")
        else:
            handle.write("No perturbation windows configured for this case.\n")

        handle.write("\nGenerated files\n")
        handle.write("---------------\n")
        for key in (
            "trajectory_plot",
            "component_error_plot",
            "segment_rmse_plot",
            "segment_component_rmse_plot",
            "perturbation_window_component_rmse_plot",
            "error_timeseries_csv",
            "segment_metrics_csv",
            "perturbation_window_metrics_csv",
        ):
            if report.get(key):
                handle.write(f"{key}: {report[key]}\n")
    print(json_path)


if __name__ == "__main__":
    main()
