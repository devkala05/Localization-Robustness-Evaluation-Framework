from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np

from .trajectory import interpolate_positions, interpolate_yaw, load_tum, umeyama_align, wrap_angle_rad, yaw_from_quat


def _stats(values: np.ndarray) -> Dict[str, float]:
    return {
        "rmse": float(np.sqrt(np.mean(values * values))),
        "mean": float(np.mean(np.abs(values))),
        "median": float(np.median(np.abs(values))),
        "p95": float(np.percentile(np.abs(values), 95)),
        "max": float(np.max(np.abs(values))),
    }


def evaluate(
    golden_tum: str | Path,
    run_tum: str | Path,
    output_dir: str | Path,
    algorithm: str,
    sequence: str,
    scenario: str,
    perturbation_params: Dict[str, Any],
    failure_threshold_m: float = 5.0,
    tracking_loss_threshold_m: float = 10.0,
    plot_dpi: int = 150,
) -> Dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    plots = output / "plots"
    plots.mkdir(exist_ok=True)

    golden = load_tum(golden_tum)
    run = load_tum(run_tum)
    target_pos = interpolate_positions(golden, run[:, 0])
    target_yaw = interpolate_yaw(golden, run[:, 0])
    aligned_pos, _, _ = umeyama_align(run[:, 1:4], target_pos, allow_translation=False)

    delta = aligned_pos - target_pos
    heading = np.column_stack([np.cos(target_yaw), np.sin(target_yaw), np.zeros_like(target_yaw)])
    lateral_axis = np.column_stack([-np.sin(target_yaw), np.cos(target_yaw), np.zeros_like(target_yaw)])
    longitudinal = np.sum(delta * heading, axis=1)
    lateral = np.sum(delta * lateral_axis, axis=1)
    vertical = delta[:, 2]
    pos3d = np.linalg.norm(delta, axis=1)
    run_yaw = yaw_from_quat(run[:, 4:8])
    yaw_deg = np.degrees(wrap_angle_rad(run_yaw - target_yaw))
    orient_deg = np.abs(yaw_deg)

    jumps = np.linalg.norm(np.diff(aligned_pos, axis=0), axis=1)
    tracking_loss_events = int(np.sum(jumps > tracking_loss_threshold_m))
    failure_idx = np.flatnonzero(pos3d > failure_threshold_m)
    duration = float(run[-1, 0] - run[0, 0]) if len(run) > 1 else 0.0
    drift_rate = float(pos3d[-1] / duration) if duration > 0 else 0.0

    stat_inputs = {
        "longitudinal_m": longitudinal,
        "lateral_m": lateral,
        "vertical_m": vertical,
        "yaw_deg": yaw_deg,
        "orientation_deg": orient_deg,
        "position_3d_m": pos3d,
    }
    all_stats = {name: _stats(values) for name, values in stat_inputs.items()}
    metrics = {
        "status": "SUCCESS",
        "algorithm": algorithm,
        "sequence": sequence,
        "scenario": scenario,
        "perturbation_params": perturbation_params,
        "duration_seconds": duration,
        "num_poses": int(len(run)),
        "rmse": {k: v["rmse"] for k, v in all_stats.items()},
        "mean": {k: v["mean"] for k, v in all_stats.items()},
        "median": {k: v["median"] for k, v in all_stats.items()},
        "max": {k: v["max"] for k, v in all_stats.items()},
        "p95": {k: v["p95"] for k, v in all_stats.items()},
        "drift_rate_m_per_s": drift_rate,
        "time_to_failure_s": None if len(failure_idx) == 0 else float(run[failure_idx[0], 0] - run[0, 0]),
        "failure_threshold_m": failure_threshold_m,
        "tracking_lost": bool(tracking_loss_events > 0),
        "tracking_loss_events": tracking_loss_events,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    (output / "metrics.json").write_text(json.dumps(metrics, indent=2))
    _write_report(output / "deviation_report.txt", metrics, all_stats)
    _plot_trajectory(plots / "trajectory_comparison.png", target_pos, aligned_pos, pos3d, plot_dpi)
    _plot_error_time(plots / "error_vs_time.png", run[:, 0] - run[0, 0], longitudinal, lateral, yaw_deg, pos3d, plot_dpi)
    _plot_lat_lon(plots / "lateral_longitudinal_error.png", lateral, longitudinal, run[:, 0] - run[0, 0], plot_dpi)
    _plot_heatmap(plots / "error_heatmap.png", aligned_pos, pos3d, plot_dpi)
    return metrics


def failed_metrics(output_dir: str | Path, algorithm: str, sequence: str, scenario: str, reason: str) -> Dict[str, Any]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    payload = {
        "status": reason,
        "algorithm": algorithm,
        "sequence": sequence,
        "scenario": scenario,
        "duration_seconds": None,
        "num_poses": 0,
        "rmse": {},
        "mean": {},
        "median": {},
        "max": {},
        "p95": {},
        "tracking_lost": True,
        "tracking_loss_events": None,
    }
    (Path(output_dir) / "metrics.json").write_text(json.dumps(payload, indent=2))
    return payload


def _write_report(path: Path, metrics: Dict[str, Any], stats: Dict[str, Dict[str, float]]) -> None:
    lines = [
        "===========================================================",
        "LOCALIZATION DEVIATION REPORT",
        "===========================================================",
        f"Algorithm  : {metrics['algorithm']}",
        f"Sequence   : {metrics['sequence']}",
        f"Scenario   : {metrics['scenario']}",
        f"Run date   : {metrics['generated_at']}",
        f"Duration   : {metrics['duration_seconds']:.1f} s | {metrics['num_poses']} pose estimates",
        "===========================================================",
        "",
        "ERROR BREAKDOWN",
        "---------------",
        "                  RMSE    Mean    Median   P95     Max",
    ]
    labels = [
        ("Longitudinal (m)", "longitudinal_m"),
        ("Lateral (m)", "lateral_m"),
        ("Vertical (m)", "vertical_m"),
        ("Yaw (deg)", "yaw_deg"),
        ("3D Position (m)", "position_3d_m"),
    ]
    for label, key in labels:
        s = stats[key]
        lines.append(f"{label:17}: {s['rmse']:<7.3f} {s['mean']:<7.3f} {s['median']:<7.3f} {s['p95']:<7.3f} {s['max']:<7.3f}")
    lines.extend([
        "",
        "TEMPORAL ANALYSIS",
        "-----------------",
        f"Drift rate        : {metrics['drift_rate_m_per_s']:.5f} m/s",
        f"Time to {metrics['failure_threshold_m']}m error  : {metrics['time_to_failure_s'] if metrics['time_to_failure_s'] is not None else 'not reached'}",
        f"Tracking losses   : {metrics['tracking_loss_events']}",
        "===========================================================",
    ])
    path.write_text("\n".join(lines) + "\n")


def _plot_trajectory(path: Path, golden: np.ndarray, run: np.ndarray, error: np.ndarray, dpi: int) -> None:
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(golden[:, 0], golden[:, 1], color="white", linewidth=1.5, label="golden")
    sc = ax.scatter(run[:, 0], run[:, 1], c=error, cmap="plasma", s=8, label="test")
    for idx in np.argsort(error)[-5:]:
        ax.scatter(run[idx, 0], run[idx, 1], s=120, facecolors="none", edgecolors="cyan", linewidths=1.0)
    ax.set_title("Trajectory Comparison")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.axis("equal")
    fig.colorbar(sc, ax=ax, label="3D error (m)")
    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    plt.close(fig)


def _plot_error_time(path: Path, t: np.ndarray, longitudinal: np.ndarray, lateral: np.ndarray, yaw: np.ndarray, pos3d: np.ndarray, dpi: int) -> None:
    plt.style.use("dark_background")
    fig, axes = plt.subplots(4, 1, figsize=(9, 8), sharex=True)
    series = [(longitudinal, "Longitudinal (m)"), (lateral, "Lateral (m)"), (yaw, "Yaw (deg)"), (pos3d, "3D position (m)")]
    for ax, (values, label) in zip(axes, series):
        ax.plot(t, values, color="tab:orange", linewidth=1.0)
        ax.set_ylabel(label)
        ax.grid(alpha=0.25)
    axes[-1].set_xlabel("time (s)")
    fig.suptitle("Error vs Time")
    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    plt.close(fig)


def _plot_lat_lon(path: Path, lateral: np.ndarray, longitudinal: np.ndarray, t: np.ndarray, dpi: int) -> None:
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(6, 6))
    sc = ax.scatter(lateral, longitudinal, c=t, cmap="viridis", s=8)
    ax.axhline(0, color="white", alpha=0.25)
    ax.axvline(0, color="white", alpha=0.25)
    ax.set_xlabel("lateral error (m)")
    ax.set_ylabel("longitudinal error (m)")
    ax.set_title("Lateral vs Longitudinal Error")
    fig.colorbar(sc, ax=ax, label="time (s)")
    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    plt.close(fig)


def _plot_heatmap(path: Path, pos: np.ndarray, error: np.ndarray, dpi: int) -> None:
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(8, 5))
    hb = ax.hexbin(pos[:, 0], pos[:, 1], C=error, gridsize=45, cmap="plasma", reduce_C_function=np.mean)
    ax.plot(pos[:, 0], pos[:, 1], color="white", alpha=0.35, linewidth=0.8)
    ax.axis("equal")
    ax.set_title("Spatial Error Heatmap")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    fig.colorbar(hb, ax=ax, label="mean 3D error (m)")
    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
