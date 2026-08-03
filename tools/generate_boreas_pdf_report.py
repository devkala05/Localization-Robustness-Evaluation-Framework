#!/usr/bin/env python3
"""Build a consolidated, provenance-aware PDF for the locked Boreas runs."""
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
from matplotlib.backends.backend_pdf import PdfPages


DISPLAY_NAMES = {
    "fastlio2": "FAST-LIO2",
    "fastlivo2": "FAST-LIVO2",
    "lvisam": "LVI-SAM",
    "orbslam3": "ORB-SLAM3",
    "rtabmap": "RTAB-Map",
}
MODES = {
    "fastlio2": "LiDAR + IMU",
    "fastlivo2": "LiDAR + camera + IMU",
    "lvisam": "LiDAR + IMU (selected stable public-data mode)",
    "orbslam3": "RGB-D (camera + calibrated LiDAR-projected depth)",
    "rtabmap": "LiDAR ICP odometry",
}
ORDER = tuple(DISPLAY_NAMES)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_locked_runs(bundle: Path) -> list[dict]:
    records = []
    for algorithm in ORDER:
        candidates = sorted((bundle / "runs" / algorithm).glob("*/evaluation/metrics.json"))
        if len(candidates) != 1:
            raise RuntimeError(
                f"expected exactly one locked {algorithm} metrics file, found {len(candidates)}"
            )
        metrics_path = candidates[0]
        run_dir = metrics_path.parent.parent
        payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        metrics = payload.get("metrics", payload)
        quality_path = run_dir / "quality_status.json"
        quality = (
            json.loads(quality_path.read_text(encoding="utf-8"))
            if quality_path.is_file()
            else {"status": "accepted", "reasons": []}
        )
        native = run_dir / "evaluation" / "native_trajectory.csv"
        final = run_dir / "evaluation" / "final_trajectory.csv"
        aligned = run_dir / "evaluation" / "aligned_trajectory.csv"
        # The bundle is self-contained. Never validate against an original
        # run path embedded in copied metadata because that source may later
        # be archived or removed.
        trajectory = run_dir / f"{algorithm}_trajectory.csv"
        required = (
            native,
            final,
            aligned,
            run_dir / "evaluation" / "trajectory_comparison.png",
            run_dir / "evaluation" / "error_over_time.png",
            trajectory,
        )
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise RuntimeError(f"{algorithm} missing locked artifacts: {missing}")
        if sha256(native) != sha256(trajectory):
            raise RuntimeError(f"{algorithm} native snapshot does not match estimator trajectory")
        if sha256(final) != sha256(aligned):
            raise RuntimeError(f"{algorithm} final plot source does not match aligned trajectory")
        records.append(
            {
                "algorithm": algorithm,
                "name": DISPLAY_NAMES[algorithm],
                "mode": MODES[algorithm],
                "run_dir": run_dir,
                "metrics": metrics,
                "quality": quality,
                "native_sha256": sha256(native),
                "final_sha256": sha256(final),
                "trajectory_plot": run_dir / "evaluation" / "trajectory_comparison.png",
                "error_plot": run_dir / "evaluation" / "error_over_time.png",
                "reproduction": (
                    (run_dir / "reproduction_command.txt").read_text(encoding="utf-8").strip()
                    if (run_dir / "reproduction_command.txt").is_file()
                    else "not recorded"
                ),
            }
        )
    return records


def compact(value, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f}"


def metric_rows(records: list[dict]) -> list[list[str]]:
    rows = []
    for record in records:
        metric = record["metrics"]
        ate = metric["ate_m"]
        rows.append(
            [
                record["name"],
                record["quality"].get("status", "unknown"),
                metric["alignment"].upper(),
                compact(metric.get("alignment_scale"), 4),
                str(metric["associations"]),
                compact(metric["trajectory_duration_sec"], 2),
                compact(ate["rmse"]),
                compact(ate.get("mae", ate.get("mean"))),
                compact(ate["p95"]),
                compact(ate["max"]),
            ]
        )
    return rows


def add_header(fig, title: str, subtitle: str = "") -> None:
    fig.text(0.055, 0.965, title, fontsize=18, fontweight="bold", va="top")
    if subtitle:
        fig.text(0.055, 0.925, subtitle, fontsize=9.5, color="#44546a", va="top")


def add_footer(fig, page: int) -> None:
    fig.text(
        0.055,
        0.025,
        "Localization Robustness Evaluation Framework · locked native-run artifacts",
        fontsize=7,
        color="#667085",
    )
    fig.text(0.95, 0.025, str(page), fontsize=7, color="#667085", ha="right")


def cover_page(pdf: PdfPages, records: list[dict], page: int) -> None:
    fig = plt.figure(figsize=(11.69, 8.27), facecolor="white")
    fig.text(0.07, 0.82, "Boreas-RT Full-Sequence\nLocalization Benchmark", fontsize=30,
             fontweight="bold", color="#16324f", va="top")
    fig.text(
        0.07,
        0.66,
        "Sequence: boreas-2024-12-04-14-44  ·  Duration: 169.35 s\n"
        "Five algorithms  ·  Native outputs  ·  Full-window evaluation",
        fontsize=14,
        color="#344054",
        linespacing=1.5,
    )
    accepted = sum(r["quality"].get("status") == "accepted" for r in records)
    fig.text(
        0.07,
        0.48,
        f"{accepted}/5 strict quality gates accepted",
        fontsize=22,
        fontweight="bold",
        color="#16794b" if accepted == 5 else "#b54708",
    )
    orb = next(record for record in records if record["algorithm"] == "orbslam3")
    orb_ate = orb["metrics"]["ate_m"]
    status_note = (
        "All five locked full-sequence runs pass the strict quality gates. "
        f"ORB-SLAM3 now records {orb['metrics']['associations']:,} associated poses "
        f"with {orb_ate['rmse']:.2f} m RMSE and {orb_ate['max']:.2f} m maximum ATE, "
        "below the 15.00 m ceiling."
        if accepted == len(records)
        else
        f"{len(records) - accepted} locked run(s) do not pass every strict quality gate; "
        "their status and reasons are reported explicitly."
    )
    fig.text(0.07, 0.39, "\n".join(textwrap.wrap(status_note, 115)), fontsize=11,
             color="#16794b" if accepted == len(records) else "#7a2e0e",
             linespacing=1.3)
    inventory = (
        "The repository contains one complete Boreas-RT sequence, not multiple "
        "separately labelled Boreas scenario datasets. The sequence itself covers "
        "stationary initialization, high-speed motion, turns, exposure changes, "
        "and a lower-motion tail. No unavailable sequences are claimed."
    )
    fig.text(0.07, 0.20, "Local inventory note\n" + "\n".join(textwrap.wrap(inventory, 120)),
             fontsize=10, color="#475467", linespacing=1.45)
    fig.text(0.07, 0.08, f"Generated {datetime.now().astimezone():%Y-%m-%d %H:%M %Z}",
             fontsize=8, color="#667085")
    add_footer(fig, page)
    pdf.savefig(fig)
    plt.close(fig)


def summary_page(pdf: PdfPages, records: list[dict], page: int) -> None:
    fig = plt.figure(figsize=(11.69, 8.27), facecolor="white")
    add_header(
        fig,
        "Executive metrics",
        "ATE values use the full matched trajectory. SE(3) preserves metric scale; "
        "ORB uses documented evaluation-only Sim(3).",
    )
    ax = fig.add_axes([0.045, 0.27, 0.91, 0.56])
    ax.axis("off")
    headers = [
        "Algorithm", "Gate", "Align", "Scale", "Pairs", "Dur. s",
        "RMSE m", "MAE m", "P95 m", "Max m",
    ]
    table = ax.table(
        cellText=metric_rows(records),
        colLabels=headers,
        loc="center",
        cellLoc="center",
        colWidths=[0.13, 0.10, 0.07, 0.08, 0.08, 0.09, 0.09, 0.09, 0.09, 0.09],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1, 1.65)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#d0d5dd")
        if row == 0:
            cell.set_facecolor("#16324f")
            cell.get_text().set_color("white")
            cell.get_text().set_fontweight("bold")
        elif row % 2 == 0:
            cell.set_facecolor("#f2f4f7")
        if row > 0 and col == 1:
            status = table[(row, col)].get_text().get_text()
            table[(row, col)].get_text().set_color(
                "#067647" if status == "accepted" else "#b42318"
            )
            table[(row, col)].get_text().set_fontweight("bold")
    best = min(records, key=lambda record: record["metrics"]["ate_m"]["rmse"])
    all_accepted = all(
        record["quality"].get("status") == "accepted" for record in records
    )
    interpretation = (
        f"Interpretation: {best['name']} has the lowest full-sequence ATE RMSE. "
        + (
            "All five algorithms pass the strict completion and maximum-error gates. "
            "ORB-SLAM3's corrected camera admission preserves Boreas timestamp jitter "
            "without injecting its 50 ms catch-up frames."
            if all_accepted
            else
            "See the Gate column and per-algorithm pages for rejected-run reasons."
        )
    )
    fig.text(
        0.055,
        0.18,
        interpretation,
        fontsize=10,
        color="#344054",
        wrap=True,
    )
    add_footer(fig, page)
    pdf.savefig(fig)
    plt.close(fig)


def comparison_page(pdf: PdfPages, records: list[dict], page: int) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.69, 8.27))
    fig.patch.set_facecolor("white")
    add_header(fig, "Cross-algorithm comparison", "Full-sequence ATE and one-second RPE.")
    names = [record["name"] for record in records]
    rmse = [record["metrics"]["ate_m"]["rmse"] for record in records]
    maximum = [record["metrics"]["ate_m"]["max"] for record in records]
    rpe = [record["metrics"]["rpe_translation_m"]["rmse"] for record in records]
    colors = ["#2e90fa", "#7f56d9", "#12b76a", "#f79009", "#6172f3"]
    y = np.arange(len(names))
    axes[0].barh(y - 0.17, rmse, 0.34, label="ATE RMSE", color=colors)
    axes[0].barh(y + 0.17, maximum, 0.34, label="ATE max", color=colors, alpha=0.43)
    axes[0].axvline(15.0, color="#b42318", linestyle="--", linewidth=1.2,
                    label="15 m max ceiling")
    axes[0].set_yticks(y, names)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("metres")
    axes[0].set_title("Absolute trajectory error")
    axes[0].grid(axis="x", alpha=0.22)
    axes[0].legend(fontsize=8)
    axes[1].barh(y, rpe, color=colors)
    axes[1].set_yticks(y, names)
    axes[1].invert_yaxis()
    axes[1].set_xlabel("metres")
    axes[1].set_title("Translational RPE RMSE (1 s)")
    axes[1].grid(axis="x", alpha=0.22)
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
    plt.subplots_adjust(left=0.13, right=0.96, top=0.82, bottom=0.12, wspace=0.34)
    add_footer(fig, page)
    pdf.savefig(fig)
    plt.close(fig)


def algorithm_page(pdf: PdfPages, record: dict, page: int) -> None:
    metric = record["metrics"]
    ate = metric["ate_m"]
    rpe_t = metric["rpe_translation_m"]
    rpe_r = metric["rpe_rotation_deg"]
    yaw = metric.get("yaw_error_deg", {})
    fig = plt.figure(figsize=(11.69, 8.27), facecolor="white")
    status = record["quality"].get("status", "unknown")
    add_header(
        fig,
        f"{record['name']} · {status.upper()}",
        f"{record['mode']} · {metric['alignment'].upper()} alignment · "
        f"scale {compact(metric.get('alignment_scale'), 5)}",
    )
    ax_traj = fig.add_axes([0.045, 0.39, 0.44, 0.45])
    ax_err = fig.add_axes([0.515, 0.39, 0.44, 0.45])
    ax_traj.imshow(mpimg.imread(record["trajectory_plot"]))
    ax_err.imshow(mpimg.imread(record["error_plot"]))
    ax_traj.axis("off")
    ax_err.axis("off")
    ax_traj.set_title("Saved aligned trajectory plot", fontsize=10)
    ax_err.set_title("Saved error-over-time plot", fontsize=10)
    details = [
        f"ATE RMSE / MAE: {compact(ate['rmse'])} / {compact(ate.get('mae', ate.get('mean')))} m",
        f"ATE median / P95 / max: {compact(ate['median'])} / {compact(ate['p95'])} / {compact(ate['max'])} m",
        f"RPE translation RMSE / mean: {compact(rpe_t['rmse'])} / {compact(rpe_t['mean'])} m",
        f"RPE rotation RMSE / mean: {compact(rpe_r['rmse'])} / {compact(rpe_r['mean'])} deg",
        f"Yaw RMSE / MAE / max: {compact(yaw.get('rmse'))} / {compact(yaw.get('mae'))} / {compact(yaw.get('max'))} deg",
        f"Associations: {metric['associations']} · trajectory/reference: "
        f"{compact(metric['trajectory_duration_sec'], 2)} / {compact(metric['reference_duration_sec'], 2)} s",
        f"Completion: {metric['completion'].get('status')} · poses "
        f"{metric['completion'].get('trajectory_poses', 'n/a')}",
    ]
    fig.text(0.055, 0.31, "\n".join(details), fontsize=8.8, color="#344054",
             va="top", linespacing=1.35)
    reasons = record["quality"].get("reasons") or []
    if reasons:
        fig.text(0.57, 0.31, "Gate reason:\n" + "\n".join(reasons), fontsize=8.8,
                 color="#b42318", va="top", wrap=True)
    fig.text(
        0.055,
        0.11,
        "Native SHA-256: " + record["native_sha256"] + "\n"
        "Final aligned SHA-256: " + record["final_sha256"] + "\n"
        "Run: " + str(record["run_dir"]) + "\n"
        "Reproduce: " + "\n".join(textwrap.wrap(record["reproduction"], 125)),
        fontsize=6.6,
        family="monospace",
        color="#475467",
        va="top",
    )
    add_footer(fig, page)
    pdf.savefig(fig)
    plt.close(fig)


def methodology_page(pdf: PdfPages, records: list[dict], page: int) -> None:
    fig = plt.figure(figsize=(11.69, 8.27), facecolor="white")
    add_header(fig, "Methodology, integrity, and limitations")
    body = """
Dataset and coverage
• Local sequence inventory: boreas-2024-12-04-14-44 only.
• Source duration 169.35 s; 1,694 camera frames; 1,627 LiDAR scans; independent DMU and
  post-processed Applanix POSPac GNSS/INS/wheel reference are present.
• Every selected run starts at offset 0 and covers the complete available sequence.

Evaluation
• FAST-LIO2, FAST-LIVO2, LVI-SAM, and RTAB-Map use SE(3); their sensor modes have observable
  metric scale. ORB-SLAM3 uses one evaluation-only Sim(3) fit because the selected single-camera
  frontend receives sparse projected LiDAR depth and retains a global gauge/scale discrepancy.
• ATE reports RMSE, MAE, median, P95, and maximum. RPE uses a one-second delta. Yaw is reported
  where orientation is meaningful. Association tolerance is recorded in each metrics.json.
• Alignment is evaluation-only and is never fed back to an estimator.

Artifact integrity
• The report generator verifies that evaluation/native_trajectory.csv is byte-identical to the
  selected estimator trajectory and that evaluation/final_trajectory.csv is byte-identical to
  evaluation/aligned_trajectory.csv for all five runs.
• The embedded trajectory and error images are the saved evaluation artifacts from those exact
  locked runs. Diagnostic, partial, and rejected tuning plots are excluded.

Limitations
• The repository does not currently contain additional Boreas-RT sequences, so this report cannot
  claim cross-sequence weather/location coverage. Scenario diversity here means phases within one
  complete route, not multiple separately labelled datasets.
• All five selected full-sequence runs pass the project-specific completion and 15 m maximum ATE
  gates. This does not establish cross-sequence robustness; additional Boreas routes are still
  required before generalizing the result beyond this sequence.
"""
    fig.text(0.065, 0.87, textwrap.dedent(body).strip(), fontsize=10.3, color="#344054",
             va="top", linespacing=1.42)
    add_footer(fig, page)
    pdf.savefig(fig)
    plt.close(fig)


def write_machine_summaries(bundle: Path, records: list[dict]) -> None:
    summary = []
    for record in records:
        metric = record["metrics"]
        summary.append(
            {
                "dataset": "boreas_rt",
                "sequence": "boreas_2024_12_04_14_44",
                "algorithm": record["algorithm"],
                "display_name": record["name"],
                "mode": record["mode"],
                "quality_status": record["quality"].get("status"),
                "quality_reasons": record["quality"].get("reasons", []),
                "alignment": metric["alignment"],
                "alignment_scale": metric.get("alignment_scale"),
                "associations": metric["associations"],
                "trajectory_duration_sec": metric["trajectory_duration_sec"],
                "reference_duration_sec": metric["reference_duration_sec"],
                "ate_m": metric["ate_m"],
                "rpe_translation_m": metric["rpe_translation_m"],
                "rpe_rotation_deg": metric["rpe_rotation_deg"],
                "yaw_error_deg": metric.get("yaw_error_deg"),
                "completion": metric["completion"],
                "run_dir": str(record["run_dir"].resolve()),
                "native_sha256": record["native_sha256"],
                "final_aligned_sha256": record["final_sha256"],
                "reproduction_command": record["reproduction"],
            }
        )
    (bundle / "boreas_full_results.json").write_text(
        json.dumps(
            {
                "dataset": "boreas_rt",
                "local_sequence_count": 1,
                "sequence": "boreas_2024_12_04_14_44",
                "generated_at": datetime.now().astimezone().isoformat(),
                "results": summary,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    fields = [
        "algorithm", "quality_status", "alignment", "alignment_scale", "associations",
        "trajectory_duration_sec", "ate_rmse_m", "ate_mae_m", "ate_median_m",
        "ate_p95_m", "ate_max_m", "rpe_translation_rmse_m", "rpe_rotation_rmse_deg",
        "yaw_rmse_deg", "run_dir",
    ]
    with (bundle / "boreas_full_results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in summary:
            ate = item["ate_m"]
            writer.writerow(
                {
                    "algorithm": item["algorithm"],
                    "quality_status": item["quality_status"],
                    "alignment": item["alignment"],
                    "alignment_scale": item["alignment_scale"],
                    "associations": item["associations"],
                    "trajectory_duration_sec": item["trajectory_duration_sec"],
                    "ate_rmse_m": ate["rmse"],
                    "ate_mae_m": ate.get("mae", ate.get("mean")),
                    "ate_median_m": ate["median"],
                    "ate_p95_m": ate["p95"],
                    "ate_max_m": ate["max"],
                    "rpe_translation_rmse_m": item["rpe_translation_m"]["rmse"],
                    "rpe_rotation_rmse_deg": item["rpe_rotation_deg"]["rmse"],
                    "yaw_rmse_deg": (item["yaw_error_deg"] or {}).get("rmse"),
                    "run_dir": item["run_dir"],
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bundle",
        type=Path,
        default=Path("results/boreas_rt/final_report"),
        help="locked report bundle containing runs/<algorithm>/<run_id>",
    )
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    bundle.mkdir(parents=True, exist_ok=True)
    records = load_locked_runs(bundle)
    write_machine_summaries(bundle, records)
    output = bundle / "Boreas_RT_Full_Benchmark_Report.pdf"
    with PdfPages(output) as pdf:
        page = 1
        cover_page(pdf, records, page); page += 1
        summary_page(pdf, records, page); page += 1
        comparison_page(pdf, records, page); page += 1
        for record in records:
            algorithm_page(pdf, record, page); page += 1
        methodology_page(pdf, records, page)
        metadata = pdf.infodict()
        metadata["Title"] = "Boreas-RT Full-Sequence Localization Benchmark"
        metadata["Author"] = "Localization Robustness Evaluation Framework"
        metadata["Subject"] = "Five-algorithm full-sequence trajectory evaluation"
        metadata["Keywords"] = "Boreas-RT, localization, ATE, RPE, ORB-SLAM3, RTAB-Map"
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
