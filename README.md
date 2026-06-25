# E2O Localization Robustness Evaluation Framework

ROS Noetic/Docker framework for running E2O localization estimators and external fusion/fallback.

Native estimator code is kept inside Docker images. This repository owns the E2O wrappers, sensor adapter, health checks, fusion supervisor, run scripts, RViz profiles, and evaluation tools.

## Algorithms

| Mode | Runs | Main output |
| --- | --- | --- |
| `fast_livo2` | FAST-LIVO2 only | `/fast_livo2/odometry` |
| `orbslam3` | ORB-SLAM3 only | `/orbslam3/camera_odometry` |
| `lvisam` | LVI-SAM only | `/lvisam/odometry` |
| `fusion` | FAST-LIVO2 + ORB-SLAM3 | `/fused_localization/odometry` |
| `lvisam_fusion` | LVI-SAM + ORB-SLAM3 | `/fused_localization/odometry`, `/fused_localization/metric_odometry` |
| `fusion_2` | Legacy alias for `lvisam_fusion` | `/fused_localization/odometry`, `/fused_localization/metric_odometry` |
| `fusion_navigation` | FAST-LIVO2 + ORB-SLAM3 + navigation safety gate | `/fused_localization/navigation_ok` |

## Input Bag

All run modes currently support only the E2O dataset:

```bash
data/e2o/one_full_loop.bag
```

The bag must provide:

```text
/lidar103/velodyne_points
/mavros/imu/data
/camera/color/image_raw
```

Check a bag before running:

```bash
rosbag info data/e2o/one_full_loop.bag
rosbag check data/e2o/one_full_loop.bag
```

## Build

Build everything:

```bash
./build.sh all
```

Build one image:

```bash
./build.sh fusion
./build.sh fast_livo2
./build.sh orbslam3
./build.sh lvisam
```

Force a clean rebuild only when needed:

```bash
./build.sh all --no-cache
./build.sh lvisam --no-cache
```

Legacy shortcuts still work:

```bash
./build_fastlivo2.sh
./build_orbslam3.sh
```

## Run

Use the explicit mode form:

```bash
./run.sh <mode> e2o <bag>
```

Examples:

```bash
./run.sh fast_livo2 e2o data/e2o/one_full_loop.bag
./run.sh orbslam3 e2o data/e2o/one_full_loop.bag
./run.sh lvisam e2o data/e2o/one_full_loop.bag
./run.sh fusion e2o data/e2o/one_full_loop.bag
./run.sh lvisam_fusion e2o data/e2o/one_full_loop.bag
```

With RViz:

```bash
RVIZ=true ./run.sh fast_livo2 e2o data/e2o/one_full_loop.bag
RVIZ=true ./run.sh orbslam3 e2o data/e2o/one_full_loop.bag
RVIZ=true ./run.sh lvisam e2o data/e2o/one_full_loop.bag
RVIZ=true ./run.sh fusion e2o data/e2o/one_full_loop.bag
RVIZ=true ./run.sh lvisam_fusion e2o data/e2o/one_full_loop.bag
```

Navigation safety gate:

```bash
TF_MODE=direct \
NAVIGATION_LAUNCH_FILE=/workspace/navigation/my_navigation.launch \
./run.sh fusion_navigation e2o data/e2o/one_full_loop.bag
```

Every run writes:

```text
data/output/<run_id>/
```

The directory contains `run_metadata.env`, trajectory CSVs, status timelines, fusion events, and evaluation outputs when generated.

## Common Overrides

| Variable | Purpose |
| --- | --- |
| `BAG_RATE=0.5` | Change playback rate. FAST/LVI-SAM-heavy modes default to `0.5`; ORB-only defaults to `1.0`. |
| `RVIZ=true` | Start RViz with the mode-specific config. |
| `RVIZ_CONFIG=/workspace/rviz/file.rviz` | Override the RViz config. |
| `PRIMARY_SOURCE=orbslam3` | Start fusion with ORB as active source when scale is valid. |
| `TF_MODE=direct` | Publish `odom -> base_link` directly. This is the default. |
| `TF_MODE=map_to_odom` | Publish `map -> odom`; requires another owner for `odom -> base_link`. |
| `FAULT_INJECTION=true` | Enable fault injection nodes for robustness tests. |
| `LIDAR_TOPIC=...` | Override source LiDAR topic. |
| `IMU_TOPIC=...` | Override source IMU topic. |
| `CAMERA_TOPIC=...` | Override source camera topic. |
| `FUSION_CONFIG=...` | Override fusion config. |

Mode-specific config overrides:

```bash
FAST_CONFIG=/workspace/wrappers/fast_livo2_e2o/config/fast_livo2_e2o.yaml
ORB_CONFIG=/workspace/wrappers/orbslam3_e2o/config/e2o_front_mono_orbslam3.yaml
LVISAM_LIDAR_CONFIG=/workspace/wrappers/lvisam_e2o/config/params_lidar_e2o.yaml
LVISAM_CAMERA_CONFIG=/workspace/wrappers/lvisam_e2o/config/params_camera_e2o.yaml
```

## Runtime Checks

Run these inside a ROS-configured shell while a run is active:

```bash
rostopic list
rostopic hz /livox/lidar
rostopic hz /livox/imu
rostopic hz /camera/right/image_raw
rostopic hz /fast_livo2/odometry
rostopic hz /orbslam3/camera_odometry
rostopic hz /lvisam/odometry
rostopic hz /fused_localization/odometry
rostopic echo -n 1 /localization_health/summary
rostopic echo -n 1 /fused_localization/status
```

Collect diagnostics:

```bash
./scripts/diagnose_runtime.sh
```

Validate one recorded standalone estimator run:

```bash
python3 tests/verify_estimator_run.py fast_livo2 data/output/<run_id>
python3 tests/verify_estimator_run.py orbslam3 data/output/<run_id>
python3 tests/verify_estimator_run.py lvisam data/output/<run_id>
```

## Evaluation

Evaluate a run:

```bash
./evaluation/evaluate.sh data/output/<run_id>
```

Use an explicit reference:

```bash
./evaluation/evaluate.sh data/output/<run_id> data/e2o/ground_truth/one_loop_gps_enu.csv
./evaluation/evaluate.sh data/output/<run_id> data/e2o/gt_one_full_loop_fastlivo2_lidar103.csv
```

Generated files are under:

```text
data/output/<run_id>/evaluation/
```

## Validation

Run static checks:

```bash
./tests/static_validation.sh
```

This checks Python syntax, XML/YAML parsing, calibration consistency, launch assumptions, and synthetic fusion/evaluation tests.

## Robustness Testing

Start fault-enabled fusion:

```bash
FAULT_INJECTION=true RVIZ=true ./run.sh fusion e2o data/e2o/one_full_loop.bag
```

Apply faults from another shell:

```bash
./tests/failure_control.sh fast_freeze
./tests/failure_control.sh fast_recover
./tests/failure_control.sh orb_freeze
./tests/failure_control.sh orb_recover
./tests/failure_control.sh camera_drop
./tests/failure_control.sh camera_recover
```

Convenience wrapper:

```bash
./robustness.sh run data/e2o/one_full_loop.bag
./robustness.sh status data/output/<run_id>
./robustness.sh watch data/output/<run_id>
./robustness.sh recover-all
./robustness.sh matrix
```

## RViz Frames

| Config | Fixed frame |
| --- | --- |
| `rviz/e2o_fast_livo2.rviz` | `camera_init` |
| `rviz/e2o_orbslam3.rviz` | `orbslam3_grid` |
| `rviz/e2o_lvisam.rviz` | `odom` |
| `rviz/e2o_fusion.rviz` | `map` |

LVI-SAM publishes its native path and registered clouds in `odom`, so the LVI-SAM RViz profile must use `odom`.

## Important Notes

- `fusion` fuses FAST-LIVO2 with ORB-SLAM3.
- `lvisam_fusion` fuses LVI-SAM with ORB-SLAM3; `fusion_2` remains as a legacy alias only.
- `/fused_localization/odometry` is continuity-preserving; `/fused_localization/metric_odometry` stays in the selected metric source frame and may jump on recovery.
- ORB-SLAM3 is monocular; fusion estimates a Sim(3) scale from overlap with the metric source.
- Native estimator TF is not used for navigation. See `TF_TREE.md`.
- The supplied archive has LiDAR-to-camera calibration, but IMU-to-LiDAR remains an explicit identity assumption. Replace it before claiming final accuracy.

More detail:

```text
RUNNING.md
TF_TREE.md
FUSION_AND_FALLBACK.md
FAILURE_TESTING.md
FINAL_REPORT.md
```
