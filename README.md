# E2O Localization Robustness Evaluation Framework

ROS Noetic / Docker framework for running E2O localization estimators with external health monitoring, fusion, and fault injection.
Native estimator code lives inside Docker images. This repository owns the E2O wrappers, sensor adapter, health checks, fusion supervisor, run scripts, RViz profiles, and evaluation tools.

---

## Algorithms

| Mode | Estimators | Sensors | Main output |
|---|---|---|---|
| `fast_livo2` | FAST-LIVO2 | LiDAR + Camera + IMU | `/fast_livo2/odometry` |
| `orbslam3` | ORB-SLAM3 | Front camera + Depth + IMU | `/orbslam3/camera_odometry` |
| `lvisam` | LVI-SAM | LiDAR + IMU | `/lvisam/odometry` |
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
./build.sh all --no-cache   # force clean rebuild
```

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
