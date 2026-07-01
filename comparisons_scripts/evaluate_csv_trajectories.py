#!/usr/bin/env python3
"""
Compare two trajectory CSVs and save overall error metrics + per-sample errors.

Important:
  If neither CSV is ground truth, these are trajectory disagreement metrics,
  NOT absolute localization accuracy metrics.

Supports common column names:
  Time:
    timestamp_s, timestamp, time, t, stamp
    timestamp_ns, time_ns, stamp_ns
  Position:
    x_m,y_m,z_m OR x,y,z OR position_x,position_y,position_z
  Orientation:
    qx,qy,qz,qw OR orientation_x,... OR roll,pitch,yaw

Example:
  python3 evaluate_csv_trajectories.py \
    --csv-a lvisam.csv \
    --csv-b fastlio2.csv \
    --name-a LVISAM \
    --name-b FASTLIO2 \
    --align se2 \
    --max-time-diff 0.10 \
    --out-dir evaluation_lvisam_vs_fastlio2
"""

import argparse
import bisect
import csv
import json
import math
import os
import sys
from datetime import datetime, timezone


def finite_float(value, default=None):
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def canonical_header(name):
    return (name or "").replace("\ufeff", "").strip().lower()


def find_column(headers, aliases):
    normalized = {canonical_header(h): h for h in headers if h}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def normalize_quaternion(qx, qy, qz, qw):
    norm = math.sqrt(qx*qx + qy*qy + qz*qz + qw*qw)
    if norm < 1e-12:
        return 0.0, 0.0, 0.0, 1.0
    return qx / norm, qy / norm, qz / norm, qw / norm


def yaw_from_quaternion(qx, qy, qz, qw):
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    return math.atan2(siny_cosp, cosy_cosp)


def euler_to_quaternion(roll, pitch, yaw):
    cr, sr = math.cos(roll / 2.0), math.sin(roll / 2.0)
    cp, sp = math.cos(pitch / 2.0), math.sin(pitch / 2.0)
    cy, sy = math.cos(yaw / 2.0), math.sin(yaw / 2.0)
    return normalize_quaternion(
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    )


def q_multiply(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def angle_wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def load_csv(path):
    poses = []

    with open(path, "r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise RuntimeError(f"{path}: CSV has no header row.")

        headers = reader.fieldnames
        col_time_s = find_column(headers, ("timestamp_s", "timestamp", "time", "t", "stamp"))
        col_time_ns = find_column(headers, ("timestamp_ns", "time_ns", "stamp_ns"))

        col_x = find_column(headers, ("x_m", "x", "position_x", "pos_x", "px"))
        col_y = find_column(headers, ("y_m", "y", "position_y", "pos_y", "py"))
        col_z = find_column(headers, ("z_m", "z", "position_z", "pos_z", "pz"))

        col_qx = find_column(headers, ("qx", "orientation_x", "quat_x", "q_x"))
        col_qy = find_column(headers, ("qy", "orientation_y", "quat_y", "q_y"))
        col_qz = find_column(headers, ("qz", "orientation_z", "quat_z", "q_z"))
        col_qw = find_column(headers, ("qw", "orientation_w", "quat_w", "q_w"))

        col_roll = find_column(headers, ("roll_rad", "roll", "r"))
        col_pitch = find_column(headers, ("pitch_rad", "pitch", "p"))
        col_yaw = find_column(headers, ("yaw_rad", "yaw", "heading", "psi"))

        missing = [
            label for label, value in (("x", col_x), ("y", col_y), ("z", col_z))
            if value is None
        ]
        if missing:
            raise RuntimeError(
                f"{path}: missing position columns {', '.join(missing)}. "
                f"Found headers: {', '.join(headers)}"
            )

        has_quaternion = all((col_qx, col_qy, col_qz, col_qw))
        has_euler = all((col_roll, col_pitch, col_yaw))
        if not has_quaternion and not has_euler:
            raise RuntimeError(
                f"{path}: need qx,qy,qz,qw or roll,pitch,yaw. "
                f"Found headers: {', '.join(headers)}"
            )

        for row_index, row in enumerate(reader):
            x = finite_float(row.get(col_x))
            y = finite_float(row.get(col_y))
            z = finite_float(row.get(col_z))
            if any(v is None for v in (x, y, z)):
                continue

            if col_time_s:
                timestamp_s = finite_float(row.get(col_time_s), float(row_index))
            elif col_time_ns:
                ns = finite_float(row.get(col_time_ns))
                timestamp_s = ns / 1e9 if ns is not None else float(row_index)
            else:
                timestamp_s = float(row_index)

            if has_quaternion:
                qx = finite_float(row.get(col_qx))
                qy = finite_float(row.get(col_qy))
                qz = finite_float(row.get(col_qz))
                qw = finite_float(row.get(col_qw))
                if any(v is None for v in (qx, qy, qz, qw)):
                    continue
                qx, qy, qz, qw = normalize_quaternion(qx, qy, qz, qw)
            else:
                roll = finite_float(row.get(col_roll))
                pitch = finite_float(row.get(col_pitch))
                yaw = finite_float(row.get(col_yaw))
                if any(v is None for v in (roll, pitch, yaw)):
                    continue
                qx, qy, qz, qw = euler_to_quaternion(roll, pitch, yaw)

            poses.append({
                "timestamp_s": timestamp_s,
                "x": x, "y": y, "z": z,
                "qx": qx, "qy": qy, "qz": qz, "qw": qw,
            })

    if not poses:
        raise RuntimeError(f"{path}: no valid poses found.")
    poses.sort(key=lambda p: p["timestamp_s"])
    return poses


def align_b_to_a(poses_a, poses_b, mode):
    """Align B to A based on their first valid poses. B only is transformed."""
    if mode == "none":
        return [dict(p) for p in poses_b]

    a0, b0 = poses_a[0], poses_b[0]
    theta = 0.0
    if mode == "se2":
        theta = (
            yaw_from_quaternion(a0["qx"], a0["qy"], a0["qz"], a0["qw"])
            - yaw_from_quaternion(b0["qx"], b0["qy"], b0["qz"], b0["qw"])
        )

    c, s = math.cos(theta), math.sin(theta)
    b0_rx = c * b0["x"] - s * b0["y"]
    b0_ry = s * b0["x"] + c * b0["y"]
    tx = a0["x"] - b0_rx
    ty = a0["y"] - b0_ry
    tz = a0["z"] - b0["z"]
    q_align = (0.0, 0.0, math.sin(theta / 2.0), math.cos(theta / 2.0))

    transformed = []
    for p in poses_b:
        out = dict(p)
        out["x"] = c * p["x"] - s * p["y"] + tx
        out["y"] = s * p["x"] + c * p["y"] + ty
        out["z"] = p["z"] + tz
        out["qx"], out["qy"], out["qz"], out["qw"] = normalize_quaternion(
            *q_multiply(q_align, (p["qx"], p["qy"], p["qz"], p["qw"]))
        )
        transformed.append(out)
    return transformed


def closest_by_timestamp(poses_a, poses_b, max_time_diff):
    """
    Pair every A pose with the closest B timestamp.
    No B sample may be used twice, so metrics do not artificially over-weight it.
    """
    b_times = [p["timestamp_s"] for p in poses_b]
    matches = []
    used_b_indices = set()

    for a in poses_a:
        t = a["timestamp_s"]
        idx = bisect.bisect_left(b_times, t)
        candidates = []
        if idx < len(poses_b):
            candidates.append(idx)
        if idx > 0:
            candidates.append(idx - 1)

        candidates = [i for i in candidates if i not in used_b_indices]
        if not candidates:
            continue

        best_i = min(candidates, key=lambda i: abs(b_times[i] - t))
        dt = b_times[best_i] - t
        if abs(dt) <= max_time_diff:
            used_b_indices.add(best_i)
            matches.append((a, poses_b[best_i], dt))

    return matches


def mean(values):
    return sum(values) / len(values) if values else float("nan")


def rmse(values):
    return math.sqrt(mean([v * v for v in values])) if values else float("nan")


def percentile(values, pct):
    if not values:
        return float("nan")
    sorted_values = sorted(values)
    position = (len(sorted_values) - 1) * pct / 100.0
    lo = int(math.floor(position))
    hi = int(math.ceil(position))
    if lo == hi:
        return sorted_values[lo]
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (position - lo)


def metric_block(values):
    absolute = [abs(v) for v in values]
    return {
        "mean_signed": mean(values),
        "mae": mean(absolute),
        "rmse": rmse(values),
        "median_abs": percentile(absolute, 50),
        "p95_abs": percentile(absolute, 95),
        "max_abs": max(absolute) if absolute else float("nan"),
    }


def safe_json_number(value):
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def recursively_safe_json(value):
    if isinstance(value, dict):
        return {k: recursively_safe_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [recursively_safe_json(v) for v in value]
    return safe_json_number(value)


def save_metrics_text(path, summary):
    m = summary["metrics"]
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("TRAJECTORY COMPARISON SUMMARY\n")
        handle.write("=" * 50 + "\n")
        handle.write(f"A: {summary['input']['name_a']} ({summary['input']['csv_a']})\n")
        handle.write(f"B: {summary['input']['name_b']} ({summary['input']['csv_b']})\n")
        handle.write(f"Alignment applied to B: {summary['input']['align']}\n")
        handle.write(f"Matched samples: {summary['matching']['matched_samples']}\n")
        handle.write(f"A samples: {summary['matching']['a_samples']}\n")
        handle.write(f"B samples: {summary['matching']['b_samples']}\n")
        handle.write(
            f"Time difference |mean| / max: "
            f"{summary['matching']['mean_abs_time_difference_s']:.6f} / "
            f"{summary['matching']['max_abs_time_difference_s']:.6f} s\n\n"
        )

        handle.write("POSITION DISAGREEMENT (B - A)\n")
        handle.write("-" * 50 + "\n")
        for key, label, unit in (
            ("x_error_m", "X error", "m"),
            ("y_error_m", "Y error", "m"),
            ("z_error_m", "Z error", "m"),
            ("position_2d_error_m", "2D position error", "m"),
            ("position_3d_error_m", "3D position error", "m"),
            ("yaw_error_deg", "Yaw error", "deg"),
        ):
            block = m[key]
            handle.write(
                f"{label}: MAE={block['mae']:.4f} {unit}, "
                f"RMSE={block['rmse']:.4f} {unit}, "
                f"P95={block['p95_abs']:.4f} {unit}, "
                f"MAX={block['max_abs']:.4f} {unit}\n"
            )

        handle.write("\nNOTE\n")
        handle.write(
            "These values compare CSV B against CSV A. They are absolute accuracy "
            "metrics only when CSV A is ground truth.\n"
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Calculate overall trajectory error metrics from two CSV files."
    )
    parser.add_argument("--csv-a", required=True, help="Reference CSV / ground truth if available")
    parser.add_argument("--csv-b", required=True, help="Compared trajectory CSV")
    parser.add_argument("--name-a", default="Trajectory A")
    parser.add_argument("--name-b", default="Trajectory B")
    parser.add_argument(
        "--align",
        choices=("none", "translation", "se2"),
        default="se2",
        help=(
            "Transform B before calculating metrics. Default se2 aligns first XYZ and yaw. "
            "Use none only when both CSVs already share one global frame."
        ),
    )
    parser.add_argument(
        "--max-time-diff",
        type=float,
        default=0.10,
        help="Maximum allowed closest timestamp difference in seconds (default 0.10).",
    )
    parser.add_argument(
        "--out-dir",
        default="trajectory_evaluation",
        help="Directory where summary and per-sample errors are saved.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.max_time_diff < 0:
        raise ValueError("--max-time-diff must be >= 0")

    for path in (args.csv_a, args.csv_b):
        if not os.path.isfile(path):
            raise FileNotFoundError(f"CSV not found: {path}")

    poses_a = load_csv(args.csv_a)
    poses_b_raw = load_csv(args.csv_b)
    poses_b = align_b_to_a(poses_a, poses_b_raw, args.align)
    matches = closest_by_timestamp(poses_a, poses_b, args.max_time_diff)

    if len(matches) < 2:
        raise RuntimeError(
            f"Only {len(matches)} samples matched within {args.max_time_diff:.3f}s. "
            "Increase --max-time-diff or verify both CSV timestamp columns."
        )

    os.makedirs(args.out_dir, exist_ok=True)
    per_sample_path = os.path.join(args.out_dir, "per_sample_errors.csv")
    json_path = os.path.join(args.out_dir, "summary.json")
    text_path = os.path.join(args.out_dir, "summary.txt")

    dxs, dys, dzs = [], [], []
    errs_2d, errs_3d, yaw_errs_deg, abs_dts = [], [], [], []

    with open(per_sample_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "timestamp_a_s", "timestamp_b_s", "time_difference_s",
                "a_x_m", "a_y_m", "a_z_m",
                "b_x_m", "b_y_m", "b_z_m",
                "error_x_m", "error_y_m", "error_z_m",
                "position_2d_error_m", "position_3d_error_m",
                "yaw_a_rad", "yaw_b_rad", "yaw_error_rad", "yaw_error_deg",
            ],
        )
        writer.writeheader()

        for a, b, dt in matches:
            dx = b["x"] - a["x"]
            dy = b["y"] - a["y"]
            dz = b["z"] - a["z"]
            err2d = math.sqrt(dx*dx + dy*dy)
            err3d = math.sqrt(dx*dx + dy*dy + dz*dz)

            yaw_a = yaw_from_quaternion(a["qx"], a["qy"], a["qz"], a["qw"])
            yaw_b = yaw_from_quaternion(b["qx"], b["qy"], b["qz"], b["qw"])
            yaw_error_rad = angle_wrap(yaw_b - yaw_a)
            yaw_error_deg = math.degrees(yaw_error_rad)

            dxs.append(dx)
            dys.append(dy)
            dzs.append(dz)
            errs_2d.append(err2d)
            errs_3d.append(err3d)
            yaw_errs_deg.append(yaw_error_deg)
            abs_dts.append(abs(dt))

            writer.writerow({
                "timestamp_a_s": f"{a['timestamp_s']:.9f}",
                "timestamp_b_s": f"{b['timestamp_s']:.9f}",
                "time_difference_s": f"{dt:.9f}",
                "a_x_m": f"{a['x']:.9f}",
                "a_y_m": f"{a['y']:.9f}",
                "a_z_m": f"{a['z']:.9f}",
                "b_x_m": f"{b['x']:.9f}",
                "b_y_m": f"{b['y']:.9f}",
                "b_z_m": f"{b['z']:.9f}",
                "error_x_m": f"{dx:.9f}",
                "error_y_m": f"{dy:.9f}",
                "error_z_m": f"{dz:.9f}",
                "position_2d_error_m": f"{err2d:.9f}",
                "position_3d_error_m": f"{err3d:.9f}",
                "yaw_a_rad": f"{yaw_a:.9f}",
                "yaw_b_rad": f"{yaw_b:.9f}",
                "yaw_error_rad": f"{yaw_error_rad:.9f}",
                "yaw_error_deg": f"{yaw_error_deg:.9f}",
            })

    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "input": {
            "csv_a": os.path.abspath(args.csv_a),
            "csv_b": os.path.abspath(args.csv_b),
            "name_a": args.name_a,
            "name_b": args.name_b,
            "align": args.align,
            "interpretation": (
                f"Errors are B - A. These are absolute accuracy metrics only if {args.name_a} is ground truth."
            ),
        },
        "matching": {
            "a_samples": len(poses_a),
            "b_samples": len(poses_b),
            "matched_samples": len(matches),
            "max_time_diff_threshold_s": args.max_time_diff,
            "mean_abs_time_difference_s": mean(abs_dts),
            "max_abs_time_difference_s": max(abs_dts),
        },
        "metrics": {
            "x_error_m": metric_block(dxs),
            "y_error_m": metric_block(dys),
            "z_error_m": metric_block(dzs),
            "position_2d_error_m": metric_block(errs_2d),
            "position_3d_error_m": metric_block(errs_3d),
            "yaw_error_deg": metric_block(yaw_errs_deg),
        },
        "outputs": {
            "per_sample_errors_csv": os.path.abspath(per_sample_path),
            "summary_json": os.path.abspath(json_path),
            "summary_txt": os.path.abspath(text_path),
        },
    }

    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(recursively_safe_json(summary), handle, indent=2)

    save_metrics_text(text_path, summary)

    print("\nSaved:")
    print(f"  {per_sample_path}")
    print(f"  {json_path}")
    print(f"  {text_path}")
    print("\nOverall metrics (B compared with A):")
    for key, label, unit in (
        ("position_3d_error_m", "3D position", "m"),
        ("position_2d_error_m", "2D position", "m"),
        ("yaw_error_deg", "Yaw", "deg"),
    ):
        block = summary["metrics"][key]
        print(
            f"  {label}: RMSE={block['rmse']:.4f} {unit}, "
            f"MAE={block['mae']:.4f} {unit}, "
            f"P95={block['p95_abs']:.4f} {unit}, "
            f"MAX={block['max_abs']:.4f} {unit}"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
