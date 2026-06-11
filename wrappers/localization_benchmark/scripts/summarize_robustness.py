#!/usr/bin/env python3
import argparse
import glob
import json
import os


def load_metric(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    overall = data.get("overall") or {}
    score = data.get("robustness_score_lower_is_better")
    if score is None:
        pos = overall.get("position_rmse_m") or 0.0
        yaw = overall.get("yaw_rmse_rad") or 0.0
        score = pos + 10.0 * yaw
    return {
        "case": os.path.basename(os.path.dirname(path)),
        "score": score,
        "position_rmse_m": overall.get("position_rmse_m"),
        "position_max_m": overall.get("position_max_m"),
        "yaw_rmse_rad": overall.get("yaw_rmse_rad"),
        "samples": overall.get("samples", 0),
    }


def fmt(value):
    if value is None:
        return "n/a"
    return f"{value:.6f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rows = []
    for metrics_path in glob.glob(os.path.join(args.results_root, "per_*_fast_lio2_*", "metrics.json")):
        row = load_metric(metrics_path)
        if row:
            rows.append(row)
    rows.sort(key=lambda row: row["score"])

    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write("FAST-LIO2 robustness ranking\n")
        handle.write("Lower score is more robust. Score = position_RMSE_m + 10 * yaw_RMSE_rad.\n\n")
        for idx, row in enumerate(rows, start=1):
            handle.write(
                f"{idx}. {row['case']} "
                f"score={fmt(row['score'])} "
                f"position_rmse_m={fmt(row['position_rmse_m'])} "
                f"position_max_m={fmt(row['position_max_m'])} "
                f"yaw_rmse_rad={fmt(row['yaw_rmse_rad'])} "
                f"samples={row['samples']}\n"
            )


if __name__ == "__main__":
    main()
