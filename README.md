# E2O Localization Robustness Evaluation Framework

ROS Noetic / Docker framework for running E2O localization estimators with external health monitoring, fusion, and fault injection.
Native estimator code lives inside Docker images. This repository owns the E2O wrappers, sensor adapter, health checks, fusion supervisor, run scripts, RViz profiles, and evaluation tools.

UrbanLoco and Boreas-RT support is integrated through the same adapters, native estimator containers, trajectory schema, and evaluation math. See [the compatibility report](docs/PUBLIC_DATASET_COMPATIBILITY.md) for verified sensor facts and the [real execution report](docs/VALIDATION_REPORT.md) for measured short-window outcomes; “configured” or merely “process complete” is not treated as accurate localization.

---

## Algorithms

| Mode | Estimators | Sensors | Main output |
|---|---|---|---|
| `fast_livo2` | FAST-LIVO2 | LiDAR + Camera + IMU | `/fast_livo2/odometry` |
| `orbslam3` | ORB-SLAM3 | Front camera + Depth + IMU | `/orbslam3/camera_odometry` |
| `lvisam` | LVI-SAM | LiDAR + camera + IMU in public-dataset runs | `/lvisam/odometry` |
| `fusion` | FAST-LIVO2 + ORB-SLAM3 + LVI-SAM | all | `/fused_localization/odometry` |
| `lvisam_fusion` / `fusion_2` | LVI-SAM + ORB-SLAM3 | LiDAR + camera + IMU | `/fused_localization/odometry` |
| `fusion_navigation` | FAST-LIVO2 + ORB-SLAM3 + LVI-SAM + nav gate | all | `/fused_localization/navigation_ok` |

In `fusion` mode: FAST-LIVO2 is primary, ORB-SLAM3 is backup, LVI-SAM is tertiary (camera failure fallback).

---

## Quick start

```bash
# 1. Build
./build.sh all

# 2. Run a standalone algorithm
./run.sh fast_livo2 e2o /path/to/one_full_loop.bag
./run.sh orbslam3   e2o /path/to/one_full_loop.bag
./run.sh lvisam     e2o /path/to/one_full_loop.bag

# 3. Run fusion
./run.sh fusion     e2o /path/to/one_full_loop.bag

# 4. Run without RViz if needed
RVIZ=false ./run.sh fusion e2o /path/to/one_full_loop.bag

# 5. Run only the first 60 seconds of the bag
BAG_DURATION=60 ./run.sh fusion e2o /path/to/one_full_loop.bag
BAG_DURATION=60 ./run.sh fusion_2 e2o /path/to/one_full_loop.bag

# Optional: slow bag playback if an estimator cannot keep up
BAG_RATE=0.5 ./run.sh fusion e2o /path/to/one_full_loop.bag
```

Output is written to `data/output/<run_id>/`.

Runtime bag controls:

| Variable | Default | Description |
|---|---|---|
| `BAG_RATE` | `1.0` | Rosbag playback speed multiplier passed to `rosbag play --rate` |
| `BAG_DURATION` | unset | Stop playback after this many seconds using `rosbag play --duration` |

---

## Build

```bash
./build.sh all              # all images
./build.sh fusion           # e2o-localization-fusion:latest
./build.sh fast_livo2       # fastlivo2-e2o:latest
./build.sh orbslam3         # orbslam3-e2o:latest
./build.sh lvisam           # lvisam-e2o:latest
./build.sh fastlio2         # fastlio2-benchmark:latest
./build.sh rtabmap          # rtabmap-benchmark:latest
./build.sh all --no-cache   # force clean rebuild
```

## Public datasets

Public data is streamed directly from ROS bags or native Boreas files; no generated Boreas bag is required. Downloaders resume into existing sequence directories. The route-window downloader retains fixed scored intervals plus only the earlier continuous camera/LiDAR frames needed for native estimator initialization.

```bash
# Download both selected sequences, official calibration, IMU and ground truth.
./scripts/datasets/download_public_datasets.sh

# Resume the Boreas Farm, Forest, and Urban scored windows and their common
# 40-second continuous sensor warm-up.
./scripts/datasets/download_boreas_route_windows.sh all

# Optional: fetch the first 120 synchronized Boreas camera/lidar frames plus
# the complete independent IMU stream for short integration tests. The full
# downloader later resumes into the same directory and fills missing files.
BOREAS_VALIDATION_FRAMES=120 ./scripts/datasets/download_boreas_validation_slice.sh

# Inspect real counts, rates, stamps, frames, calibration and GT availability.
./scripts/datasets/inspect_dataset.py --dataset urbanloco --sequence ca_20190828184706
./scripts/datasets/inspect_dataset.py --dataset boreas_rt --sequence boreas_2024_12_04_14_44

# Convert only official GNSS/INS reference poses (never estimator output).
./scripts/datasets/prepare_ground_truth.sh all
```

Build all native images with `./build.sh all`, then use the same command shape for every pair:

```bash
for dataset_sequence in \
  'urbanloco ca_20190828184706' \
  'boreas_rt boreas_2024_12_04_14_44'; do
  read -r dataset sequence <<<"$dataset_sequence"
  for algorithm in fastlio2 fastlivo2 orbslam3 rtabmap lvisam; do
    rate=1.0
    case "$algorithm" in orbslam3|rtabmap|lvisam) rate=0.5 ;; esac
    ./run_benchmark.sh --dataset "$dataset" --sequence "$sequence" \
      --algorithm "$algorithm" --rate "$rate" --duration 30
  done
done
```

The slower rates are the validated playback settings for the heavier native
pipelines; they do not change sensor timestamps. Remove `--duration 30` only
after a pair passes short validation. Results are written to
`results/<dataset>/<sequence>/<algorithm>/<run_id>/`, including the raw
trajectory, copied configuration, execution status, logs, aligned trajectory,
machine-readable metrics, report, and plots. Public modes are metric and
normally use SE(3); Sim(3) requires a recorded gauge/scale reason. Boreas
ORB-SLAM3 defaults to native RGB-D tracking using the camera plus calibrated,
causally deskewed LiDAR-projected depth. Pure mono and inertial variants remain
explicit ablations. LVI-SAM defaults to its stable lidar-inertial pipeline;
pass `--lvisam-mode visual-lidar-inertial` to start the VINS nodes as well.

Leak-free parameter work uses explicit temporal phases and offsets. Tuning and
validation runs are excluded from the default result summary; only frozen
`holdout` and normal `production` runs can appear there:

```bash
./run_benchmark.sh --dataset urbanloco --sequence ca_20190828184706 \
  --algorithm rtabmap --start-offset 0 --duration 60 --phase tuning
./run_benchmark.sh --dataset urbanloco --sequence ca_20190828184706 \
  --algorithm rtabmap --start-offset 60 --duration 60 --phase validation
./run_benchmark.sh --dataset urbanloco --sequence ca_20190828184706 \
  --algorithm rtabmap --start-offset 180 --duration 68 --phase holdout
```

Validation and holdout replay the sensor prefix from sequence start for
stateful estimator warm-up, but evaluation crops that prefix and scores only
the requested offset/duration.

The three Boreas route manifests declare a common 40-second ORB warm-up.
Farm also declares a 120-second FAST-LIVO2 low-speed initialization prefix.
`--pre-roll` replays these sensor prefixes without moving the absolute scored
timestamps, and the route-matrix runner supplies them automatically:

```bash
./scripts/run_boreas_route_matrix.sh
python3 tools/generate_boreas_route_report.py
python3 tools/generate_repository_implementation_pdf.py
```

Generate a full-production comparison table directly from accuracy-accepted
artifacts. Holdout slices never replace a rejected full route in this table.
Evaluation writes `quality_status.json`
and exactly one of `VALIDATION_ACCEPTED` or `VALIDATION_REJECTED`. The automatic
gate requires a completed run, at least 20 matched poses, at least 80% duration
coverage, and ATE RMSE no greater than 2% of the matched reference distance
(with a 1 m floor for short windows), plus maximum ATE no greater than 15 m.
Metric modes use SE(3); explicitly
scale-unobservable pure monocular runs use Sim(3). `run_benchmark.sh` returns
non-zero when this gate rejects a run:

```bash
python3 tools/summarize_public_results.py --dataset boreas_rt \
  --sequence boreas_2024_12_04_14_44
python3 tools/summarize_public_results.py --dataset urbanloco \
  --sequence ca_20190828184706
```

Measured full-sequence acceptance is recorded in
`docs/VALIDATION_REPORT.md`. Under the full-sequence gate, both datasets accept
FAST-LIO2 and FAST-LIVO2. ORB-SLAM3, RTAB-Map, and LVI-SAM remain explicit
full-route accuracy failures even though their processes produce evaluable
trajectories. Short or locally aligned slices are not promoted over those
full-route results.

Add `--rviz` to any `run_benchmark.sh` command to display the legitimate reference path, reference vehicle pose/TF, live estimator trajectory, current frames, and an explicitly labelled non-official accumulated LiDAR cloud using `rviz/public_dataset_reference.rviz`. The launch receives the dataset's `base_to_lidar` calibration and applies no visual offsets. A completed aligned result can be reopened by passing its `evaluation/aligned_trajectory.csv` as `estimate_csv` to `reference_visualization.launch`.

---

## Input bag requirements

The bag must contain:
```
/lidar103/velodyne_points
/mavros/imu/data
/camera/color/image_raw
/camera/depth/image_rect_raw
```

Check before running:
```bash
rosbag info /path/to/one_full_loop.bag
```

---

## Documentation

| File | Contents |
|---|---|
| `SOLO.md` | All standalone modes — full run commands and options |
| `FUSION.md` | All fusion modes — fault injection, switching behavior, monitoring |
| `SENSOR_FAILURE_AND_HEALTH.md` | Sensor failure commands and health monitoring checklist |
| `ARCHITECTURE.md` | Data flow, package descriptions, state machine |
| `TF_TREE.md` | TF ownership and frame conventions |
| `UPSTREAM_LOCK.md` | Pinned native estimator refs |

---

## Evaluation

Runs evaluate automatically on completion. To evaluate manually:
```bash
./evaluation/evaluate.sh data/output/<run_id>
./evaluation/evaluate.sh data/output/<run_id> data/e2o/ground_truth/ref.csv
```

---

## Static validation

```bash
./tests/static_validation.sh
```

Checks Python syntax, XML/YAML, calibration consistency, and runs synthetic fusion/evaluation unit tests.

---

## Runtime diagnostics

```bash
./scripts/diagnose_runtime.sh

rostopic echo -n 1 /fused_localization/status
rostopic echo    /fused_localization/active_source
rostopic hz      /fast_livo2/odometry
rostopic hz      /fused_localization/odometry
```

---

## RViz configs

| Config | Fixed frame |
|---|---|
| `rviz/e2o_fast_livo2.rviz` | `camera_init` |
| `rviz/e2o_orbslam3.rviz` | `orbslam3_grid` |
| `rviz/e2o_lvisam.rviz` | `odom` |
| `rviz/e2o_fusion.rviz` | `map` |
