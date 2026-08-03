#!/usr/bin/env python3
"""Generate the audited complete-local-interval Boreas-RT benchmark report."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import textwrap
from datetime import datetime
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.backends.backend_pdf import PdfPages


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "boreas_rt"
ALGORITHMS = ("fastlio2", "fastlivo2", "lvisam", "orbslam3", "rtabmap")
NAMES = {
    "fastlio2": "FAST-LIO2",
    "fastlivo2": "FAST-LIVO2",
    "lvisam": "LVI-SAM",
    "orbslam3": "ORB-SLAM3",
    "rtabmap": "RTAB-Map",
}
ROUTES = (
    ("Tunnel", "boreas_2024_12_04_14_44", "complete locally downloaded 169.35 s interval"),
    ("Farm", "boreas_2025_07_18_15_30_farm_complete_local", "complete locally downloaded 420.56 s joint-sensor interval"),
    ("Forest", "boreas_2025_07_18_11_53_forest_complete_local", "complete locally downloaded 216.90 s joint-sensor interval"),
    ("Urban", "boreas_2025_08_06_06_33_urban_complete_local", "complete locally downloaded 196.80 s joint-sensor interval"),
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def matches_current_route_window(run: Path, sequence: str) -> bool:
    """Reject accepted artifacts produced for an older manifest window."""
    manifest_path = (
        ROOT / "configs" / "datasets" / "boreas_rt" / sequence / "sequence.yaml"
    )
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    source = manifest["source"]
    metadata = {}
    for line in (run / "run_metadata.env").read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            metadata[key] = value
    expected = {
        "sequence_start_time": float(source["window_start_timestamp_s"]),
        "evaluation_start_offset": float(source.get("evaluation_start_offset_s", 0.0)),
        "evaluation_duration": float(source.get("evaluation_duration_sec", 0.0)),
    }
    try:
        return all(
            abs(float(metadata[key]) - value) < 1.0e-6
            for key, value in expected.items()
        )
    except (KeyError, ValueError):
        return False


def selected_run(route: str, sequence: str, algorithm: str) -> dict:
    pattern = RESULTS / sequence / algorithm
    candidates = [
        item
        for item in pattern.glob("*/evaluation/metrics.json")
        if (item.parent.parent / "VALIDATION_ACCEPTED").is_file()
        and matches_current_route_window(item.parent.parent, sequence)
    ]
    if not candidates:
        raise RuntimeError(f"no accepted run for {route}/{algorithm} in {pattern}")
    metrics_path = max(candidates, key=lambda item: item.stat().st_mtime_ns)
    run = metrics_path.parent.parent
    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    metrics = payload.get("metrics", payload)
    quality = json.loads((run / "quality_status.json").read_text(encoding="utf-8"))
    execution = json.loads((run / "execution_status.json").read_text(encoding="utf-8"))
    if quality.get("status") != "accepted" or execution.get("status") != "completed":
        raise RuntimeError(f"selected run is not accepted and complete: {run}")
    native = run / "evaluation" / "native_trajectory.csv"
    aligned = run / "evaluation" / "aligned_trajectory.csv"
    final = run / "evaluation" / "final_trajectory.csv"
    trajectory = run / f"{algorithm}_trajectory.csv"
    plots = (
        run / "evaluation" / "trajectory_comparison.png",
        run / "evaluation" / "error_over_time.png",
    )
    required = (native, aligned, final, trajectory, *plots)
    missing = [str(item) for item in required if not item.is_file()]
    if missing:
        raise RuntimeError(f"missing artifacts for {route}/{algorithm}: {missing}")
    if digest(native) != digest(trajectory):
        raise RuntimeError(f"native snapshot differs from estimator output: {run}")
    if digest(final) != digest(aligned):
        raise RuntimeError(f"final plotted trajectory is not the aligned output: {run}")
    return {
        "route": route,
        "sequence": sequence,
        "algorithm": algorithm,
        "name": NAMES[algorithm],
        "run": run,
        "metrics": metrics,
        "quality": quality,
        "execution": execution,
        "trajectory_plot": plots[0],
        "error_plot": plots[1],
        "native_sha256": digest(native),
        "final_sha256": digest(final),
        "reproduction": (run / "reproduction_command.txt").read_text(
            encoding="utf-8"
        ).strip(),
    }


def load_records() -> list[dict]:
    return [
        selected_run(route, sequence, algorithm)
        for route, sequence, _ in ROUTES
        for algorithm in ALGORITHMS
    ]


def header(fig, title: str, subtitle: str = "") -> None:
    fig.text(0.055, 0.965, title, fontsize=18, fontweight="bold", va="top",
             color="#16324f")
    if subtitle:
        fig.text(0.055, 0.925, subtitle, fontsize=9, va="top", color="#475467")


def footer(fig, page: int) -> None:
    fig.text(0.055, 0.022, "Boreas-RT complete-local benchmark · accepted native runs only",
             fontsize=7, color="#667085")
    fig.text(0.95, 0.022, str(page), fontsize=7, color="#667085", ha="right")


def table_style(table) -> None:
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.45)
    for (row, _), cell in table.get_celld().items():
        cell.set_edgecolor("#d0d5dd")
        if row == 0:
            cell.set_facecolor("#16324f")
            cell.get_text().set_color("white")
            cell.get_text().set_fontweight("bold")
        elif row % 2 == 0:
            cell.set_facecolor("#f2f4f7")


def scale_value(metrics: dict) -> float:
    value = metrics.get("alignment_scale")
    return 1.0 if value is None else float(value)


def cover(pdf: PdfPages, records: list[dict], page: int) -> None:
    fig = plt.figure(figsize=(11.69, 8.27), facecolor="white")
    fig.text(0.07, 0.82, "Boreas-RT Complete-Local\nLocalization Benchmark",
             fontsize=30, fontweight="bold", color="#16324f", va="top")
    fig.text(0.07, 0.61, "Tunnel · Farm · Forest · Urban\n"
             "Five native algorithms · complete locally downloaded intervals · saved final plots",
             fontsize=14, color="#344054", linespacing=1.5)
    fig.text(0.07, 0.44, f"{len(records)}/20 accepted runs",
             fontsize=23, fontweight="bold", color="#067647")
    scope = (
        "Every metric covers the complete camera/LiDAR-overlap interval currently "
        "stored locally: Tunnel 169.35 s, Farm 420.56 s, Forest 216.90 s, and Urban "
        "196.80 s. These are complete local downloads, not claims of the longer "
        "original cloud traversals. No warm-up or scoring crop is excluded."
    )
    fig.text(0.07, 0.30, "\n".join(textwrap.wrap(scope, 108)), fontsize=11,
             color="#475467", linespacing=1.4)
    fig.text(0.07, 0.09, f"Generated {datetime.now().astimezone():%Y-%m-%d %H:%M %Z}",
             fontsize=8, color="#667085")
    footer(fig, page); pdf.savefig(fig); plt.close(fig)


def matrix_page(pdf: PdfPages, records: list[dict], page: int, metric: str) -> None:
    fig = plt.figure(figsize=(11.69, 8.27), facecolor="white")
    label = "ATE RMSE (m)" if metric == "rmse" else "Maximum ATE (m)"
    header(fig, f"Cross-route {label}",
           "All values come from accepted metrics.json artifacts; lower is better.")
    values = np.asarray([
        [next(r for r in records if r["route"] == route and r["algorithm"] == alg)
         ["metrics"]["ate_m"][metric] for alg in ALGORITHMS]
        for route, _, _ in ROUTES
    ])
    ax = fig.add_axes([0.16, 0.18, 0.76, 0.64])
    image = ax.imshow(values, cmap="YlGn_r", aspect="auto")
    ax.set_xticks(range(len(ALGORITHMS)), [NAMES[item] for item in ALGORITHMS])
    ax.set_yticks(range(len(ROUTES)), [item[0] for item in ROUTES])
    ax.tick_params(axis="x", rotation=18)
    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            ax.text(col, row, f"{values[row, col]:.3f}", ha="center", va="center",
                    fontsize=9, color="black")
    fig.colorbar(image, ax=ax, shrink=0.82, label="metres")
    footer(fig, page); pdf.savefig(fig); plt.close(fig)


def route_page(pdf: PdfPages, records: list[dict], route_info, page: int) -> None:
    route, sequence, scope = route_info
    selected = [r for r in records if r["route"] == route]
    fig = plt.figure(figsize=(11.69, 8.27), facecolor="white")
    header(fig, f"{route} route summary", f"{sequence} · {scope}")
    rows = []
    for item in selected:
        m = item["metrics"]; ate = m["ate_m"]
        rows.append([item["name"], m["alignment"].upper(),
                     f"{scale_value(m):.4f}", str(m["associations"]),
                     f"{ate['rmse']:.3f}", f"{ate['p95']:.3f}", f"{ate['max']:.3f}",
                     f"{m['rpe_translation_m']['rmse']:.3f}"])
    ax = fig.add_axes([0.06, 0.38, 0.88, 0.43]); ax.axis("off")
    table = ax.table(cellText=rows, colLabels=("Algorithm", "Align", "Scale", "Pairs",
                     "RMSE m", "P95 m", "Max m", "RPE m"), loc="center",
                     cellLoc="center")
    table_style(table)
    best = min(selected, key=lambda item: item["metrics"]["ate_m"]["rmse"])
    fig.text(0.07, 0.26, f"Lowest RMSE: {best['name']} "
             f"({best['metrics']['ate_m']['rmse']:.3f} m). All five selected runs "
             "passed completion, coverage, RMSE, and the 15 m absolute maximum gate.",
             fontsize=10, color="#344054")
    footer(fig, page); pdf.savefig(fig); plt.close(fig)


def detail_page(pdf: PdfPages, item: dict, page: int) -> None:
    m = item["metrics"]; ate = m["ate_m"]
    fig = plt.figure(figsize=(11.69, 8.27), facecolor="white")
    header(fig, f"{item['route']} · {item['name']}",
           f"ACCEPTED · {m['alignment'].upper()} · scale {scale_value(m):.5f}")
    left = fig.add_axes([0.04, 0.36, 0.45, 0.49]); right = fig.add_axes([0.51, 0.36, 0.45, 0.49])
    left.imshow(mpimg.imread(item["trajectory_plot"])); right.imshow(mpimg.imread(item["error_plot"]))
    left.axis("off"); right.axis("off")
    left.set_title("Saved final aligned trajectory", fontsize=10)
    right.set_title("Saved error over time", fontsize=10)
    details = (
        f"ATE RMSE / MAE / median / P95 / max: {ate['rmse']:.3f} / "
        f"{ate.get('mae', ate.get('mean')):.3f} / {ate['median']:.3f} / "
        f"{ate['p95']:.3f} / {ate['max']:.3f} m\n"
        f"RPE translation RMSE: {m['rpe_translation_m']['rmse']:.3f} m · "
        f"rotation RMSE: {m['rpe_rotation_deg']['rmse']:.3f} deg · "
        f"pairs: {m['associations']} · duration: {m['trajectory_duration_sec']:.2f} s\n"
        f"Run: {item['run']}\nNative SHA-256: {item['native_sha256']}\n"
        f"Final aligned SHA-256: {item['final_sha256']}\n"
        f"Reproduce: {item['reproduction']}"
    )
    fig.text(0.055, 0.285, details, fontsize=7.3, family="monospace", color="#475467",
             va="top", linespacing=1.35, wrap=True)
    footer(fig, page); pdf.savefig(fig); plt.close(fig)


def methodology(pdf: PdfPages, page: int) -> None:
    fig = plt.figure(figsize=(11.69, 8.27), facecolor="white")
    header(fig, "Methodology and artifact integrity")
    body = """
• Ground truth is available only after estimator shutdown. It is never published to ORB-SLAM3,
  RTAB-Map, FAST-LIO2, FAST-LIVO2, or LVI-SAM.
• Every report row covers the entire locally downloaded camera/LiDAR-overlap interval. There is no
  warm-up exclusion, pre-roll, or fixed scoring crop in this complete-local campaign.
• Metric LiDAR modes use SE(3). Boreas ORB-SLAM3 uses a documented evaluation-only Sim(3) because
  a single camera with sparse projected LiDAR depth retains a global gauge discrepancy. Scale is
  reported for every run and is never fed back to tracking.
• The generator selects only VALIDATION_ACCEPTED runs. It verifies that native_trajectory.csv is
  byte-identical to the estimator CSV and that final_trajectory.csv is byte-identical to
  aligned_trajectory.csv before embedding the saved trajectory comparison.
• Diagnostic, interrupted, rejected, and superseded runs remain on disk for audit but cannot enter
  this report. Each row comes from the matching complete-local route configuration.
• Acceptance requires completed playback, finite monotonic poses, sufficient coverage and
  associations, reasonable RMSE relative to route distance, and maximum ATE no greater than 15 m.
"""
    fig.text(0.07, 0.86, textwrap.dedent(body).strip(), fontsize=10.5,
             color="#344054", va="top", linespacing=1.5)
    footer(fig, page); pdf.savefig(fig); plt.close(fig)


def write_summaries(output_dir: Path, records: list[dict]) -> None:
    rows = []
    for item in records:
        m = item["metrics"]; ate = m["ate_m"]
        rows.append({
            "route": item["route"], "sequence": item["sequence"],
            "algorithm": item["algorithm"], "alignment": m["alignment"],
            "alignment_scale": scale_value(m),
            "associations": m["associations"], "duration_sec": m["trajectory_duration_sec"],
            "ate_rmse_m": ate["rmse"], "ate_p95_m": ate["p95"], "ate_max_m": ate["max"],
            "rpe_translation_rmse_m": m["rpe_translation_m"]["rmse"],
            "run_dir": str(item["run"].resolve()),
            "native_sha256": item["native_sha256"], "final_sha256": item["final_sha256"],
        })
    (output_dir / "Boreas_RT_Four_Route_Results.json").write_text(
        json.dumps({"generated_at": datetime.now().astimezone().isoformat(), "results": rows},
                   indent=2) + "\n", encoding="utf-8")
    with (output_dir / "Boreas_RT_Four_Route_Results.csv").open(
            "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)


def generate(output: Path) -> None:
    records = load_records()
    output.parent.mkdir(parents=True, exist_ok=True)
    write_summaries(output.parent, records)
    with PdfPages(output) as pdf:
        page = 1; cover(pdf, records, page); page += 1
        matrix_page(pdf, records, page, "rmse"); page += 1
        matrix_page(pdf, records, page, "max"); page += 1
        for route in ROUTES:
            route_page(pdf, records, route, page); page += 1
        for route, _, _ in ROUTES:
            for item in (r for r in records if r["route"] == route):
                detail_page(pdf, item, page); page += 1
        methodology(pdf, page)
        info = pdf.infodict()
        info["Title"] = "Boreas-RT Complete-Local-Data Localization Benchmark"
        info["Author"] = "Localization Robustness Evaluation Framework"
        info["Subject"] = "Complete locally downloaded Tunnel, Farm, Forest and Urban localization results"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=(
        RESULTS / "complete_local_benchmark" / "Boreas_RT_Complete_Local_Data_Benchmark_Report.pdf"))
    args = parser.parse_args(); generate(args.output.resolve()); print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
