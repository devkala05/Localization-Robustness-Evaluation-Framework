#!/usr/bin/env python3
"""Generate a source-grounded implementation report for this repository."""
from __future__ import annotations

import argparse
import textwrap
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


ROOT = Path(__file__).resolve().parents[1]
NAVY = "#102A43"
TEAL = "#0F766E"
INK = "#243B53"
MUTED = "#627D98"
PAPER = "#F8FAFC"


def wrapped(text: str, width: int = 112) -> str:
    lines = []
    for paragraph in text.strip().splitlines():
        if not paragraph.strip():
            lines.append("")
        elif paragraph.startswith("•"):
            lines.extend(textwrap.wrap(paragraph, width, subsequent_indent="  "))
        else:
            lines.extend(textwrap.wrap(paragraph, width))
    return "\n".join(lines)


def page(pdf: PdfPages, number: int, title: str, subtitle: str, body: str) -> None:
    fig = plt.figure(figsize=(8.27, 11.69), facecolor=PAPER)
    fig.add_artist(plt.Line2D([0.075, 0.925], [0.973, 0.973], color=TEAL, linewidth=3.2))
    fig.text(0.075, 0.95, title, fontsize=20, fontweight="bold", color=NAVY, va="top")
    fig.text(0.075, 0.912, subtitle, fontsize=9.2, color=MUTED, va="top")
    fig.text(0.075, 0.865, wrapped(body), fontsize=9.4, color=INK,
             va="top", linespacing=1.36, family="sans-serif")
    fig.add_artist(plt.Line2D([0.075, 0.925], [0.047, 0.047], color="#D9E2EC", linewidth=0.7))
    fig.text(0.075, 0.025, "LOCALIZATION ROBUSTNESS EVALUATION FRAMEWORK  /  IMPLEMENTATION GUIDE",
             fontsize=6.6, color=MUTED, fontweight="bold")
    fig.text(0.925, 0.025, f"{number:02d}", fontsize=7.2, color=TEAL, ha="right", fontweight="bold")
    pdf.savefig(fig)
    plt.close(fig)


def architecture_page(pdf: PdfPages, number: int) -> None:
    fig = plt.figure(figsize=(8.27, 11.69), facecolor=PAPER)
    fig.add_artist(plt.Line2D([0.075, 0.925], [0.973, 0.973], color=TEAL, linewidth=3.2))
    fig.text(0.075, 0.95, "Repository architecture", fontsize=20, fontweight="bold",
             color=NAVY, va="top")
    fig.text(0.075, 0.912, "One adapter/evaluation contract surrounds five native estimators.",
             fontsize=9.2, color=MUTED, va="top")
    ax = fig.add_axes([0.08, 0.20, 0.84, 0.64])
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    boxes = [
        (0.4, 8.1, 9.2, 1.0, "Dataset layer\nE2O bag · UrbanLoco bag · Boreas native files", "#E0F2FE"),
        (0.4, 6.4, 9.2, 1.0, "Input layer\nplayers → timestamp-preserving sensor adapter → calibrated TF/topics", "#CCFBF1"),
        (0.4, 4.2, 1.55, 1.2, "FAST-LIO2", "#DBEAFE"),
        (2.3, 4.2, 1.55, 1.2, "FAST-LIVO2", "#CFFAFE"),
        (4.2, 4.2, 1.55, 1.2, "LVI-SAM", "#D1FAE5"),
        (6.1, 4.2, 1.55, 1.2, "ORB-SLAM3", "#EDE9FE"),
        (8.0, 4.2, 1.55, 1.2, "RTAB-Map", "#FFEDD5"),
        (0.4, 2.4, 9.2, 1.0, "Output contract\nnative odometry → recorder → finite/monotonic trajectory CSV", "#E0F2FE"),
        (0.4, 0.7, 9.2, 1.0, "Evaluation/reporting\ntime association → justified alignment → ATE/RPE/yaw → plots, JSON, PDF", "#CCFBF1"),
    ]
    for x, y, w, h, label, color in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=color,
                                   edgecolor=TEAL, linewidth=1.15))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=8.3, color=NAVY)
    for y1, y2 in ((8.1, 7.4), (6.4, 5.4), (4.2, 3.4), (2.4, 1.7)):
        ax.annotate("", xy=(5, y2), xytext=(5, y1),
                    arrowprops={"arrowstyle": "->", "color": MUTED})
    fig.text(0.075, 0.105, wrapped(
        "Native algorithm containers are isolated and pinned. The repository owns data conversion, "
        "topic/frame normalization, launch wiring, output capture, health/fusion utilities, evaluation, "
        "and provenance. Ground truth is available only to the post-run evaluator and RViz reference view."
    ), fontsize=9.2, color=INK, va="top", linespacing=1.35)
    fig.add_artist(plt.Line2D([0.075, 0.925], [0.047, 0.047], color="#D9E2EC", linewidth=0.7))
    fig.text(0.075, 0.025, "LOCALIZATION ROBUSTNESS EVALUATION FRAMEWORK  /  IMPLEMENTATION GUIDE",
             fontsize=6.6, color=MUTED, fontweight="bold")
    fig.text(0.925, 0.025, f"{number:02d}", fontsize=7.2, color=TEAL, ha="right", fontweight="bold")
    pdf.savefig(fig); plt.close(fig)


def generate(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(output) as pdf:
        page(pdf, 1, "Localization Benchmark Implementation",
             "Five algorithms, three dataset families, reproducible execution and evaluation.",
             f"""
Repository: {ROOT}
Generated: {datetime.now().astimezone():%Y-%m-%d %H:%M %Z}

This document explains the implementation actually present in the repository. It distinguishes native estimator code from wrapper behavior, records the sensor mode used for each algorithm, and documents timing, calibration, output, evaluation, provenance, and no-leak safeguards.

The Boreas complete-local campaign covers the entire locally downloaded joint camera/LiDAR interval for all four routes: Tunnel 169.35 s, Farm 420.56 s, Forest 216.90 s, and Urban 196.80 s. There is no warm-up exclusion, pre-roll, or 60-second scoring crop in this campaign. The report explicitly calls these complete local downloads rather than claiming they are the much longer original cloud traversals.

Primary entry points
• run_benchmark.sh — uniform public-dataset execution and evaluation.
• run.sh — existing private E2O and fusion workflows.
• scripts/datasets — reproducible download, inspection, and ground-truth conversion.
• wrappers — ROS packages that adapt sensors and normalize native outputs.
• evaluation — trajectory association, alignment, metrics, quality gates, and plots.
• results — immutable per-run inputs, logs, outputs, metrics, status, plots, and reports.
""")
        architecture_page(pdf, 2)
        page(pdf, 3, "Dataset ingestion and calibration",
             "Timestamps and transforms come from dataset records, never guessed constants.",
             """
E2O
• Existing ROS bag workflow is preserved. The E2O adapter normalizes the private LiDAR, camera, depth, and IMU streams and supports standalone estimators plus monitored fusion and fault injection.

UrbanLoco
• The ROS bag player republishes selected topics using rosbag event timestamps. The camera's invalid/zero header time is replaced by the legitimate bag event time. NovAtel SPAN reference poses are converted using receiver measurement time and supplied sensor extrinsics.

Boreas-RT
• boreas_player.py streams PNG camera images, six-field Velodyne scans, and the independent 200 Hz DMU directly from native files; no large intermediate bag is created.
• LiDAR filenames and camera filenames encode acquisition time in microseconds; DMU rows encode nanoseconds. The player merges them chronologically and publishes /clock without changing message stamps.
• Complete-local manifests use an absolute acquisition-time start at the earliest joint camera/LiDAR timestamp and run to the latest common timestamp. This prevents the start from moving when one algorithm enables camera+LiDAR while another enables LiDAR+IMU.
• The complete-local campaign evaluates every replayed pose in its locally available joint-sensor interval. The earlier fixed-window campaign remains separately auditable, but its warm-up and 60-second crop are not used in this report.
• Ground truth comes from post-processed Applanix POSPac GNSS/INS/wheel output. Estimators use the independent DMU41 rather than the Applanix IMU, avoiding reference/estimator sensor correlation.
• The four selected Boreas sequences were audited: all supplied calibration files are byte-identical. The shared wrapper profile is therefore evidence-based, while every run still copies the exact applied configuration.
""")
        page(pdf, 4, "FAST-LIO2 implementation",
             "Pinned native FAST_LIO · LiDAR + independent IMU · metric SE(3).",
             """
Native method
• FAST-LIO2 performs tightly coupled iterated error-state filtering with direct raw-point registration against an incremental map. It estimates metric motion from a 3D LiDAR and IMU; no camera or ground-truth input is used.

Repository integration
• docker/fastlio2 pins hku-mars/FAST_LIO at commit 7cc4175… and its Livox dependencies. The native fastlio_mapping executable is launched unchanged by wrappers/fastlio2_benchmark.
• The adapter publishes /benchmark/points_raw and /benchmark/imu_raw with native acquisition stamps. It preserves x/y/z/intensity/ring/time and converts the supplied DMU/LiDAR calibration into the estimator's body convention.
• Boreas uses 128 scan lines, 10 Hz scans, calibrated extrinsics, fixed extrinsic estimation, and metric odometry on /fastlio2/odometry.
• The recorder stores native odometry in fastlio2_trajectory.csv. SE(3) is used because LiDAR+IMU scale is observable.
""")
        page(pdf, 5, "FAST-LIVO2 implementation",
             "Pinned native FAST-LIVO2 · LiDAR + camera + independent IMU · metric SE(3).",
             """
Native method
• FAST-LIVO2 combines direct LiDAR-inertial odometry with visual photometric constraints. The visual and LiDAR branches share the filter state; depth and scale remain metric through LiDAR/IMU geometry.

Repository integration
• docker/fastlivo2 pins FAST-LIVO2 commit 0d2c034…, rpg_vikit 6c886c8…, and the required Sophus revision. A versioned compatibility patch exposes native outputs; it does not inject reference poses.
• The adapter emits /livox/lidar, /livox/imu, and—when enabled—/camera/right/image_raw. Boreas images remain at their native rectified 2448×2048 projection; the supplied camera/LiDAR and DMU/LiDAR matrices populate Rcl/Pcl and body extrinsics.
• Farm selects FAST-LIVO2's native img_en=0 LiDAR-inertial mode because the crop-road replay retrieved almost no persistent visual-map points and its VIO update diverged. Tunnel, Forest, and Urban retain full LIVO. The selected mode is stored in run metadata rather than hidden behind output repair.
• The wrapper remaps the native odometry output and disables navigation anchoring for public benchmarks (rebase_on_start=false). Map/PCD saving is disabled during trajectory evaluation to control storage.
• Output is fastlivo2_trajectory.csv and evaluation is SE(3).
""")
        page(pdf, 6, "LVI-SAM implementation",
             "Pinned native LVI-SAM · selected stable LiDAR-inertial mode · metric SE(3).",
             """
Native method
• LVI-SAM contains LiDAR deskewing, feature extraction, IMU preintegration, factor-graph map optimization, and optional visual-inertial modules.

Repository integration
• docker/lvisam pins LVI-SAM commit 0d822f6… and GTSAM 4.0.2. The repository patch supplies ROS Noetic/OpenCV compatibility, avoids an empty GPS subscription, and provides an opt-in calibrated camera/LiDAR conversion.
• Public Boreas production runs select lidar-inertial mode because the visual branch showed native VINS resets during complete validation. This is reported explicitly; the executable is not silently replaced by a different algorithm.
• The 128-ring Boreas geometry and per-point time are retained. The independent DMU and official sensor-to-body transform are used; GPS/ground truth is not subscribed. Single-pass route evaluation disables speculative loop closure.
• Native map-optimization odometry is converted from the calibrated sensor pose to base_link and recorded as lvisam_trajectory.csv. Evaluation is SE(3).
""")
        page(pdf, 7, "ORB-SLAM3 implementation",
             "Pinned native ORB-SLAM3 · camera + calibrated LiDAR-projected depth.",
             """
Native method
• ORB-SLAM3 extracts multi-scale ORB features, tracks a sparse map, performs local bundle adjustment, keyframe management, relocalization, Atlas map handling, and loop/map optimization.

Repository integration
• docker/orbslam3 pins ORB-SLAM3 V1.0 commit 0df83dde… and Pangolin v0.8. Versioned build patches expose read-only native pose/keyframe outputs, add ROS entry points, and apply the documented sparse-RGBD integration policy before the native core is compiled; feature matching, pose optimization, bundle adjustment, loop closure, and map geometry remain native.
• Boreas has one camera rather than a native RGB-D sensor. The adapter projects one calibrated complete LiDAR sweep into the rectified camera, z-buffers measured depth, and locally splats valid returns only so native RGB-D tracking can consume metric observations. It does not use GT depth or aligned trajectory data.
• Farm production masks the far sky and fixed ego hood so optimization uses the static LiDAR-supported road/field band. The configured virtual baseline affects native RGB-D depth uncertainty, not measured depth or output scale. Contrast enhancement remains disabled because its route replay caused a native map reset.
• Boreas points retain their signed acquisition offsets around the documented scan midpoint. Each selected sweep is causally deskewed to camera time using only preceding native ORB poses; neither GT nor another estimator supplies motion.
• Native 2448×2048 images are admitted at the measured 10 Hz cadence. A lossless producer/consumer frontend keeps synchronized frames. The sparse-depth local-map floor is consistent with ORB's own motion/recovery criteria, while a mapper-idle cadence bounds keyframe spacing to one second without restoring the dense-depth trigger that requested nearly every image.
• During RECENTLY_LOST, an unset frame is marked lost in native trajectory bookkeeping. This makes SaveTrajectoryTUM omit the placeholder exactly as its contract states, instead of exporting a repeated prior timestamp. Valid poses are neither sorted, stitched, re-anchored, nor rewritten.
• Complete-local route manifests begin at the earliest joint camera/LiDAR timestamp and run through the latest common timestamp. This initializes each method from the natural beginning of the locally available interval instead of re-anchoring, trimming, or rewriting a failed output.
• The native finalized trajectory is exported on clean shutdown, converted from optical-camera pose to base_link using official calibration, and preserved separately. A documented global Sim(3) is evaluation-only for the remaining single-camera sparse-depth gauge; its scale is reported and the final plotted CSV is the aligned artifact.
""")
        page(pdf, 8, "RTAB-Map implementation",
             "ROS Noetic RTAB-Map 0.21.13 · deskewed LiDAR ICP + IMU · metric SE(3).",
             """
Native method
• RTAB-Map provides odometry frontends and graph SLAM. The Boreas production profile uses native point-to-plane ICP odometry with an IMU motion prior and scan deskewing.

Repository integration
• docker/rtabmap uses the frozen final ROS Noetic package snapshot. Every run stores the Docker image ID.
• The adapter publishes /benchmark/points_raw and /benchmark/imu_raw, preserving Boreas scan-midpoint timing and signed per-point offsets required by native deskewing.
• The configuration uses 4-DoF road-vehicle ICP, bounded local correspondence, constant-motion prediction, every accepted scan as the next local reference, and finite translation gates sized for road speed.
• Boreas reports /rtabmap/icp_odometry directly. Graph output is not substituted because these selected single-pass windows have no verified loop-closure source. The native RTAB database remains a run artifact. Evaluation is SE(3).
""")
        page(pdf, 9, "Execution, outputs, and provenance",
             "A completed process is not automatically an accepted localization result.",
             """
run_benchmark.sh
• Validates dataset/sequence/algorithm/mode arguments and checks required Docker images and inputs.
• Creates a unique results/<dataset>/<sequence>/<algorithm>/<run_id> directory before starting isolated ROS containers.
• Starts roscore, only the required sensor-adapter branches, the selected native algorithm, and a trajectory recorder. Unrelated camera/LiDAR decoding is disabled per mode.
• Replays data with original ROS timestamps at a slower wall-clock rate only when compute margin is required. Playback rate never changes acquisition time or evaluation time.
• Captures stdout/stderr, topic graph, copied sensor and algorithm YAML, image ID, run metadata, exact reproduction command, native trajectory, validation status, and—where applicable—the native RTAB database or ORB TUM export.

Completion checks
• Player exit, early algorithm exit, native finalization, pose count, finite values, normalized quaternions, and strictly monotonic stamps are checked.
• execution_status.json records process completion. quality_status.json independently records accuracy acceptance and its reasons. Failure is retained rather than hidden or replaced by fabricated numbers.
""")
        page(pdf, 10, "Evaluation and no-leak safeguards",
             "Ground truth is post-run only; native and aligned trajectories remain distinct.",
             """
Association and metrics
• Estimated and reference poses are associated by acquisition timestamp with a recorded tolerance (default 0.05 s).
• SE(3) alignment fits one global rigid transform for metric modes. Sim(3) is allowed only with an explicit scale-unobservable/gauge reason and records its scale factor.
• The report includes ATE RMSE, MAE, median, P95, maximum; translational and rotational RPE at one second; yaw error; associated pose count; durations; and reference/estimated distance.

Artifact semantics
• evaluation/native_trajectory.csv is an exact snapshot of estimator output.
• evaluation/aligned_trajectory.csv is produced only after the run. evaluation/final_trajectory.csv is byte-identical to it and is the only estimate used by the saved comparison plot.
• Neither alignment transform nor ground truth is published to tracking, mapping, or state estimation.

No-leak protocol
• Ground truth is used for post-run scoring and failure diagnosis only. It is never published to an estimator, used to generate RGB-D depth, used for deskew, or fed back as a pose/scale correction.
• The route campaign is a regression benchmark after implementation remediation, not a claim of untouched statistical holdout performance. Diagnostic and rejected runs remain on disk. The accompanying complete-local evidence book displays every execution and labels its status rather than hiding non-accepted cells.
""")
        page(pdf, 11, "Quality gates, testing, and reproducibility",
             "Results are accepted by measured coverage and error, not visual appearance alone.",
             """
Quality policy
• Execution must complete, evaluation must be valid, at least 20 poses must associate, and trajectory duration must cover at least 80% of the reference interval.
• ATE RMSE must be no greater than 2% of associated reference distance with a 1 m floor. Maximum ATE has an absolute 15 m ceiling.
• The CLI exits non-zero on rejection while retaining all artifacts for diagnosis.

Tests and static checks
• Unit tests cover time cropping, SE(3)/Sim(3) policy, final-plot artifact identity, ORB projected-depth behavior, native ORB conversion, RTAB timing/configuration, and trajectory validity.
• scripts/validate_configuration.py cross-checks duplicated calibration values and frame transforms across YAML/OpenCV formats. XML, Python, shell syntax, and repository static checks are run before report generation.

Rebuild and repeat
• UPSTREAM_LOCK.md records every native repository ref/package version. Dockerfiles verify commits during build.
• scripts/datasets/download_boreas_route_windows.sh reproduces the exact route files by sequence and acquisition timestamp.
• scripts/run_boreas_route_matrix.sh applies the same five-algorithm matrix to every declared route window.
• Each result embeds the reproduction command, Docker image identity, configurations, and input/output hashes needed for audit.
""")
        metadata = pdf.infodict()
        metadata["Title"] = "Localization Benchmark Repository Implementation"
        metadata["Author"] = "Localization Robustness Evaluation Framework"
        metadata["Subject"] = "Implementation of FAST-LIO2, FAST-LIVO2, LVI-SAM, ORB-SLAM3 and RTAB-Map"
        metadata["Keywords"] = "localization, Boreas-RT, ROS, ATE, RPE, reproducibility"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path("results/boreas_rt/complete_local_benchmark/"
                                     "Boreas_RT_Repository_Implementation_Report.pdf"))
    args = parser.parse_args()
    output = args.output.resolve()
    generate(output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
