# UrbanNav Localization Perturbation Benchmark

This folder contains both algorithm runners. FAST-LIO2 and LVI-SAM build into separate Docker images and run through separate command files, but they share the same dataset, custom bridge, perturbation configs, RViz config, recorder, evaluator, and result folder.

```text
data/results/
```

## Data Flow

```text
UrbanNav rosbag
  /velodyne_points
  /imu/data
  /zed2/camera/right/image_raw
        |
        v
custom bridge
  /mycar/lidar/custom_points
  /mycar/imu/custom_imu
  /mycar/camera/right/custom_image
        |
        v
perturbation adapter, selected by --per N
  /cloud_registered_raw
  /livox/imu
  /camera/right/image_raw
        |
        v
FAST-LIO2 or LVI-SAM
  algorithm odometry topic
        |
        v
CSV recorder + RViz + evaluator
```

## Build FAST-LIO2

```bash
cd /home/devil/Desktop/car/localisation/fast_lio2_complete
./build.sh
```

## Build LVI-SAM

```bash
cd /home/devil/Desktop/car/localisation/fast_lio2_complete
./build_lvisam.sh
```

## Visualise Dataset

```bash
./run.sh --visualise=true
```

This opens RViz and plays the bag with LiDAR, camera, ground truth, moving car pose, and the rosbag `/clock` marker.

## Run FAST-LIO2

No perturbation:

```bash
./run.sh --algo fastlio2 --per 0
```

Perturbation cases:

```bash
./run.sh --algo fastlio2 --per 1
./run.sh --algo fastlio2 --per 2
./run.sh --algo fastlio2 --per 3
./run.sh --algo fastlio2 --per 4
./run.sh --algo fastlio2 --per 5
./run.sh --algo fastlio2 --per 6
```

Outputs:

```text
data/results/fast_lio2/per_<N>/trajectory.csv
```

## Run LVI-SAM

No perturbation:

```bash
./run_lvisam.sh 0
```

Perturbation cases:

```bash
./run_lvisam.sh 1
./run_lvisam.sh 2
./run_lvisam.sh 3
./run_lvisam.sh 4
./run_lvisam.sh 5
./run_lvisam.sh 6
```

Outputs:

```text
data/results/lvi_sam/per_<N>/trajectory.csv
```

## Evaluate

Full bag:

```bash
./run.sh --algo fastlio2 --per 0 --eval
```

Short smoke test:

```bash
./run.sh --algo fastlio2 --per 0 --eval --duration 10
```

Evaluation writes a dated folder:

```text
data/results/fast_lio2/per_<N>_fast_lio2_<YYYYMMDD_HHMMSS>/
```

It contains `trajectory.csv`, `metrics.json`, `analysis.txt`, plots, segment metrics, perturbation-window metrics, and an updated robustness ranking.

## Perturbation Configs

Edit:

```text
wrappers/localization_benchmark/config/perturbations/per_0.yaml
wrappers/localization_benchmark/config/perturbations/per_1.yaml
...
wrappers/localization_benchmark/config/perturbations/per_6.yaml
```

`per_0.yaml` is clean data. `per_6.yaml` is reserved for full sensor on/off windows with `type: sensor_off`.

Use the cyan `BAG /clock` text in RViz for timestamps. Do not use ROS wall-time log prefixes.

## Main Files

```text
build.sh
run.sh
build_lvisam.sh
run_lvisam.sh
RUN_README.md
Dockerfile
docker/lvisam/Dockerfile
wrappers/fast-lio_urbannav/
wrappers/lvi_sam_urbannav/
wrappers/custom_localization_msgs/
wrappers/localization_benchmark/
wrappers/localization_benchmark/config/road_segments.yaml
wrappers/localization_benchmark/config/perturbations/per_*.yaml
algorithms/lvi_sam/
```
