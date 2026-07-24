#!/usr/bin/env python3
"""Print a Markdown comparison from real public benchmark artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ALGORITHMS = ("fastlio2", "fastlivo2", "orbslam3", "rtabmap", "lvisam")
MAX_ATE_M = 15.0


def best_run(root: Path, algorithm: str, include_unreviewed: bool):
    candidates = []
    for metrics_path in root.joinpath(algorithm).glob("*/evaluation/metrics.json"):
        run_dir = metrics_path.parents[1]
        metadata_path = run_dir / "run_metadata.env"
        phase = "production"
        requested_duration = 0.0
        if metadata_path.is_file():
            for line in metadata_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("phase="):
                    phase = line.partition("=")[2].strip()
                elif line.startswith("duration="):
                    try:
                        requested_duration = float(line.partition("=")[2].strip())
                    except ValueError:
                        requested_duration = 0.0
        # The default table is a full-route production summary. A locally
        # aligned holdout can be diagnostically useful, but must never replace
        # a rejected full trajectory in the final 5x2 result table.
        if not include_unreviewed and phase != "production":
            continue
        # A production run with an explicit duration is also a diagnostic
        # slice, not a full result.
        if not include_unreviewed and phase == "production" and requested_duration > 0.0:
            continue
        if not include_unreviewed:
            quality_path = run_dir / "quality_status.json"
            if quality_path.is_file():
                try:
                    if not json.loads(quality_path.read_text(encoding="utf-8")).get("accepted"):
                        continue
                except json.JSONDecodeError:
                    continue
            elif not (run_dir / "VALIDATION_ACCEPTED").is_file():
                continue
        try:
            payload = json.loads(metrics_path.read_text(encoding="utf-8"))
            metrics = payload["metrics"]
            duration = float(metrics.get("trajectory_duration_sec", 0.0))
            associations = int(metrics.get("associations", 0))
            if (not include_unreviewed and
                    float(metrics.get("ate_m", {}).get("max", float("inf"))) > MAX_ATE_M):
                continue
            if metrics.get("valid") and associations > 0:
                candidates.append((duration, associations, metrics_path, metrics))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
    return max(candidates, default=None, key=lambda item: (item[0], item[1]))


def number(mapping, *keys):
    value = mapping
    try:
        for key in keys:
            value = value[key]
        return f"{float(value):.4f}"
    except (KeyError, TypeError, ValueError):
        return "—"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=Path("results"))
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--sequence", required=True)
    parser.add_argument("--include-unreviewed", action="store_true",
                        help="include technically valid runs not explicitly accepted after log review")
    args = parser.parse_args()
    sequence_root = args.results_root / args.dataset / args.sequence

    print("| Algorithm | Accuracy | Duration (s) | Matched | Distance (m) | ATE RMSE (m) | Max ATE (m) | ATE/Distance | RPE trans. RMSE (m) | Run |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for algorithm in ALGORITHMS:
        selected = best_run(sequence_root, algorithm, args.include_unreviewed)
        if selected is None:
            print(f"| {algorithm} | missing/rejected | — | — | — | — | — | — | — | — |")
            continue
        duration, associations, path, metrics = selected
        quality_path = path.parents[1] / "quality_status.json"
        quality = "unreviewed"
        if quality_path.is_file():
            quality = json.loads(quality_path.read_text(encoding="utf-8")).get("status", "unknown")
        elif (path.parents[1] / "VALIDATION_ACCEPTED").is_file():
            quality = "legacy-accepted"
        run_name = path.parents[1].name
        print(
            f"| {algorithm} | {quality} | {duration:.2f} | {associations} | "
            f"{number(metrics, 'reference_distance_m')} | {number(metrics, 'ate_m', 'rmse')} | "
            f"{number(metrics, 'ate_m', 'max')} | "
            f"{number(metrics, 'ate_rmse_fraction_of_reference_distance')} | "
            f"{number(metrics, 'rpe_translation_m', 'rmse')} | `{run_name}` |"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
