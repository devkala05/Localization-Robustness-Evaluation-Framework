#!/usr/bin/env python3
"""Aggregate ALIVE baseline/perturbation runs using one fixed SE(3) method."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Dict, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import yaml

import sys
REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY / "evaluation"))
from evaluate_e2o import associate, load_trajectory, quat_to_matrix, umeyama  # noqa: E402


SCENARIOS = ("baseline", "rain", "fog", "sensor_degradation")
DISPLAY_SCENARIOS = {
    "baseline": "Baseline", "rain": "Rain", "fog": "Fog",
    "sensor_degradation": "Sensor Degradation",
}
DISPLAY_ALGORITHMS = {
    "fastlivo2": "FAST-LIVO2", "fastlio2": "FAST-LIO2", "lvisam": "LVI-SAM",
    "floam": "FLOAM", "orbslam3": "ORB-SLAM3", "rtabmap": "RTAB-Map",
}
SENSOR_CLASSES = {
    "fastlivo2": "LiDAR-camera-IMU", "fastlio2": "LiDAR-IMU",
    "lvisam": "LiDAR-IMU (visual branch disabled by campaign default)",
    "floam": "LiDAR-only", "orbslam3": "visual RGB-D",
    "rtabmap": "LiDAR-IMU ICP/graph",
}


def yaw(matrix: np.ndarray) -> float:
    return math.atan2(matrix[1, 0], matrix[0, 0])


def wrapped_degrees(angle: float) -> float:
    return math.degrees(math.atan2(math.sin(angle), math.cos(angle)))


def longest_bad_episode(stamps: np.ndarray, bad: np.ndarray, gap_limit: float) -> float:
    longest = current = 0.0
    for index in range(1, len(stamps)):
        if bad[index - 1] and bad[index] and stamps[index] - stamps[index - 1] <= gap_limit:
            current += stamps[index] - stamps[index - 1]
            longest = max(longest, current)
        else:
            current = 0.0
    return float(longest)


def recovery_time(stamps: np.ndarray, errors: np.ndarray, interval_end: float,
                  threshold: float, hold: float, limit: float) -> Optional[float]:
    candidates = np.flatnonzero((stamps >= interval_end) & (stamps <= interval_end + limit))
    for index in candidates:
        end_time = stamps[index] + hold
        held = (stamps >= stamps[index]) & (stamps <= end_time)
        if held.sum() >= 2 and stamps[held][-1] >= end_time - 0.2 and np.all(errors[held] <= threshold):
            return float(max(0.0, stamps[index] - interval_end))
    return None


def evaluate_pair(gt: dict, est: dict, max_dt: float, bag_start: float,
                  interval: Tuple[float, float], policy: dict) -> Tuple[dict, dict]:
    gi, ei = associate(gt, est, max_dt)
    if len(gi) < 3:
        return {"valid": False, "reason": "fewer_than_3_associations", "associations": int(len(gi))}, {}
    gt_p, est_p = gt["position"][gi], est["position"][ei]
    scale, rotation, translation = umeyama(est_p, gt_p, with_scale=False)
    aligned = (rotation @ est_p.T).T + translation
    residual = aligned - gt_p
    error_3d = np.linalg.norm(residual, axis=1)
    error_xy = np.linalg.norm(residual[:, :2], axis=1)
    yaw_error = np.asarray([
        wrapped_degrees(yaw(rotation @ quat_to_matrix(est["quaternion"][e])) -
                        yaw(quat_to_matrix(gt["quaternion"][g])))
        for g, e in zip(gi, ei)
    ])
    relative_stamps = est["stamp"][ei] - bag_start
    gaps = np.diff(est["stamp"])
    dropout_gap = float(policy["dropout_gap_threshold_s"])
    dropout_gaps = gaps[gaps > dropout_gap]
    failure_threshold = float(policy["failure_error_threshold_m"])
    failure_duration = longest_bad_episode(relative_stamps, error_3d > failure_threshold, dropout_gap)
    perturb_start, perturb_end = interval
    trajectory_ends_early = bool(relative_stamps[-1] < perturb_end)
    recovery = recovery_time(
        relative_stamps, error_3d, perturb_end,
        float(policy["recovery_error_threshold_m"]),
        float(policy["recovery_hold_duration_s"]),
        float(policy["recovery_search_limit_s"]),
    )
    metrics = {
        "valid": True,
        "alignment": "se3",
        "alignment_scale": scale,
        "associations": int(len(gi)),
        "x_rmse_m": float(np.sqrt(np.mean(residual[:, 0] ** 2))),
        "y_rmse_m": float(np.sqrt(np.mean(residual[:, 1] ** 2))),
        "z_rmse_m": float(np.sqrt(np.mean(residual[:, 2] ** 2))),
        "xy_rmse_m": float(np.sqrt(np.mean(error_xy ** 2))),
        "overall_rmse_m": float(np.sqrt(np.mean(error_3d ** 2))),
        "yaw_rmse_deg": float(np.sqrt(np.mean(yaw_error ** 2))),
        "maximum_trajectory_error_m": float(np.max(error_3d)),
        "trajectory_start_relative_s": float(relative_stamps[0]),
        "trajectory_end_relative_s": float(relative_stamps[-1]),
        "maximum_output_gap_s": float(np.max(gaps)) if len(gaps) else None,
        "dropout_gap_count": int(len(dropout_gaps)),
        "longest_failure_episode_s": failure_duration,
        "localization_failure": bool(
            trajectory_ends_early or
            failure_duration >= float(policy["failure_minimum_duration_s"]) or
            (len(dropout_gaps) and float(np.max(dropout_gaps)) >= dropout_gap)
        ),
        "recovered": recovery is not None,
        "recovery_time_s": recovery,
    }
    samples = {
        "timestamp_relative_s": relative_stamps,
        "timestamp_absolute_s": est["stamp"][ei],
        "x_error_m": residual[:, 0], "y_error_m": residual[:, 1], "z_error_m": residual[:, 2],
        "xy_error_m": error_xy, "overall_error_m": error_3d, "yaw_error_deg": yaw_error,
    }
    return metrics, samples


def metadata(path: Path) -> dict:
    values = {}
    metadata_path = path / "run_metadata.env"
    if metadata_path.is_file():
        for line in metadata_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "=" in line:
                key, value = line.split("=", 1); values[key] = value
    return values


def select_run(results_root: Path, algorithm: str, scenario: str) -> Optional[Path]:
    root = results_root / algorithm
    if not root.is_dir():
        return None
    candidates = [path for path in root.iterdir() if path.is_dir() and
                  metadata(path).get("perturbation_scenario", "baseline") == scenario]
    return sorted(candidates, key=lambda item: item.stat().st_mtime)[-1] if candidates else None


def write_samples(path: Path, samples: dict) -> None:
    keys = list(samples)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow(keys)
        writer.writerows(zip(*(samples[key] for key in keys)))


def degradation(value: Optional[float], baseline: Optional[float]) -> Optional[float]:
    if value is None or baseline is None or baseline <= 1.0e-12:
        return None
    return 100.0 * (value - baseline) / baseline


def percent(value: Optional[float]) -> str:
    """Avoid misleading '-0.0%' after rounding small measured changes."""
    if value is None:
        return "N/A"
    if abs(value) < 0.05:
        return f"{value:+.2f}%"
    return f"{value:+.1f}%"


def fmt(value: Optional[float], suffix: str = "") -> str:
    return "N/A" if value is None or not math.isfinite(value) else f"{value:.3f}{suffix}"


def plot_algorithm(algorithm: str, records: dict, intervals: dict, output: Path) -> None:
    figure, axes = plt.subplots(4, 1, figsize=(12, 11), sharex=True)
    baseline_samples = records.get("baseline", {}).get("samples", {})
    for axis, scenario in zip(axes, SCENARIOS):
        samples = records.get(scenario, {}).get("samples", {})
        if baseline_samples:
            axis.plot(baseline_samples["timestamp_relative_s"], baseline_samples["overall_error_m"],
                      color="0.65", linewidth=1.0, label="clean baseline")
        if samples:
            axis.plot(samples["timestamp_relative_s"], samples["overall_error_m"],
                      color="#1259a7", linewidth=1.2, label=DISPLAY_SCENARIOS[scenario])
        if scenario != "baseline":
            start, end = intervals[scenario]
            axis.axvspan(start, end, color="#d95f02", alpha=0.20, label="perturbed interval")
            axis.axvline(end, color="#d95f02", linestyle="--", linewidth=0.8)
        axis.set_ylabel("3D error [m]"); axis.set_title(DISPLAY_SCENARIOS[scenario]); axis.grid(True, alpha=0.3)
        handles, labels = axis.get_legend_handles_labels()
        if handles:
            axis.legend(loc="upper right")
    axes[-1].set_xlabel("time from bag start [s]")
    figure.suptitle(f"{DISPLAY_ALGORITHMS[algorithm]}: before → perturbation → recovery")
    figure.tight_layout(); figure.savefig(output, dpi=180); plt.close(figure)


def make_analysis(all_metrics: dict) -> str:
    complete = all(
        all(all_metrics.get(algorithm, {}).get(scenario, {}).get("valid", False) for scenario in SCENARIOS)
        for algorithm in DISPLAY_ALGORITHMS
    )
    if not complete:
        missing = [f"{DISPLAY_ALGORITHMS[a]} / {DISPLAY_SCENARIOS[s]}" for a in DISPLAY_ALGORITHMS
                   for s in SCENARIOS if not all_metrics.get(a, {}).get(s, {}).get("valid", False)]
        return "\n".join([
            "# Research Analysis", "",
            "No robustness conclusion is reported because the campaign is incomplete or contains invalid trajectories.", "",
            "Missing/invalid pairs:", "", *[f"- {item}" for item in missing], "",
            "This guard prevents process completion or absent outputs from being presented as localization evidence.",
        ])
    # A lower RMSE in a one-off perturbed replay is not evidence that a system
    # improved: small scan-selection/timing differences can change a globally
    # aligned score.  More importantly, a trajectory flagged as failed cannot
    # be ranked as robust merely because its RMSE happens to decrease.
    operational = [a for a in DISPLAY_ALGORITHMS if not any(
        all_metrics[a][s].get("localization_failure", False) for s in SCENARIOS
    )]
    failed = [a for a in DISPLAY_ALGORITHMS if a not in operational]
    worst_change = {
        a: max(degradation(all_metrics[a][s]["overall_rmse_m"],
                           all_metrics[a]["baseline"]["overall_rmse_m"])
               for s in SCENARIOS[1:])
        for a in operational
    }
    most_stable = min(operational, key=worst_change.get)
    best_baseline = min(operational, key=lambda a: all_metrics[a]["baseline"]["overall_rmse_m"])
    lines = ["# Research Analysis", "",
             "All statements below are generated only from valid campaign artifacts. Results are one replay per condition; a negative change is reported as a score difference, not an improvement claim.", "",
             "## Overall robustness", "",
             f"Among systems without a configured localization failure, **{DISPLAY_ALGORITHMS[most_stable]}** has the smallest worst-case relative 3D-RMSE change ({percent(worst_change[most_stable])}). "
             f"**{DISPLAY_ALGORITHMS[best_baseline]}** has the lowest clean-baseline 3D RMSE ({all_metrics[best_baseline]['baseline']['overall_rmse_m']:.3f} m), but its worst perturbation increase is {percent(worst_change[best_baseline])}.", ""]
    if failed:
        lines += [f"**{', '.join(DISPLAY_ALGORITHMS[a] for a in failed)}** is excluded from the robustness ranking: the configured failure/dropout criterion was triggered in every condition, and recovery was not detected. Its RMSE values remain reported as failure evidence, not as a robustness win.", ""]
    for scenario in SCENARIOS[1:]:
        changes = {a: degradation(all_metrics[a][scenario]["overall_rmse_m"],
                                  all_metrics[a]["baseline"]["overall_rmse_m"])
                   for a in operational}
        least = min(changes, key=changes.get)
        most = max(changes, key=changes.get)
        lines += [f"## {DISPLAY_SCENARIOS[scenario]}", "",
                  f"Smallest score change among operational systems: **{DISPLAY_ALGORITHMS[least]}** ({percent(changes[least])}). "
                  f"Largest increase: **{DISPLAY_ALGORITHMS[most]}** ({percent(changes[most])}).", ""]
    lines += ["## Sensor dependency and recovery", ""]
    for algorithm in DISPLAY_ALGORITHMS:
        recovery = ", ".join(
            f"{DISPLAY_SCENARIOS[s]}: " + (fmt(all_metrics[algorithm][s]["recovery_time_s"], " s")
             if all_metrics[algorithm][s]["recovered"] else "not recovered") for s in SCENARIOS[1:])
        lines.append(f"- **{DISPLAY_ALGORITHMS[algorithm]}** ({SENSOR_CLASSES[algorithm]}): {recovery}.")
    lines += ["", "Rain and fog directly attack LiDAR returns, while fog additionally attacks image contrast/depth. "
              "The sensor-disturbance case directly attacks IMU/GNSS; the configured standalone FLOAM and visual RGB-D modes do not consume GNSS/IMU, so any change there must be interpreted alongside run-to-run determinism rather than attributed to those unused topics."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=REPOSITORY / "robustness/config/alive_perturbations.yaml", type=Path)
    parser.add_argument("--results-root", default=REPOSITORY / "results/alive/one_full_loop", type=Path)
    parser.add_argument("--output", default=REPOSITORY / "robustness/results/latest", type=Path)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    evaluation = config["evaluation"]
    gt = load_trajectory(Path(evaluation["ground_truth"]))
    if not len(gt["stamp"]):
        raise SystemExit("reference trajectory contains no readable poses")
    bag_start = float(evaluation.get("bag_start_time_s", gt["stamp"][0]))
    intervals = {"baseline": (0.0, 0.0)}
    intervals.update({name: (float(config["scenarios"][name]["start_time"]),
                             float(config["scenarios"][name]["end_time"])) for name in SCENARIOS[1:]})
    args.output.mkdir(parents=True, exist_ok=True)
    all_metrics: Dict[str, Dict[str, dict]] = {}
    records: Dict[str, Dict[str, dict]] = {}
    for algorithm in config["algorithms"]:
        all_metrics[algorithm] = {}; records[algorithm] = {}
        for scenario in SCENARIOS:
            run_dir = select_run(args.results_root, algorithm, scenario)
            trajectory_path = run_dir / f"{algorithm}_trajectory.csv" if run_dir else None
            if trajectory_path is None or not trajectory_path.is_file():
                metrics, samples = {"valid": False, "reason": "run_or_trajectory_missing"}, {}
            else:
                metrics, samples = evaluate_pair(
                    gt, load_trajectory(trajectory_path),
                    float(evaluation["max_association_difference_s"]), bag_start,
                    intervals[scenario], evaluation,
                )
                metrics["run_directory"] = str(run_dir.resolve())
                metrics["trajectory"] = str(trajectory_path.resolve())
            all_metrics[algorithm][scenario] = metrics
            records[algorithm][scenario] = {"metrics": metrics, "samples": samples}
            if samples:
                write_samples(args.output / f"{algorithm}_{scenario}_per_sample_errors.csv", samples)
        baseline = all_metrics[algorithm]["baseline"].get("overall_rmse_m")
        for scenario in SCENARIOS[1:]:
            all_metrics[algorithm][scenario]["overall_rmse_degradation_percent"] = degradation(
                all_metrics[algorithm][scenario].get("overall_rmse_m"), baseline)
        plot_algorithm(algorithm, records[algorithm], intervals, args.output / f"{algorithm}_error_vs_time.png")

    (args.output / "robustness_metrics.json").write_text(
        json.dumps(all_metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    detailed_header = ["algorithm", "scenario", "x_rmse_m", "y_rmse_m", "z_rmse_m", "xy_rmse_m",
                       "overall_rmse_m", "yaw_rmse_deg", "degradation_percent", "maximum_error_m",
                       "localization_failure", "recovered", "recovery_time_s"]
    with (args.output / "detailed_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow(detailed_header)
        for algorithm in config["algorithms"]:
            for scenario in SCENARIOS:
                item = all_metrics[algorithm][scenario]
                writer.writerow([DISPLAY_ALGORITHMS[algorithm], DISPLAY_SCENARIOS[scenario],
                                 item.get("x_rmse_m"), item.get("y_rmse_m"), item.get("z_rmse_m"),
                                 item.get("xy_rmse_m"), item.get("overall_rmse_m"), item.get("yaw_rmse_deg"),
                                 item.get("overall_rmse_degradation_percent"), item.get("maximum_trajectory_error_m"),
                                 item.get("localization_failure"), item.get("recovered"), item.get("recovery_time_s")])
    detailed = ["# ALIVE Detailed Robustness Metrics", "",
                "All alignments are one global SE(3) fit with no scale fitting.", ""]
    for scenario in SCENARIOS:
        detailed += [f"## {DISPLAY_SCENARIOS[scenario]}", "",
                     "| Algorithm | X RMSE (m) | Y RMSE (m) | Z RMSE (m) | XY RMSE (m) | Overall RMSE (m) | Yaw RMSE (°) | Max error (m) | Degradation | Failure/dropout | Recovery |",
                     "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
        for algorithm in config["algorithms"]:
            item = all_metrics[algorithm][scenario]
            change = item.get("overall_rmse_degradation_percent")
            recovery = item.get("recovery_time_s")
            detailed.append(
                f"| {DISPLAY_ALGORITHMS[algorithm]} | {fmt(item.get('x_rmse_m'))} | "
                f"{fmt(item.get('y_rmse_m'))} | {fmt(item.get('z_rmse_m'))} | "
                f"{fmt(item.get('xy_rmse_m'))} | {fmt(item.get('overall_rmse_m'))} | "
                f"{fmt(item.get('yaw_rmse_deg'))} | {fmt(item.get('maximum_trajectory_error_m'))} | "
                f"{('—' if scenario == 'baseline' else percent(change))} | "
                f"{('YES' if item.get('localization_failure') else 'no') if item.get('valid') else 'N/A'} | "
                f"{('N/A' if recovery is None else f'{recovery:.2f} s')} |"
            )
        detailed.append("")
    (args.output / "detailed_tables.md").write_text("\n".join(detailed), encoding="utf-8")
    table = ["# ALIVE Robustness Comparison", "",
             "Values are 3D RMSE in metres; parentheses give change relative to the clean baseline.", "",
             "| Algorithm | Baseline | Rain | Fog | Sensor Degradation |",
             "|---|---:|---:|---:|---:|"]
    for algorithm in config["algorithms"]:
        values = all_metrics[algorithm]
        cells = [fmt(values["baseline"].get("overall_rmse_m"))]
        changes = []
        for scenario in SCENARIOS[1:]:
            value = values[scenario].get("overall_rmse_m")
            change = values[scenario].get("overall_rmse_degradation_percent")
            changes.append(change)
            if value is None:
                cells.append("N/A")
            else:
                cells.append(f"{value:.3f} ({percent(change)})")
        table.append(f"| {DISPLAY_ALGORITHMS[algorithm]} | {' | '.join(cells)} |")
    (args.output / "comparison_table.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    (args.output / "research_analysis.md").write_text(make_analysis(all_metrics), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
