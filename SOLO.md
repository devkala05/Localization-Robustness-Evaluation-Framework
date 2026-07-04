# Standalone Algorithms

Run any single algorithm in isolation against the E2O rosbag.
Each mode starts its own container stack (roscore + sensor adapter + the algorithm + health monitor + trajectory recorder).

## Prerequisites

- Docker installed and running
- E2O rosbag with `/lidar103/velodyne_points`, `/mavros/imu/data`, `/camera/color/image_raw`, `/camera/depth/image_rect_raw`

Check the bag:
```bash
rosbag info /path/to/one_full_loop.bag
```

Build the images you need:
```bash
./build.sh all            # build everything
./build.sh fusion         # base image (health monitor / recorder)
./build.sh fast_livo2
./build.sh orbslam3
./build.sh lvisam
./build.sh all --no-cache # force clean rebuild
```

---

## FAST-LIVO2  (LiDAR + Camera + IMU)

Primary output: `/fast_livo2/odometry`

```bash
./run.sh fast_livo2 e2o /path/to/one_full_loop.bag
```

RViz is enabled by default. To disable it:
```bash
RVIZ=false ./run.sh fast_livo2 e2o /path/to/one_full_loop.bag
```

Slower playback:
```bash
BAG_RATE=0.3 ./run.sh fast_livo2 e2o /path/to/one_full_loop.bag
```

Save a PCD map:
```bash
FAST_SAVE_PCD=true ./run.sh fast_livo2 e2o /path/to/one_full_loop.bag
```

Custom config:
```bash
FAST_CONFIG=/path/to/my_config.yaml ./run.sh fast_livo2 e2o /path/to/one_full_loop.bag
```

Health topic: `/localization_health/fast_livo2`
Output directory: `data/output/<run_id>/`

---

## ORB-SLAM3  (Front Camera + Depth + IMU)

Runs in `RGBD_Inertial` mode. RGB is resized to the depth image dimensions by the sensor adapter.
Primary output: `/orbslam3/camera_odometry`

```bash
./run.sh orbslam3 e2o /path/to/one_full_loop.bag
```

RViz is enabled by default. To disable it:
```bash
RVIZ=false ./run.sh orbslam3 e2o /path/to/one_full_loop.bag
```

Custom camera config:
```bash
ORB_CONFIG=/path/to/my_orb.yaml ./run.sh orbslam3 e2o /path/to/one_full_loop.bag
```

Health topic: `/localization_health/orbslam3`
Tracking status: `/orbslam3/tracking_status`

---

## LVI-SAM  (LiDAR + IMU only)

Runs with `enable_visual=false` — visual nodes are not started.
Primary output: `/lvisam/odometry`

```bash
./run.sh lvisam e2o /path/to/one_full_loop.bag
```

RViz is enabled by default. To disable it:
```bash
RVIZ=false ./run.sh lvisam e2o /path/to/one_full_loop.bag
```

Custom configs:
```bash
LVISAM_LIDAR_CONFIG=/path/to/lidar.yaml \
LVISAM_CAMERA_CONFIG=/path/to/camera.yaml \
./run.sh lvisam e2o /path/to/one_full_loop.bag
```

Enable visual mode (if you have the visual nodes built):
```bash
LVISAM_ENABLE_VISUAL=true ./run.sh lvisam e2o /path/to/one_full_loop.bag
```

Health topic: `/localization_health/lvisam`

---

## Environment variables (all modes)

| Variable | Default | Description |
|---|---|---|
| `BAG_RATE` | `1.0` | Rosbag playback speed |
| `RVIZ` | `true` | Launch RViz |
| `RVIZ_CONFIG` | mode-specific | Path to `.rviz` file |
| `LIDAR_TOPIC` | `/lidar103/velodyne_points` | Raw LiDAR topic in bag |
| `IMU_TOPIC` | `/mavros/imu/data` | Raw IMU topic in bag |
| `CAMERA_TOPIC` | `/camera/color/image_raw` | Raw RGB topic in bag |
| `DEPTH_TOPIC` | `/camera/depth/image_rect_raw` | Raw depth topic in bag |
| `SENSOR_CONFIG` | `wrappers/localization_benchmark/config/e2o.yaml` | Sensor adapter config |
| `EVALUATE_AFTER_RUN` | `true` | Run evaluator when bag finishes |
| `EVAL_GT` | `data/e2o/ground_truth/ref.csv` | Ground truth CSV |

---

## Verify a completed run

```bash
python3 tests/verify_estimator_run.py fast_livo2 data/output/<run_id>
python3 tests/verify_estimator_run.py orbslam3  data/output/<run_id>
```

Check static configuration:
```bash
./tests/static_validation.sh
```
