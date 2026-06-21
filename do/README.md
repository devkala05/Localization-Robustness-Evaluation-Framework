# E2O FAST-LIVO2 + ORB-SLAM3 Localization Framework

This repository is an E2O-only cleanup of the supplied localization framework. It contains two native estimators—FAST-LIVO2 and monocular ORB-SLAM3—and an external ROS1 supervisory fusion/fallback layer. Native optimization, tracking, mapping, loop closure, feature extraction, and sensor processing remain in their upstream projects.

## What remains

- `wrappers/fast_livo2_e2o`: E2O configuration and output normalization around native FAST-LIVO2.
- `wrappers/orbslam3_e2o`: E2O monocular configuration and camera-pose normalization around native ORB-SLAM3.
- `wrappers/localization_benchmark`: E2O sensor adapter, camera info, static sensor TF, and controllable sensor faults.
- `wrappers/e2o_localization_fusion`: health monitor, metric alignment, continuity-preserving failover, TF ownership, recording, and navigation velocity gate.
- `evaluation`: ATE/RPE, trajectory plots, switching metrics, and health/sensor timelines.

All other algorithms and non-E2O dataset integrations were removed. See `CHANGES.md` for the complete path-by-path inventory.

## Build

```bash
./build.sh all
# or independently
./build.sh fusion
./build.sh fast_livo2
./build.sh orbslam3
```

Docker sources are pinned in `UPSTREAM_LOCK.md`. No native source tree is stored in this repository; the Docker builds clone exact refs.

## Run

```bash
./run.sh fast_livo2 e2o /path/to/one_loop.bag
./run.sh orbslam3 e2o /path/to/one_loop.bag
./run.sh fusion e2o /path/to/one_loop.bag
./run.sh fusion_navigation e2o /path/to/one_loop.bag
```

Test each native estimator independently with its own RViz view:

```bash
./test_estimators.sh run fast
./test_estimators.sh run orb

# After each run, use the output path printed by run.sh:
./test_estimators.sh verify fast data/output/<fast_run_id>
./test_estimators.sh verify orb data/output/<orb_run_id>
```

Useful overrides:

```bash
RVIZ=true BAG_RATE=0.5 ./run.sh fusion e2o /path/to/one_loop.bag
PRIMARY_SOURCE=orbslam3 ./run.sh fusion e2o /path/to/one_loop.bag
TF_MODE=map_to_odom NAVIGATION_LAUNCH_FILE=/workspace/path/to/nav.launch \
  ./run.sh fusion_navigation e2o /path/to/one_loop.bag
```

`TF_MODE=direct` is the default and is appropriate when no independent wheel-odometry TF exists. `TF_MODE=map_to_odom` requires another component to own `odom -> base_link`.

## Outputs

- `/fused_localization/odometry`
- `/fused_localization/pose`
- `/fused_localization/path`
- `/fused_localization/status`
- `/fused_localization/active_source`
- `/fused_localization/events`
- `/fused_localization/navigation_ok`
- `/localization_health/{fast_livo2,orbslam3,summary,diagnostics}`

Each run creates `data/output/<run_id>/` containing independent trajectories, event logs, the combined timeline, metadata, and optional map output.

## Evaluation

```bash
./evaluation/evaluate.sh data/output/<run_id>
# Explicit reference selection:
./evaluation/evaluate.sh data/output/<run_id> data/e2o/ground_truth/one_loop_gps_enu.csv
./evaluation/evaluate.sh data/output/<run_id> data/e2o/ground_truth/one_loop_fastlivo2_reference.csv
```

The included GPS reference has meter-level uncertainty and untrusted yaw. The FAST-LIVO2-derived reference is not independent and cannot support a claim that FAST-LIVO2 is accurate. Reports state these limitations explicitly.

## Validation and failure testing

```bash
./tests/static_validation.sh
FAULT_INJECTION=true ./run.sh fusion e2o /path/to/one_loop.bag
# From another ROS-configured shell:
./tests/failure_control.sh fast_freeze
./tests/failure_control.sh fast_recover
./tests/failure_control.sh camera_drop
./tests/failure_control.sh camera_recover
```

Read `RUNNING.md`, `FUSION_AND_FALLBACK.md`, `TF_TREE.md`, and `FAILURE_TESTING.md` before using the output for navigation.

## Calibration warning

The supplied camera intrinsics and LiDAR-to-camera calibration are retained. IMU-to-LiDAR extrinsics and sensor time offsets were not independently measured in the archive and are currently explicit identity/zero assumptions. Replace them before treating results as final. See `configs/e2o/assumptions.yaml`.
