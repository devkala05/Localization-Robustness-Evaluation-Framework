# Final implementation report

## Scope completed

The supplied archive was reduced to an E2O-only framework with two localization estimators: native FAST-LIVO2 and native monocular ORB-SLAM3. Fusion, health monitoring, frame alignment, switching, TF ownership, recording, navigation gating, and fault injection were added as external ROS nodes.

This report distinguishes **implemented/static-tested** behavior from **runtime-validated** behavior. The execution environment used for this modification had no Docker executable, ROS installation, or E2O `.bag` file, so native image builds, live topics, TF, and failure scenarios could not be executed here. They remain mandatory target-machine acceptance tests.

## Original repository structure

The archive contained:

- an `algorithms/` source area;
- Docker definitions for FAST-LIVO2, ORB-SLAM3, and several other estimators;
- dataset/benchmark scripts covering E2O and non-E2O paths;
- wrappers for FAST-LIO, FAST-LIVO2, ORB-SLAM3, RTAB-Map, R3LIVE, LVI-SAM, and an adaptive LVIO integration;
- shared custom messages, perturbation tools, RViz comparisons, GPS helpers, batch-run outputs, and historical documentation.

The full original path inventory and every removed path are in `CHANGES.md`.

## Components removed

- Every estimator other than FAST-LIVO2 and ORB-SLAM3.
- All non-E2O launch/configuration/evaluation paths.
- Old multi-algorithm orchestration, perturbation and batch tooling.
- Obsolete custom messages and algorithm-specific adapters.
- Duplicate/historical RViz, documentation, generated caches, output artifacts, and Git metadata.
- Dockerfiles and build aliases for removed estimators.

## Components retained or adapted

- E2O camera intrinsics and front-camera/LiDAR calibration values.
- E2O raw topics: middle LiDAR, MAVROS IMU, and front color camera.
- Two existing E2O reference CSV files, with provenance warnings.
- Pinned upstream-native estimator build approach.
- FAST-LIVO2 native odometry normalization and ORB-SLAM3 native camera-pose exposure, rewritten into E2O-only wrappers.

## Components added

- `e2o_sensor_adapter.py`: E2O topic normalization, PointCloud2 time conversion, camera info, and sensor fault gates.
- `e2o_static_tf_publisher.py`: sensor-only static TF.
- `localization_health_monitor.py`: independent sensor/estimator health.
- `fusion_node.py`: metric trajectory alignment, consistency checking, state machine, continuity transforms, blending, authoritative TF, and explicit failure state.
- `cmd_vel_safety_gate.py`: zero-velocity enforcement when localization is invalid/stale.
- trajectory/timeline recorder and evaluator.
- pose fault injectors and sensor/process failure controls.
- reproducible build/run interface, RViz, static/synthetic tests, and documentation.

## Fusion architecture

The selected approach is health-gated primary selection with secondary consistency checking and external metric trajectory alignment. It was chosen instead of an EKF because ORB-SLAM3 monocular translation has unknown scale and the two wrappers do not expose consistently meaningful covariance/residual models.

FAST-LIVO2 is primary. During healthy synchronized overlap, ORB camera poses are aligned to FAST base poses using orientation alignment, positive scalar translation scale, world translation, and the known camera-to-base extrinsic. Scale/alignment are accepted only inside configured bounds and RMSE thresholds. The accepted similarity is held fixed while ORB is active so ongoing re-estimation cannot move the output without a switch.

At every source switch, the new source is transformed so its current metric pose equals the last fused pose. A time-based SE(3) interpolation then transitions toward the moving new-source trajectory. This guarantees zero intended pose jump at the switch instant; logged `pose_jump_m` verifies the realized handoff.

## Source-selection state machine

- Wait for a stable healthy usable source.
- Prefer FAST-LIVO2.
- On persistent FAST failure, use ORB only if ORB is healthy and metric alignment is validated.
- On ORB failure, continue FAST without interruption.
- On both failures, stop fused pose/TF updates and set navigation invalid.
- On recovery, require stabilization, minimum dwell, and stricter cross-source consistency before returning to the primary.
- Large disagreement while both remain individually healthy is reported as degraded; the system does not pretend it can identify the faulty estimator from disagreement alone.

## Health criteria

FAST-LIVO2 and ORB-SLAM3 are checked for pose freshness/rate, process presence, finite pose, monotonic timestamps, frozen output, discontinuities, unrealistic linear/angular motion, acceleration, and required sensor health. ORB additionally requires current tracking status. Sensor health includes receipt age, timestamp lag/future stamps, regression, and duplicate/frozen stamps.

FAST-LIVO2 currently requires LiDAR, IMU, and camera. The implementation does not assume a safe native LIO-only or VIO-only fallback. Any relaxation requires runtime proof using the pinned native source/configuration.

## TF ownership

Default direct mode:

```text
map -> odom                 fusion, static identity
odom -> base_link           fusion, dynamic fused pose
base_link -> sensor frames  E2O static TF publisher
```

Map-to-odom mode instead assigns `odom -> base_link` to an existing external odometry source and makes fusion own `map -> odom`. Native estimator TF topics are remapped away from the authoritative TF channels. See `TF_TREE.md`.

## Navigation integration

The original archive did not include a concrete navigation planner/controller. The implementation therefore provides a strict integration contract:

- navigation consumes fused localization/TF only;
- controller output is remapped to `/cmd_vel_unfiltered`;
- the safety gate is the only publisher to `/cmd_vel`;
- localization failure or stale health forces zero velocity.

A user-supplied launch file can be included through `NAVIGATION_LAUNCH_FILE`. Runtime validation with that actual stack is still required.

## Evaluation

The recorder stores FAST-LIVO2, ORB-SLAM3, and fused trajectories independently, plus health/status/events/navigation state. The evaluator computes ATE/RPE, uses Sim(3) for raw monocular ORB and SE(3) for metric trajectories, plots source/health/sensor timelines, and reports switch count, source duration, pose jump, and availability fractions.

Reference caveats:

- `one_loop_fastlivo2_reference.csv` is estimator-derived, explicitly states no external ground truth, and was generated with vision disabled (`img_en=0`); it is not an independent validation reference for current FAST-LIVO2.
- `one_loop_gps_enu.csv` has meter-level covariance and untrusted yaw; rotational RPE is therefore disabled when it is selected.

## Test evidence produced here

Passed:

- Python byte-code compilation for every Python file.
- XML parsing for all ROS launch/package files.
- YAML parsing for standard YAML files.
- `bash -n` for every shell entry point.
- repository scan confirming no removed estimator or non-E2O integration reference remains outside historical change reporting.
- calibration consistency checks across central camera config, FAST-LIVO2, ORB-SLAM3, and fusion extrinsics.
- synthetic fusion-math test with exact recovery of known monocular scale, world transform, camera lever arm, and quaternion interpolation.
- synthetic evaluator test: all three trajectories valid, monocular Sim(3) scale recovered, ATE RMSE below `1e-8`, and plot/report output generated.
- ORB-SLAM3 launcher regression test confirming that ROS remapping arguments survive the Python-to-native `exec` boundary.
- health-state regression test confirming duplicate, regressed, and non-finite pose timestamps are rejected without corrupting the forward kinematic baseline.
- configuration validation confirming the ORB camera/base convention, centralized E2O calibration values, topic wiring, and authoritative-TF settings are internally consistent.

Not executable in this environment:

- Docker image builds (Docker command unavailable).
- ROS node/launch tests (ROS unavailable).
- E2O bag replay (no bag supplied in the archive/runtime).
- live `rostopic`, `rosnode`, `roswtf`, TF graph, RViz, and navigation checks.
- real sensor/estimator failure and recovery matrix.

## Known limitations and remaining risks

1. ORB fallback is intentionally unavailable until healthy overlap provides validated metric scale. A FAST failure before that point results in a safe failed state.
2. Monocular scale can drift after alignment; consistency monitoring detects divergence but does not perform full map merging.
3. IMU-to-LiDAR extrinsic is assumed identity and time offsets are assumed zero. These are accuracy-critical.
4. The E2O LiDAR ring count and point-time unit are based on existing framework assumptions and need bag inspection.
5. Native Docker refs are pinned but their current Dockerfiles were not built in this environment; upstream build compatibility must be confirmed.
6. The ORB ROS-example patch is interface-only but must be reviewed against the exact pinned source during build.
7. Continuity preserves handoff pose, not absolute global correctness of a drifted backup.
8. Large disagreement cannot by itself identify which estimator is wrong.
9. The actual navigation stack was absent and must be integrated/tested on the target robot or simulator.
10. Included references are not survey-grade ground truth.

## Acceptance gate before claiming operational fusion/fallback

Run `./build.sh all`, every launch mode, `./scripts/diagnose_runtime.sh`, all scenarios in `FAILURE_TESTING.md`, and evaluation on the actual E2O bag. Preserve container logs, topic-rate output, `roswtf`, `frames.pdf`, source-switch events, and navigation-stop evidence. Only after those checks pass should the system be described as runtime-validated.
