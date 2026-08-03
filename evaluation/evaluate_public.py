#!/usr/bin/env python3
"""Evaluate one public-dataset trajectory using the E2O association/alignment math."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from evaluate_e2o import associate, load_trajectory, metrics_for, quat_to_matrix, umeyama


DEFAULT_MAX_ATE_FRACTION = 0.02
DEFAULT_MIN_ATE_LIMIT_M = 1.0
DEFAULT_MAX_ATE_M = 15.0
DEFAULT_MIN_ASSOCIATIONS = 20
DEFAULT_MIN_DURATION_COVERAGE = 0.80


def travelled_distance(positions):
    positions = np.asarray(positions, dtype=float)
    if len(positions) < 2:
        return 0.0
    return float(np.linalg.norm(np.diff(positions, axis=0), axis=1).sum())


def assess_quality(result, max_ate_fraction=DEFAULT_MAX_ATE_FRACTION,
                   min_ate_limit_m=DEFAULT_MIN_ATE_LIMIT_M,
                   max_ate_m=DEFAULT_MAX_ATE_M,
                   min_associations=DEFAULT_MIN_ASSOCIATIONS,
                   min_duration_coverage=DEFAULT_MIN_DURATION_COVERAGE):
    """Apply the public-driving accuracy acceptance policy.

    RMSE is bounded by 2% of associated reference distance, with a 1 m floor,
    and peak ATE has an absolute 15 m ceiling. The normalized bound makes routes
    comparable while the peak bound prevents long routes from hiding local
    failures. A declared Sim(3) evaluation may fit one global scale, but that
    transform remains an evaluation artifact and is never estimator input.
    """
    reasons = []
    completion = result.get("completion", {})
    if completion.get("status") != "completed":
        reasons.append("execution did not complete")
    if not result.get("valid"):
        reasons.append("trajectory evaluation is invalid")
    associations = int(result.get("associations", 0))
    if associations < min_associations:
        reasons.append(f"matched poses {associations} < {min_associations}")
    reference_duration = float(result.get("reference_duration_sec", 0.0))
    trajectory_duration = float(result.get("trajectory_duration_sec", 0.0))
    duration_coverage = (trajectory_duration / reference_duration
                         if reference_duration > 0.0 else 0.0)
    if reference_duration > 0.0 and duration_coverage < min_duration_coverage:
        reasons.append(
            f"trajectory duration coverage {duration_coverage:.1%} < "
            f"{min_duration_coverage:.1%}"
        )
    reference_distance = float(result.get("reference_distance_m", 0.0))
    ate_rmse = result.get("ate_m", {}).get("rmse")
    ate_max = result.get("ate_m", {}).get("max")
    limit = max(float(min_ate_limit_m), float(max_ate_fraction) * reference_distance)
    if ate_rmse is None or not math.isfinite(float(ate_rmse)):
        reasons.append("ATE RMSE is missing or non-finite")
    elif float(ate_rmse) > limit:
        reasons.append(f"ATE RMSE {float(ate_rmse):.4f} m > {limit:.4f} m limit")
    if ate_max is None or not math.isfinite(float(ate_max)):
        reasons.append("maximum ATE is missing or non-finite")
    elif float(ate_max) > float(max_ate_m):
        reasons.append(
            f"maximum ATE {float(ate_max):.4f} m > {float(max_ate_m):.4f} m ceiling"
        )
    alignment = str(result.get("alignment", "se3")).lower()
    scale_fitting_allowed = alignment == "sim3"
    return {
        "accepted": not reasons,
        "status": "accepted" if not reasons else "rejected",
        "reasons": reasons,
        "policy": {
            "metric": f"{alignment.upper()} ATE RMSE",
            "max_ate_fraction_of_matched_reference_distance": float(max_ate_fraction),
            "min_ate_limit_m": float(min_ate_limit_m),
            "effective_ate_limit_m": limit,
            "max_ate_m": float(max_ate_m),
            "min_associations": int(min_associations),
            "min_duration_coverage": float(min_duration_coverage),
            "duration_coverage": duration_coverage,
            "scale_fitting_allowed": scale_fitting_allowed,
        },
    }


def matrix_to_quaternion(matrix):
    trace = float(np.trace(matrix))
    if trace > 0:
        s = math.sqrt(trace + 1.0) * 2
        q = np.array([(matrix[2, 1]-matrix[1, 2])/s, (matrix[0, 2]-matrix[2, 0])/s,
                      (matrix[1, 0]-matrix[0, 1])/s, 0.25*s])
    else:
        index = int(np.argmax(np.diag(matrix)))
        if index == 0:
            s = math.sqrt(1+matrix[0, 0]-matrix[1, 1]-matrix[2, 2])*2
            q = np.array([.25*s, (matrix[0, 1]+matrix[1, 0])/s,
                          (matrix[0, 2]+matrix[2, 0])/s, (matrix[2, 1]-matrix[1, 2])/s])
        elif index == 1:
            s = math.sqrt(1+matrix[1, 1]-matrix[0, 0]-matrix[2, 2])*2
            q = np.array([(matrix[0, 1]+matrix[1, 0])/s, .25*s,
                          (matrix[1, 2]+matrix[2, 1])/s, (matrix[0, 2]-matrix[2, 0])/s])
        else:
            s = math.sqrt(1+matrix[2, 2]-matrix[0, 0]-matrix[1, 1])*2
            q = np.array([(matrix[0, 2]+matrix[2, 0])/s,
                          (matrix[1, 2]+matrix[2, 1])/s, .25*s,
                          (matrix[1, 0]-matrix[0, 1])/s])
    return q / np.linalg.norm(q)


def wrapped_degrees(value):
    return math.degrees(math.atan2(math.sin(value), math.cos(value)))


def completion(run_dir: Path):
    path = run_dir / "execution_status.json"
    if not path.is_file():
        return {"status": "unknown", "reason": "execution_status.json missing"}
    return json.loads(path.read_text(encoding="utf-8"))


def file_identity(path: Path):
    """Return immutable provenance for an evaluation input artifact."""
    resolved = path.resolve()
    digest = hashlib.sha256()
    with resolved.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    stat = resolved.stat()
    return {
        "path": str(resolved),
        "sha256": digest.hexdigest(),
        "size_bytes": stat.st_size,
    }


def crop_trajectory(data, start_time, duration):
    """Return a timestamp-windowed trajectory without modifying source data."""
    stamps = np.asarray(data["stamp"])
    mask = stamps >= float(start_time)
    if duration > 0.0:
        mask &= stamps <= float(start_time) + float(duration)
    return {
        key: (np.asarray(value)[mask] if len(value) == len(stamps) else value)
        for key, value in data.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--gt", required=True, type=Path)
    parser.add_argument("--trajectory", required=True, type=Path)
    parser.add_argument("--algorithm", required=True)
    parser.add_argument("--alignment", choices=("se3", "sim3"), default="se3")
    parser.add_argument("--alignment-reason", default="metric sensor mode; scale observable")
    parser.add_argument("--max-association-dt", type=float, default=0.05)
    parser.add_argument("--rpe-delta-sec", type=float, default=1.0)
    parser.add_argument("--max-ate-fraction", type=float, default=DEFAULT_MAX_ATE_FRACTION)
    parser.add_argument("--min-ate-limit-m", type=float, default=DEFAULT_MIN_ATE_LIMIT_M)
    parser.add_argument("--max-ate-m", type=float, default=DEFAULT_MAX_ATE_M)
    parser.add_argument("--min-associations", type=int, default=DEFAULT_MIN_ASSOCIATIONS)
    parser.add_argument("--min-duration-coverage", type=float,
                        default=DEFAULT_MIN_DURATION_COVERAGE)
    parser.add_argument("--eval-start-offset", type=float, default=0.0)
    parser.add_argument("--eval-duration", type=float, default=0.0)
    parser.add_argument("--sequence-start-time", type=float)
    parser.add_argument("--sequence-duration", type=float, default=0.0)
    args = parser.parse_args()
    if args.alignment == "sim3" and not args.alignment_reason.strip():
        parser.error("Sim(3) requires --alignment-reason")

    run_dir = args.run_dir.resolve()
    report_dir = run_dir / "evaluation"
    report_dir.mkdir(parents=True, exist_ok=True)
    # A rerun must never leave a successful-looking plot from an older input.
    for artifact in ("aligned_trajectory.csv", "error_over_time.png",
                     "trajectory_comparison.png", "final_trajectory.csv",
                     "native_trajectory.csv", "ground_truth.csv",
                     "metrics.json", "report.md"):
        (report_dir / artifact).unlink(missing_ok=True)
    reference_path = args.gt.resolve()
    trajectory_path = args.trajectory.resolve()
    reference_identity = file_identity(reference_path)
    trajectory_identity = file_identity(trajectory_path)
    gt = load_trajectory(reference_path)
    est = load_trajectory(trajectory_path)
    if args.eval_start_offset < 0.0 or args.eval_duration < 0.0:
        parser.error("evaluation start offset and duration must be non-negative")
    sequence_start = (float(args.sequence_start_time) if args.sequence_start_time is not None
                      else float(gt["stamp"][0]))
    eval_start = sequence_start + args.eval_start_offset
    effective_duration = args.eval_duration
    if effective_duration <= 0.0 and args.sequence_duration > 0.0:
        effective_duration = max(0.0, args.sequence_duration - args.eval_start_offset)
    if (args.sequence_start_time is not None or args.eval_start_offset > 0.0 or
            args.eval_duration > 0.0):
        gt = crop_trajectory(gt, eval_start, effective_duration)
        est = crop_trajectory(est, eval_start, effective_duration)
    result_window = {
        "sequence_start_time": sequence_start,
        "start_offset_sec": args.eval_start_offset,
        "duration_sec": effective_duration,
        "requested_duration_sec": args.eval_duration,
        "warmup_excluded": args.eval_start_offset > 0.0,
    }
    result, _ = metrics_for(gt, est, args.alignment, args.max_association_dt,
                            args.rpe_delta_sec, evaluate_orientation=True)
    result["alignment_reason"] = args.alignment_reason
    result["evaluation_window"] = result_window
    result["algorithm"] = args.algorithm
    result["completion"] = completion(run_dir)
    result["trajectory_duration_sec"] = (float(est["stamp"][-1] - est["stamp"][0])
                                         if len(est["stamp"]) > 1 else 0.0)
    result["reference_duration_sec"] = (float(gt["stamp"][-1] - gt["stamp"][0])
                                        if len(gt["stamp"]) > 1 else 0.0)
    if "ate_m" in result:
        result["ate_m"]["mae"] = result["ate_m"]["mean"]

    gi, ei = associate(gt, est, args.max_association_dt)
    result["reference_distance_m"] = travelled_distance(gt["position"][gi])
    result["estimated_distance_m"] = travelled_distance(est["position"][ei])
    if result["reference_distance_m"] > 0.0 and result.get("ate_m", {}).get("rmse") is not None:
        result["ate_rmse_fraction_of_reference_distance"] = (
            float(result["ate_m"]["rmse"]) / result["reference_distance_m"]
        )
    errors = np.empty(0)
    yaw_errors = []
    aligned_positions = np.empty((0, 3))
    aligned_quaternions = np.empty((0, 4))
    if result.get("valid"):
        gt_p, est_p = gt["position"][gi], est["position"][ei]
        scale, rotation, translation = umeyama(est_p, gt_p, args.alignment == "sim3")
        aligned_positions = (scale * (rotation @ est_p.T)).T + translation
        errors = np.linalg.norm(aligned_positions - gt_p, axis=1)
        aligned_rotations = [rotation @ quat_to_matrix(est["quaternion"][index]) for index in ei]
        aligned_quaternions = np.asarray([matrix_to_quaternion(item) for item in aligned_rotations])
        for gidx, est_rotation in zip(gi, aligned_rotations):
            gt_rotation = quat_to_matrix(gt["quaternion"][gidx])
            gt_yaw = math.atan2(gt_rotation[1, 0], gt_rotation[0, 0])
            est_yaw = math.atan2(est_rotation[1, 0], est_rotation[0, 0])
            yaw_errors.append(wrapped_degrees(est_yaw - gt_yaw))
        yaw_abs = np.abs(np.asarray(yaw_errors))
        result["yaw_error_deg"] = {
            "rmse": float(np.sqrt(np.mean(np.square(yaw_errors)))),
            "mae": float(np.mean(yaw_abs)), "median": float(np.median(yaw_abs)),
            "p95": float(np.percentile(yaw_abs, 95)), "max": float(np.max(yaw_abs)),
        }

    shutil.copyfile(reference_path, report_dir / "ground_truth.csv")
    # Preserve the estimator's untouched native output separately. Alignment
    # is an evaluation-only operation and is never fed back to the estimator.
    shutil.copyfile(trajectory_path, report_dir / "native_trajectory.csv")
    with (report_dir / "aligned_trajectory.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["timestamp_s", "gt_timestamp_s", "x_m", "y_m", "z_m",
                         "qx", "qy", "qz", "qw", "position_error_m", "yaw_error_deg"])
        # A failed association is still a legitimate execution artifact.  Keep
        # the CSV header, but do not index the deliberately empty aligned arrays.
        aligned_pairs = zip(gi, ei) if result.get("valid") else ()
        for n, (gidx, eidx) in enumerate(aligned_pairs):
            writer.writerow([est["stamp"][eidx], gt["stamp"][gidx], *aligned_positions[n],
                             *aligned_quaternions[n], errors[n], yaw_errors[n]])
    # The final trajectory is exactly the aligned/scaled series used by the
    # plots. Keeping this distinct from native_trajectory.csv avoids presenting
    # an old or unscaled estimator snapshot as the plotted result.
    shutil.copyfile(report_dir / "aligned_trajectory.csv",
                    report_dir / "final_trajectory.csv")

    if len(errors):
        relative_time = est["stamp"][ei] - est["stamp"][ei][0]
        plt.figure(figsize=(11, 4.5))
        plt.plot(relative_time, errors)
        plt.xlabel("trajectory time [s]"); plt.ylabel("ATE [m]"); plt.grid(True)
        plt.tight_layout(); plt.savefig(report_dir / "error_over_time.png", dpi=160); plt.close()
        plt.figure(figsize=(9, 8))
        plt.plot(gt["position"][gi, 0], gt["position"][gi, 1], label="Ground truth")
        plt.plot(aligned_positions[:, 0], aligned_positions[:, 1], label=args.algorithm)
        plt.axis("equal"); plt.grid(True); plt.legend(); plt.tight_layout()
        plt.savefig(report_dir / "trajectory_comparison.png", dpi=160); plt.close()

    native_identity = file_identity(report_dir / "native_trajectory.csv")
    aligned_identity = file_identity(report_dir / "aligned_trajectory.csv")
    plotted_identity = file_identity(report_dir / "final_trajectory.csv")
    payload = {
        "reference": reference_identity,
        "trajectory": trajectory_identity,
        "native_trajectory_snapshot": {
            **native_identity,
            "identical_to_trajectory": (
                native_identity["sha256"] == trajectory_identity["sha256"]
            ),
        },
        "plotted_trajectory_snapshot": {
            **plotted_identity,
            "alignment_applied": args.alignment,
            "identical_to_aligned_trajectory": (
                plotted_identity["sha256"] == aligned_identity["sha256"]
            ),
        },
        "metrics": result,
    }
    (report_dir / "metrics.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    quality = assess_quality(
        result, args.max_ate_fraction, args.min_ate_limit_m, args.max_ate_m,
        args.min_associations, args.min_duration_coverage
    )
    (run_dir / "quality_status.json").write_text(
        json.dumps(quality, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    accepted_marker = run_dir / "VALIDATION_ACCEPTED"
    rejected_marker = run_dir / "VALIDATION_REJECTED"
    accepted_marker.unlink(missing_ok=True)
    rejected_marker.unlink(missing_ok=True)
    marker = accepted_marker if quality["accepted"] else rejected_marker
    marker.write_text(
        f"Automatic public-benchmark quality gate: {quality['status']}.\n"
        + ("\n".join(quality["reasons"]) + "\n" if quality["reasons"] else ""),
        encoding="utf-8",
    )
    lines = [f"# {args.algorithm} evaluation", "", f"Completion: `{result['completion'].get('status')}`",
             "", f"Accuracy gate: `{quality['status']}`", "",
             f"Alignment: `{args.alignment}` — {args.alignment_reason}", "", "```json",
             json.dumps(result, indent=2, sort_keys=True), "```", ""]
    (report_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(report_dir)
    return 0 if quality["accepted"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
