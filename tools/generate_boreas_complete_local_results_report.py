#!/usr/bin/env python3
"""Create an inclusive, presentation-ready report for every complete-local run.

Unlike the acceptance-only report, this generator deliberately includes complete,
rejected, and incomplete runs.  It never invents a metric or a plot for a failed
execution: unavailable values are shown as em dashes and the recorded failure
reason is printed in the corresponding detail page.
"""
from __future__ import annotations

import argparse
import csv
import json
import textwrap
from datetime import datetime
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import ListedColormap


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "boreas_rt"
OUT = RESULTS / "complete_local_benchmark"
ALGORITHMS = ("fastlio2", "fastlivo2", "lvisam", "orbslam3", "rtabmap")
NAMES = {
    "fastlio2": "FAST-LIO2", "fastlivo2": "FAST-LIVO2", "lvisam": "LVI-SAM",
    "orbslam3": "ORB-SLAM3", "rtabmap": "RTAB-Map",
}
ROUTES = (
    ("Tunnel", "boreas_2024_12_04_14_44", 169.35),
    ("Farm", "boreas_2025_07_18_15_30_farm_complete_local", 420.560486),
    ("Forest", "boreas_2025_07_18_11_53_forest_complete_local", 216.900620),
    ("Urban", "boreas_2025_08_06_06_33_urban_complete_local", 196.801987),
)
NAVY = "#102A43"
NAVY_DARK = "#081C33"
TEAL = "#0F766E"
TEAL_LIGHT = "#CCFBF1"
SKY = "#E0F2FE"
INK = "#243B53"
MUTED = "#627D98"
PAPER = "#F8FAFC"
COLORS = {"accepted": "#15803D", "rejected": "#C2410C", "failed": "#B42318"}


def wrap(value: str, width: int = 112) -> str:
    return "\n".join(textwrap.wrap(value, width=width))


def header(fig, title: str, subtitle: str = "") -> None:
    fig.add_artist(plt.Line2D([0.055, 0.945], [0.976, 0.976], color=TEAL, linewidth=3.2))
    fig.text(0.055, 0.958, title, fontsize=18, fontweight="bold", va="top", color=NAVY)
    if subtitle:
        fig.text(0.055, 0.918, subtitle, fontsize=9, va="top", color=MUTED)


def footer(fig, number: int) -> None:
    fig.add_artist(plt.Line2D([0.055, 0.945], [0.047, 0.047], color="#D9E2EC", linewidth=0.7))
    fig.text(0.055, 0.024, "BOREAS-RT  /  COMPLETE-LOCAL EVIDENCE", fontsize=6.8, color=MUTED, fontweight="bold")
    fig.text(0.945, 0.024, f"{number:02d}", fontsize=7.2, color=TEAL, ha="right", fontweight="bold")


def table_style(table) -> None:
    table.auto_set_font_size(False); table.set_fontsize(7.7); table.scale(1, 1.43)
    for (row, _), cell in table.get_celld().items():
        cell.set_edgecolor("#d0d5dd")
        if row == 0:
            cell.set_facecolor(NAVY); cell.get_text().set_color("white")
            cell.get_text().set_fontweight("bold")
        elif row % 2 == 0:
            cell.set_facecolor("#F0F4F8")


def current_run(sequence: str, algorithm: str) -> Path:
    candidates = sorted((RESULTS / sequence / algorithm).glob("*/execution_status.json"),
                        key=lambda item: item.stat().st_mtime_ns)
    if not candidates:
        raise RuntimeError(f"missing run for {sequence}/{algorithm}")
    return candidates[-1].parent


def load_records() -> list[dict]:
    records = []
    for route, sequence, nominal_duration in ROUTES:
        manifest = yaml.safe_load((ROOT / "configs/datasets/boreas_rt" / sequence / "sequence.yaml").read_text())
        source = manifest["source"]
        for algorithm in ALGORITHMS:
            run = current_run(sequence, algorithm)
            execution = json.loads((run / "execution_status.json").read_text())
            quality_path = run / "quality_status.json"
            quality = json.loads(quality_path.read_text()) if quality_path.exists() else None
            metrics_path = run / "evaluation" / "metrics.json"
            metrics = json.loads(metrics_path.read_text()).get("metrics", {}) if metrics_path.exists() else None
            if execution.get("status") != "completed":
                status = "failed"
            elif quality and quality.get("status") == "accepted":
                status = "accepted"
            else:
                status = "rejected"
            records.append({
                "route": route, "sequence": sequence, "nominal_duration": nominal_duration,
                "local_start": source["window_start_timestamp_s"], "status": status,
                "algorithm": algorithm, "name": NAMES[algorithm], "run": run,
                "execution": execution, "quality": quality, "metrics": metrics,
                "trajectory_plot": run / "evaluation" / "trajectory_comparison.png",
                "error_plot": run / "evaluation" / "error_over_time.png",
            })
    return records


def metric(record: dict, field: str) -> float:
    if not record["metrics"]:
        return float("nan")
    return float(record["metrics"]["ate_m"][field])


def reason(record: dict) -> str:
    if record["status"] == "accepted":
        return "Passed completion, coverage, RMSE, and 15 m maximum-error gates."
    if record["quality"]:
        return "; ".join(record["quality"].get("reasons", [])) or "Quality evaluation was not accepted."
    return record["execution"].get("reason", "Execution did not complete.")


def cover(pdf: PdfPages, records: list[dict], page: int) -> None:
    counts = {state: sum(r["status"] == state for r in records) for state in COLORS}
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=NAVY_DARK)
    fig.add_artist(plt.Rectangle((0.0, 0.0), 0.43, 1.0, transform=fig.transFigure, facecolor=TEAL, alpha=0.24, edgecolor="none"))
    fig.add_artist(plt.Rectangle((0.78, 0.72), 0.33, 0.33, transform=fig.transFigure, facecolor="#155E75", alpha=0.42, edgecolor="none"))
    fig.text(0.075, 0.87, "LOCALIZATION ROBUSTNESS\nEVALUATION FRAMEWORK", fontsize=8.5, fontweight="bold", color="#99F6E4", va="top", linespacing=1.35)
    fig.text(0.075, 0.76, "Boreas-RT\nComplete-Local Results", fontsize=31,
             fontweight="bold", color="white", va="top", linespacing=1.13)
    fig.text(0.075, 0.55, "Evidence book · all 20 native executions\nTunnel · Farm · Forest · Urban", fontsize=13,
             color="#D9E2EC", linespacing=1.55)
    x = 0.075
    for state in ("accepted", "rejected", "failed"):
        fig.add_artist(plt.Rectangle((x - 0.012, 0.31), 0.118, 0.12, transform=fig.transFigure,
                                     facecolor="white", alpha=0.96, edgecolor="none"))
        fig.text(x, 0.365, str(counts[state]), fontsize=24, fontweight="bold", color=COLORS[state])
        fig.text(x, 0.33, state.upper(), fontsize=7.2, color=INK, fontweight="bold")
        x += 0.145
    scope = ("Each result uses the full locally stored camera/LiDAR-overlap interval: Tunnel 169.35 s, "
             "Farm 420.56 s, Forest 216.90 s, Urban 196.80 s. The report includes rejected and incomplete "
             "runs rather than hiding them. Missing metrics/plots remain explicitly marked unavailable.")
    fig.text(0.075, 0.19, wrap(scope, 105), fontsize=9.7, color="#D9E2EC", linespacing=1.43)
    fig.text(0.075, 0.075, f"GENERATED {datetime.now().astimezone():%Y-%m-%d %H:%M %Z}", fontsize=7.2, color="#99F6E4", fontweight="bold")
    fig.text(0.925, 0.075, f"{page:02d}", fontsize=8, color="#99F6E4", ha="right", fontweight="bold")
    pdf.savefig(fig); plt.close(fig)


def data_page(pdf: PdfPages, records: list[dict], page: int) -> None:
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=PAPER)
    header(fig, "Dataset scope and evaluation contract", "Full locally downloaded joint-sensor coverage; original cloud traversals may be longer.")
    rows = []
    for route, sequence, duration in ROUTES:
        root = ROOT / "data/datasets/boreas_rt" / yaml.safe_load((ROOT / "configs/datasets/boreas_rt" / sequence / "sequence.yaml").read_text())["display_name"]
        camera = len(list((root / "camera").glob("*.png"))); lidar = len(list((root / "lidar").glob("*.bin")))
        rows.append([route, sequence.replace("boreas_", "")[:26], f"{duration:.2f}", f"{camera:,}", f"{lidar:,}", "camera + LiDAR + DMU + Applanix"])
    ax = fig.add_axes([0.055, 0.48, 0.89, 0.30]); ax.axis("off")
    table = ax.table(cellText=rows, colLabels=("Route", "Source sequence", "Evaluated s", "Camera", "LiDAR", "Inputs"), loc="center", cellLoc="center")
    table_style(table)
    text = ("Playback preserves acquisition timestamps. All five estimators receive only their declared native sensor inputs. "
            "Applanix ground truth is loaded after shutdown for association, alignment, metrics, and saved comparison plots; it is never published to tracking, mapping, deskewing, depth generation, or scale correction.")
    fig.text(0.07, 0.36, wrap(text, 110), fontsize=10.4, color=INK, linespacing=1.45)
    fig.add_artist(plt.Rectangle((0.06, 0.12), 0.88, 0.12, transform=fig.transFigure, facecolor=SKY, edgecolor="#BAE6FD"))
    fig.text(0.075, 0.197, "QUALITY STATUS DEFINITIONS", fontsize=8.2, fontweight="bold", color=TEAL)
    fig.text(0.075, 0.153, "ACCEPTED: completed and passed all gates     REJECTED: completed but failed an accuracy/coverage gate     FAILED: execution/finalization did not complete", fontsize=9.2, color=INK)
    footer(fig, page); pdf.savefig(fig); plt.close(fig)


def status_matrix(pdf: PdfPages, records: list[dict], page: int) -> None:
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=PAPER)
    header(fig, "Execution and quality matrix", "Every completed and incomplete cell is included.")
    value = {"accepted": 2, "rejected": 1, "failed": 0}
    matrix = np.array([[value[next(r for r in records if r["route"] == route and r["algorithm"] == alg)["status"]]
                        for alg in ALGORITHMS] for route, _, _ in ROUTES])
    ax = fig.add_axes([0.16, 0.23, 0.72, 0.55])
    ax.imshow(matrix, cmap=ListedColormap(["#FECACA", "#FED7AA", "#BBF7D0"]), vmin=0, vmax=2, aspect="auto")
    ax.set_xticks(range(5), [NAMES[a] for a in ALGORITHMS], rotation=18)
    ax.set_yticks(range(4), [r[0] for r in ROUTES])
    for row in range(4):
        for col in range(5):
            status = next(r for r in records if r["route"] == ROUTES[row][0] and r["algorithm"] == ALGORITHMS[col])["status"]
            ax.text(col, row, status.upper(), ha="center", va="center", fontsize=8, fontweight="bold", color=NAVY)
    fig.text(0.16, 0.13, "Green = accepted · amber = completed but rejected · red = incomplete execution / unavailable quality metrics", fontsize=9, color=MUTED)
    footer(fig, page); pdf.savefig(fig); plt.close(fig)


def heatmap(pdf: PdfPages, records: list[dict], page: int, field: str, title: str) -> None:
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=PAPER)
    header(fig, title, "Metres. Blank/red cells have no completed evaluation metric; amber text identifies rejected measurements.")
    values = np.array([[metric(next(r for r in records if r["route"] == route and r["algorithm"] == alg), field)
                        for alg in ALGORITHMS] for route, _, _ in ROUTES])
    image = np.ma.masked_invalid(values)
    ax = fig.add_axes([0.16, 0.19, 0.72, 0.62]); im = ax.imshow(image, cmap="YlGnBu_r", aspect="auto")
    ax.set_xticks(range(5), [NAMES[a] for a in ALGORITHMS], rotation=18); ax.set_yticks(range(4), [r[0] for r in ROUTES])
    for row in range(4):
        for col in range(5):
            record = next(r for r in records if r["route"] == ROUTES[row][0] and r["algorithm"] == ALGORITHMS[col])
            value = values[row, col]
            label = "—" if not np.isfinite(value) else f"{value:.2f}"
            ax.text(col, row, label, ha="center", va="center", fontsize=9,
                    fontweight="bold", color=COLORS[record["status"]] if record["status"] != "accepted" else NAVY)
    fig.colorbar(im, ax=ax, shrink=0.82, label="metres")
    footer(fig, page); pdf.savefig(fig); plt.close(fig)


def route_summary(pdf: PdfPages, records: list[dict], route_info: tuple, page: int) -> None:
    route, sequence, duration = route_info
    selected = [r for r in records if r["route"] == route]
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=PAPER)
    header(fig, f"{route} · complete-local summary", f"{duration:.2f} s joint camera/LiDAR interval · {sequence}")
    rows = []
    for r in selected:
        m = r["metrics"] or {}; ate = m.get("ate_m", {})
        rows.append([r["name"], r["status"].upper(), m.get("alignment", "—").upper(), str(m.get("associations", "—")),
                     "—" if not ate else f"{ate['rmse']:.3f}", "—" if not ate else f"{ate['p95']:.3f}", "—" if not ate else f"{ate['max']:.3f}", wrap(reason(r), 52)])
    ax = fig.add_axes([0.04, 0.30, 0.92, 0.56]); ax.axis("off")
    table = ax.table(
        cellText=rows,
        colLabels=("Algorithm", "Status", "Align", "Pairs", "RMSE m", "P95 m", "Max m", "Recorded result"),
        colWidths=(0.13, 0.085, 0.07, 0.055, 0.07, 0.07, 0.07, 0.45),
        loc="center", cellLoc="center",
    )
    table_style(table)
    table.set_fontsize(6.8)
    table.scale(1, 1.22)
    for idx, r in enumerate(selected, start=1):
        table[(idx, 1)].get_text().set_color(COLORS[r["status"]]); table[(idx, 1)].get_text().set_fontweight("bold")
        result_cell = table[(idx, 7)]
        result_cell.get_text().set_ha("left")
        result_cell.get_text().set_wrap(True)
        result_cell.get_text().set_fontsize(6.4)
        lines = rows[idx - 1][7].count("\n") + 1
        if lines > 1:
            for column in range(8):
                table[(idx, column)].set_height(0.102 + 0.022 * (lines - 2))
    finite = [r for r in selected if r["metrics"]]
    if finite:
        best = min(finite, key=lambda r: metric(r, "rmse"))
        fig.text(0.07, 0.20, f"BEST MEASURED RMSE  ·  {best['name']} ({metric(best, 'rmse'):.3f} m)", fontsize=9.5, color=TEAL, fontweight="bold")
    footer(fig, page); pdf.savefig(fig); plt.close(fig)


def detail_page(pdf: PdfPages, record: dict, page: int) -> None:
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=PAPER)
    status = record["status"].upper()
    header(fig, f"{record['route']} · {record['name']}", f"{status} · full locally downloaded interval")
    m = record["metrics"]
    if m and record["trajectory_plot"].is_file() and record["error_plot"].is_file():
        left = fig.add_axes([0.04, 0.37, 0.45, 0.48]); right = fig.add_axes([0.51, 0.37, 0.45, 0.48])
        left.imshow(mpimg.imread(record["trajectory_plot"])); right.imshow(mpimg.imread(record["error_plot"])); left.axis("off"); right.axis("off")
        left.set_title("Saved final aligned trajectory", fontsize=10); right.set_title("Saved error over time", fontsize=10)
        ate = m["ate_m"]
        metric_text = (f"ATE RMSE / P95 / max: {ate['rmse']:.3f} / {ate['p95']:.3f} / {ate['max']:.3f} m · "
                       f"RPE translation RMSE: {m['rpe_translation_m']['rmse']:.3f} m · "
                       f"associations: {m['associations']} · trajectory duration: {m['trajectory_duration_sec']:.2f} s")
    else:
        ax = fig.add_axes([0.09, 0.43, 0.82, 0.28]); ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, facecolor="#FFF1F2", edgecolor="#FECDD3", linewidth=1.5))
        ax.text(0.5, 0.64, "No comparison plot was produced", ha="center", va="center", fontsize=18, fontweight="bold", color="#b42318")
        ax.text(0.5, 0.39, wrap(reason(record), 88), ha="center", va="center", fontsize=10, color="#7a271a")
        metric_text = "Metrics unavailable because the execution/finalization gate did not complete."
    fig.text(0.055, 0.285, f"STATUS  ·  {status}\n{metric_text}\nRECORDED RESULT  ·  {reason(record)}\nRUN DIRECTORY  ·  {record['run']}", fontsize=8.15, color=INK, va="top", linespacing=1.43, wrap=True)
    footer(fig, page); pdf.savefig(fig); plt.close(fig)


def write_summary(records: list[dict]) -> None:
    rows = []
    for r in records:
        m = r["metrics"] or {}; ate = m.get("ate_m", {})
        rows.append({"route": r["route"], "sequence": r["sequence"], "algorithm": r["algorithm"], "status": r["status"],
                     "duration_sec": r["nominal_duration"], "alignment": m.get("alignment"), "associations": m.get("associations"),
                     "ate_rmse_m": ate.get("rmse"), "ate_p95_m": ate.get("p95"), "ate_max_m": ate.get("max"),
                     "reason": reason(r), "run_dir": str(r["run"].resolve())})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "Boreas_RT_Complete_Local_All_Results.json").write_text(json.dumps({"generated_at": datetime.now().astimezone().isoformat(), "results": rows}, indent=2) + "\n")
    with (OUT / "Boreas_RT_Complete_Local_All_Results.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)


def generate(output: Path) -> None:
    records = load_records(); write_summary(records); output.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(output) as pdf:
        page = 1; cover(pdf, records, page); page += 1
        data_page(pdf, records, page); page += 1
        status_matrix(pdf, records, page); page += 1
        heatmap(pdf, records, page, "rmse", "Cross-route ATE RMSE comparison"); page += 1
        heatmap(pdf, records, page, "max", "Cross-route maximum ATE comparison"); page += 1
        for route_info in ROUTES:
            route_summary(pdf, records, route_info, page); page += 1
        for route_info in ROUTES:
            for record in (r for r in records if r["route"] == route_info[0]):
                detail_page(pdf, record, page); page += 1
        info = pdf.infodict(); info["Title"] = "Boreas-RT Complete-Local Results and Evidence Book"
        info["Author"] = "Localization Robustness Evaluation Framework"; info["Subject"] = "All complete-local Boreas runs, including non-accepted results"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT / "Boreas_RT_Complete_Local_Results_and_Evidence.pdf")
    args = parser.parse_args(); generate(args.output.resolve()); print(args.output.resolve()); return 0


if __name__ == "__main__":
    raise SystemExit(main())
