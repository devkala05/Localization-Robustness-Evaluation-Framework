#!/usr/bin/env python3
"""Evaluate E2O estimator and fused trajectory recordings.

LiDAR/visual-inertial and fused trajectories are aligned with SE(3). Monocular
ORB-SLAM3 is aligned with Sim(3), because its raw trajectory has no guaranteed metric scale.
The report records the provenance and limitations of the selected reference.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

EMPTY = {"stamp": np.empty(0), "position": np.empty((0, 3)), "quaternion": np.empty((0, 4))}


def load_trajectory(path: Path) -> dict:
    if not path.is_file():
        return {key: value.copy() for key, value in EMPTY.items()}
    stamps: List[float] = []
    positions: List[List[float]] = []
    quaternions: List[np.ndarray] = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                stamp_text = row.get("timestamp_s", "").strip()
                stamp = float(stamp_text) if stamp_text else float(row["timestamp_ns"]) * 1.0e-9
                p = [float(row["x_m"]), float(row["y_m"]), float(row.get("z_m", 0.0) or 0.0)]
                q = np.asarray([
                    float(row.get("qx", 0.0) or 0.0), float(row.get("qy", 0.0) or 0.0),
                    float(row.get("qz", 0.0) or 0.0), float(row.get("qw", 1.0) or 1.0),
                ], dtype=float)
                values = np.asarray([stamp] + p + q.tolist(), dtype=float)
                norm = float(np.linalg.norm(q))
                if np.all(np.isfinite(values)) and norm > 1.0e-12:
                    stamps.append(stamp)
                    positions.append(p)
                    quaternions.append(q / norm)
            except (KeyError, TypeError, ValueError):
                continue
    if not stamps:
        return {key: value.copy() for key, value in EMPTY.items()}
    order = np.argsort(np.asarray(stamps, dtype=float))
    return {
        "stamp": np.asarray(stamps, dtype=float)[order],
        "position": np.asarray(positions, dtype=float)[order],
        "quaternion": np.asarray(quaternions, dtype=float)[order],
    }


def read_reference_metadata(path: Path) -> dict:
    metadata = {"path": str(path), "source_method": "unknown", "notes": "", "limitations": []}
    if not path.is_file():
        metadata["limitations"].append("reference_file_missing")
        return metadata
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            row = next(csv.DictReader(handle))
        metadata["source_method"] = row.get("source_method", "unknown")
        metadata["notes"] = row.get("notes", "")
    except (StopIteration, OSError):
        metadata["limitations"].append("reference_metadata_unreadable")
        return metadata
    source = metadata["source_method"].lower()
    notes = metadata["notes"].lower()
    if "fastlivo" in source or "no_external_gt" in notes:
        metadata["limitations"].append(
            "FAST-LIVO2-derived reference is not independent and must not be used to claim FAST-LIVO2 accuracy."
        )
    if "img_en=0" in notes or "lio_mode" in notes:
        metadata["limitations"].append(
            "This reference was produced in LiDAR-IMU mode with vision disabled, not by the current full LiDAR-visual-inertial configuration."
        )
    if "gps" in source:
        metadata["limitations"].append(
            "GPS-ENU reference has meter-level uncertainty and does not provide trustworthy orientation/yaw."
        )
    metadata["limitations"].append("Neither included reference is survey-grade ground truth.")
    return metadata


def associate(gt: dict, est: dict, max_dt: float) -> Tuple[np.ndarray, np.ndarray]:
    if len(gt["stamp"]) == 0 or len(est["stamp"]) == 0:
        return np.empty(0, dtype=int), np.empty(0, dtype=int)
    gt_idx: List[int] = []
    est_idx: List[int] = []
    last_gt = -1
    for i, stamp in enumerate(est["stamp"]):
        j = int(np.searchsorted(gt["stamp"], stamp))
        candidates = [k for k in (j - 1, j) if last_gt < k < len(gt["stamp"])]
        if not candidates:
            continue
        best = min(candidates, key=lambda k: abs(gt["stamp"][k] - stamp))
        if abs(gt["stamp"][best] - stamp) <= max_dt:
            gt_idx.append(best)
            est_idx.append(i)
            last_gt = best
    return np.asarray(gt_idx, dtype=int), np.asarray(est_idx, dtype=int)


def umeyama(source: np.ndarray, target: np.ndarray, with_scale: bool) -> Tuple[float, np.ndarray, np.ndarray]:
    if len(source) < 3:
        raise ValueError("at least three associated poses are required")
    src_mean = source.mean(axis=0)
    dst_mean = target.mean(axis=0)
    src = source - src_mean
    dst = target - dst_mean
    covariance = (dst.T @ src) / len(source)
    U, singular, Vt = np.linalg.svd(covariance)
    S = np.eye(3)
    if np.linalg.det(U @ Vt) < 0.0:
        S[2, 2] = -1.0
    rotation = U @ S @ Vt
    variance = float(np.mean(np.sum(src * src, axis=1)))
    if variance <= 1.0e-12:
        raise ValueError("reference trajectory has insufficient motion")
    scale = float(np.sum(singular * np.diag(S)) / variance) if with_scale else 1.0
    translation = dst_mean - scale * (rotation @ src_mean)
    return scale, rotation, translation


def quat_to_matrix(q: np.ndarray) -> np.ndarray:
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([
        [1 - 2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)],
    ])


def rotation_error(rotation: np.ndarray) -> float:
    return math.acos(max(-1.0, min(1.0, (float(np.trace(rotation)) - 1.0) * 0.5)))


def metrics_for(gt: dict, est: dict, mode: str, max_dt: float, rpe_delta_sec: float,
                evaluate_orientation: bool = True) -> Tuple[dict, Optional[np.ndarray]]:
    gi, ei = associate(gt, est, max_dt)
    if len(gi) < 3:
        return {"valid": False, "reason": "fewer_than_3_associations", "associations": int(len(gi))}, None
    gt_p = gt["position"][gi]
    est_p = est["position"][ei]
    try:
        scale, rotation, translation = umeyama(est_p, gt_p, with_scale=(mode == "sim3"))
    except ValueError as exc:
        return {"valid": False, "reason": str(exc), "associations": int(len(gi))}, None
    aligned = (scale * (rotation @ est_p.T)).T + translation
    errors = np.linalg.norm(aligned - gt_p, axis=1)

    rpe_t: List[float] = []
    rpe_r: List[float] = []
    est_stamps = est["stamp"][ei]
    for i in range(len(ei) - 1):
        j = int(np.searchsorted(est_stamps, est_stamps[i] + rpe_delta_sec))
        if j >= len(ei):
            break
        rpe_t.append(float(np.linalg.norm((aligned[j] - aligned[i]) - (gt_p[j] - gt_p[i]))))
        if evaluate_orientation:
            gt_rel = quat_to_matrix(gt["quaternion"][gi[i]]).T @ quat_to_matrix(gt["quaternion"][gi[j]])
            est_rel = (rotation @ quat_to_matrix(est["quaternion"][ei[i]])).T @ (
                rotation @ quat_to_matrix(est["quaternion"][ei[j]])
            )
            rpe_r.append(rotation_error(gt_rel.T @ est_rel))

    return {
        "valid": True,
        "alignment": mode,
        "alignment_scale": scale,
        "associations": int(len(errors)),
        "association_max_dt_sec": max_dt,
        "ate_m": {
            "rmse": float(np.sqrt(np.mean(errors ** 2))),
            "mean": float(np.mean(errors)),
            "median": float(np.median(errors)),
            "p95": float(np.percentile(errors, 95)),
            "max": float(np.max(errors)),
        },
        "rpe_translation_m": {
            "rmse": float(np.sqrt(np.mean(np.square(rpe_t)))) if rpe_t else None,
            "mean": float(np.mean(rpe_t)) if rpe_t else None,
            "count": len(rpe_t),
            "delta_sec": rpe_delta_sec,
        },
        "rpe_rotation_deg": {
            "evaluated": evaluate_orientation,
            "rmse": math.degrees(float(np.sqrt(np.mean(np.square(rpe_r))))) if rpe_r else None,
            "mean": math.degrees(float(np.mean(rpe_r))) if rpe_r else None,
            "count": len(rpe_r),
            "delta_sec": rpe_delta_sec,
        },
    }, aligned


def load_timeline(path: Path) -> List[dict]:
    if not path.is_file():
        return []
    items: List[dict] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return items


def analyze_timeline(items: List[dict]) -> dict:
    status = [item for item in items if item.get("topic") == "/fused_localization/status"]
    events = [item.get("data", {}) for item in items if item.get("topic") == "/fused_localization/events"]
    durations: Dict[str, float] = {}
    for a, b in zip(status, status[1:]):
        source = str(a.get("data", {}).get("active_source", "none"))
        dt = max(0.0, float(b.get("receipt_time", 0.0)) - float(a.get("receipt_time", 0.0)))
        durations[source] = durations.get(source, 0.0) + dt
    switches = [event for event in events if event.get("event") == "switch"]
    applied_switches = [event for event in events if event.get("event") == "switch_applied"]
    health_items = [item for item in items if item.get("topic") == "/localization_health/summary"]
    sensor_uptime: Dict[str, float] = {}
    estimator_uptime: Dict[str, float] = {}
    if health_items:
        for sensor in ("lidar", "imu", "camera"):
            values = [bool(item.get("data", {}).get("sensors", {}).get(sensor, {}).get("available", False)) for item in health_items]
            sensor_uptime[sensor] = sum(values) / len(values)
        for estimator in ("fast_livo2", "orbslam3", "lvisam"):
            values = [bool(item.get("data", {}).get("estimators", {}).get(estimator, {}).get("healthy", False)) for item in health_items]
            estimator_uptime[estimator] = sum(values) / len(values)
    navigation_items = [item for item in items if item.get("topic") == "/fused_localization/navigation_ok"]
    navigation_ok_fraction = (sum(bool(item.get("data", False)) for item in navigation_items) / len(navigation_items)
                              if navigation_items else None)
    return {
        "source_duration_sec": durations,
        "switch_count": len(switches),
        "switches": switches,
        "applied_switches": applied_switches,
        "max_switch_pose_jump_m": max([float(item.get("pose_jump_m", 0.0)) for item in (applied_switches or switches)], default=0.0),
        "max_switch_orientation_jump_deg": max([float(item.get("orientation_jump_deg", 0.0)) for item in applied_switches], default=0.0),
        "sensor_availability_fraction": sensor_uptime,
        "estimator_healthy_fraction": estimator_uptime,
        "navigation_ok_fraction": navigation_ok_fraction,
    }


def plot_trajectories(gt: dict, aligned: dict, out: Path) -> None:
    if len(gt["position"]) == 0:
        return
    plt.figure(figsize=(10, 8))
    plt.plot(gt["position"][:, 0], gt["position"][:, 1], label="Reference", linewidth=2)
    for name, points in aligned.items():
        if points is not None and len(points):
            plt.plot(points[:, 0], points[:, 1], label=name)
    plt.axis("equal")
    plt.grid(True)
    plt.xlabel("x [m]")
    plt.ylabel("y [m]")
    plt.title("E2O trajectory comparison (time-associated and aligned)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out, dpi=160)
    plt.close()


def plot_source_timeline(items: List[dict], out: Path) -> None:
    status = [item for item in items if item.get("topic") == "/fused_localization/status"]
    if not status:
        return
    t0 = float(status[0].get("receipt_time", 0.0))
    mapping = {"none": 0, "orbslam3": 1, "fast_livo2": 2, "lvisam": 3}
    times = [float(item.get("receipt_time", 0.0)) - t0 for item in status]
    values = [mapping.get(str(item.get("data", {}).get("active_source", "none")), 0) for item in status]
    plt.figure(figsize=(11, 3.5))
    plt.step(times, values, where="post")
    plt.yticks([0, 1, 2, 3], ["failed", "ORB-SLAM3", "FAST-LIVO2", "LVI-SAM"])
    plt.xlabel("time [s]")
    plt.title("Active localization source")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out, dpi=160)
    plt.close()


def plot_health_timeline(items: List[dict], out: Path) -> None:
    health = [item for item in items if item.get("topic") == "/localization_health/summary"]
    if not health:
        return
    t0 = float(health[0].get("receipt_time", 0.0))
    times = [float(item.get("receipt_time", 0.0)) - t0 for item in health]
    series = {
        "FAST-LIVO2 healthy": [bool(item.get("data", {}).get("estimators", {}).get("fast_livo2", {}).get("healthy", False)) for item in health],
        "ORB-SLAM3 healthy": [bool(item.get("data", {}).get("estimators", {}).get("orbslam3", {}).get("healthy", False)) for item in health],
        "LVI-SAM healthy": [bool(item.get("data", {}).get("estimators", {}).get("lvisam", {}).get("healthy", False)) for item in health],
        "LiDAR available": [bool(item.get("data", {}).get("sensors", {}).get("lidar", {}).get("available", False)) for item in health],
        "IMU available": [bool(item.get("data", {}).get("sensors", {}).get("imu", {}).get("available", False)) for item in health],
        "Camera available": [bool(item.get("data", {}).get("sensors", {}).get("camera", {}).get("available", False)) for item in health],
    }
    plt.figure(figsize=(11, 5.5))
    for index, (name, values) in enumerate(series.items()):
        shifted = [index + (0.65 if value else 0.0) for value in values]
        plt.step(times, shifted, where="post", label=name)
    plt.yticks(range(len(series)), list(series.keys()))
    plt.xlabel("time [s]")
    plt.title("Estimator health and sensor availability")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out, dpi=160)
    plt.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--gt", default="data/e2o/ground_truth/one_loop_gps_enu.csv")
    parser.add_argument("--max-association-dt", type=float, default=0.1)
    parser.add_argument("--rpe-delta-sec", type=float, default=1.0)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    gt_path = Path(args.gt).resolve()
    report_dir = run_dir / "evaluation"
    report_dir.mkdir(parents=True, exist_ok=True)
    reference = read_reference_metadata(gt_path)
    gt = load_trajectory(gt_path)
    files = {
        "fast_livo2": run_dir / "fast_livo2_trajectory.csv",
        "orbslam3": run_dir / "orbslam3_trajectory.csv",
        "lvisam": run_dir / "lvisam_trajectory.csv",
        "fused": run_dir / "fused_trajectory.csv",
        "fused_continuous": run_dir / "fused_continuous_trajectory.csv",
        "fused_metric": run_dir / "fused_metric_trajectory.csv",
    }
    trajectories = {name: load_trajectory(path) for name, path in files.items()}
    alignment_modes = {
        "fast_livo2": "se3",
        "orbslam3": "sim3",
        "lvisam": "se3",
        "fused": "se3",
        "fused_continuous": "se3",
        "fused_metric": "se3",
    }
    orientation_trusted = "gps" not in reference["source_method"].lower()
    metrics: Dict[str, dict] = {}
    aligned: Dict[str, Optional[np.ndarray]] = {}
    for name, trajectory in trajectories.items():
        metrics[name], aligned[name] = metrics_for(
            gt, trajectory, alignment_modes[name], args.max_association_dt,
            args.rpe_delta_sec, evaluate_orientation=orientation_trusted,
        )
    timeline_items = load_timeline(run_dir / "localization_timeline.jsonl")
    timeline = analyze_timeline(timeline_items)
    output = {"reference": reference, "metrics": metrics, "fusion_timeline": timeline}
    (report_dir / "metrics.json").write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    plot_trajectories(gt, aligned, report_dir / "trajectory_xy.png")
    plot_source_timeline(timeline_items, report_dir / "source_timeline.png")
    plot_health_timeline(timeline_items, report_dir / "health_sensor_timeline.png")

    lines = ["# E2O Localization Evaluation", "", f"Reference: `{gt_path}`", "",
             f"Source method: `{reference['source_method']}`", "", "## Reference limitations", ""]
    lines.extend([f"- {item}" for item in reference["limitations"]])
    lines.append("")
    for name, result in metrics.items():
        lines += [f"## {name}", "", "```json", json.dumps(result, indent=2), "```", ""]
    lines += ["## Fusion timeline", "", "```json", json.dumps(timeline, indent=2), "```", ""]
    (report_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(report_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
