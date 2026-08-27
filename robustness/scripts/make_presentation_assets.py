#!/usr/bin/env python3
"""Create slide-ready figures from the validated ALIVE robustness metrics."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ALGORITHMS = ["FAST-LIVO2", "FAST-LIO2", "LVI-SAM", "FLOAM", "ORB-SLAM3", "RTAB-Map"]
SCENARIOS = ["Baseline", "Rain", "Fog", "Sensor Degradation"]
COLORS = {"Baseline": "#264653", "Rain": "#e76f51", "Fog": "#457b9d", "Sensor Degradation": "#f4a261"}


def read_metrics(path: Path) -> dict:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    return {(row["algorithm"], row["scenario"]): row for row in rows}


def as_float(row: dict, key: str):
    value = row.get(key, "")
    return None if value in ("", "None", "nan") else float(value)


def style(axis, title: str, ylabel: str):
    axis.set_title(title, loc="left", fontweight="bold")
    axis.set_ylabel(ylabel)
    axis.grid(axis="y", alpha=0.25)
    axis.spines[["top", "right"]].set_visible(False)


def make_rmse(metrics: dict, output: Path):
    fig, axis = plt.subplots(figsize=(12, 6.5), constrained_layout=True)
    x = np.arange(len(ALGORITHMS))
    width = 0.19
    for index, scenario in enumerate(SCENARIOS):
        values = [as_float(metrics[(algorithm, scenario)], "overall_rmse_m") or np.nan for algorithm in ALGORITHMS]
        bars = axis.bar(x + (index - 1.5) * width, values, width, label=scenario, color=COLORS[scenario])
        for bar, algorithm in zip(bars, ALGORITHMS):
            row = metrics[(algorithm, scenario)]
            if row.get("localization_failure") == "True":
                bar.set_hatch("///")
                bar.set_edgecolor("#222222")
    axis.set_xticks(x, ALGORITHMS, rotation=18, ha="right")
    style(axis, "ALIVE robustness: absolute 3D RMSE", "3D RMSE [m]")
    axis.legend(ncol=4, frameon=False, loc="upper left")
    axis.text(0.99, 0.98, "Hatched bars = failure/dropout criterion", transform=axis.transAxes,
              ha="right", va="top", fontsize=9)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def make_degradation(metrics: dict, output: Path):
    fig, axis = plt.subplots(figsize=(11, 6.5), constrained_layout=True)
    x = np.arange(len(ALGORITHMS))
    width = 0.24
    for index, scenario in enumerate(SCENARIOS[1:]):
        values = [as_float(metrics[(algorithm, scenario)], "degradation_percent") or 0.0 for algorithm in ALGORITHMS]
        bars = axis.bar(x + (index - 1) * width, values, width, label=scenario, color=COLORS[scenario])
        for bar, algorithm in zip(bars, ALGORITHMS):
            if metrics[(algorithm, scenario)].get("localization_failure") == "True":
                bar.set_hatch("///")
                bar.set_edgecolor("#222222")
    axis.axhline(0.0, color="#333333", linewidth=0.8)
    axis.set_xticks(x, ALGORITHMS, rotation=18, ha="right")
    style(axis, "Perturbation effect relative to clean baseline", "3D RMSE change [%]")
    axis.legend(frameon=False, ncol=3, loc="upper left")
    axis.text(0.99, 0.98, "Negative values are replay score differences, not claimed improvements", transform=axis.transAxes,
              ha="right", va="top", fontsize=9)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def make_status(metrics: dict, output: Path):
    fig, axis = plt.subplots(figsize=(10, 4.8), constrained_layout=True)
    statuses = np.zeros((len(ALGORITHMS), len(SCENARIOS)))
    for i, algorithm in enumerate(ALGORITHMS):
        for j, scenario in enumerate(SCENARIOS):
            row = metrics[(algorithm, scenario)]
            statuses[i, j] = 1 if row.get("localization_failure") == "True" else 0
    image = axis.imshow(statuses, cmap=matplotlib.colors.ListedColormap(["#2a9d8f", "#d62828"]), vmin=0, vmax=1, aspect="auto")
    for i in range(len(ALGORITHMS)):
        for j in range(len(SCENARIOS)):
            axis.text(j, i, "FAIL" if statuses[i, j] else "OK", ha="center", va="center",
                      color="white", fontweight="bold", fontsize=11)
    axis.set_xticks(range(len(SCENARIOS)), SCENARIOS, rotation=20, ha="right")
    axis.set_yticks(range(len(ALGORITHMS)), ALGORITHMS)
    axis.set_title("Localization outcome across the campaign", loc="left", fontweight="bold")
    axis.set_xlabel("Condition")
    axis.set_ylabel("Algorithm")
    axis.tick_params(length=0)
    for spine in axis.spines.values():
        spine.set_visible(False)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def make_timeline(config: dict, output: Path):
    fig, axis = plt.subplots(figsize=(11, 3.8), constrained_layout=True)
    intervals = [("Rain", config["scenarios"]["rain"], "#e76f51"),
                 ("Fog", config["scenarios"]["fog"], "#457b9d"),
                 ("Sensor degradation", config["scenarios"]["sensor_degradation"], "#f4a261")]
    for y, (name, item, color) in enumerate(intervals):
        start, end = float(item["start_time"]), float(item["end_time"])
        axis.barh(y, end - start, left=start, height=0.5, color=color, alpha=0.9)
        axis.text((start + end) / 2, y, f"{name}  {start:.0f}–{end:.0f} s", ha="center", va="center", color="white", fontweight="bold")
    axis.set_yticks(range(3), ["Rain", "Fog", "Sensor degradation"])
    axis.set_xlabel("Seconds from bag start")
    axis.set_title("Controlled live-perturbation intervals", loc="left", fontweight="bold")
    axis.grid(axis="x", alpha=0.25)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.tick_params(axis="y", length=0)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    metrics = read_metrics(args.metrics)
    config = json.loads(json.dumps(__import__("yaml").safe_load(args.config.read_text(encoding="utf-8"))))
    make_rmse(metrics, args.output / "absolute_3d_rmse.png")
    make_degradation(metrics, args.output / "relative_degradation.png")
    make_status(metrics, args.output / "localization_status.png")
    make_timeline(config, args.output / "perturbation_timeline.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
