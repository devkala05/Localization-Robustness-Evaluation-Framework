# Run Guide

Run commands from:

```bash
cd /home/devil/Desktop/car/localisation/fast_lio2_complete
```

## Build FAST-LIO2

```bash
./build.sh
```

Clean rebuild only when needed:

```bash
./build.sh --no-cache
```

The FAST-LIO2 build checks the UrbanNav bag, ground-truth file, FAST-LIO2 wrapper, custom messages, benchmark scripts, and perturbation YAML files.

## Build LVI-SAM

```bash
./build_lvisam.sh
```

Clean rebuild only when needed:

```bash
./build_lvisam.sh --no-cache
```

LVI-SAM uses its own Docker image and dependencies, including Ceres and GTSAM. It shares the common benchmark wrappers and configs from this same folder.

## Visualise Only

```bash
./run.sh --visualise=true
```

This does not run FAST-LIO2. It starts RViz and plays the rosbag so you can inspect LiDAR, camera, ground truth, moving car pose, and rosbag time.

tmux windows:

```text
Ctrl-B 0 = roscore, TF, custom bridge, adapter
Ctrl-B 1 = rosbag playback
Ctrl-B 2 = status and /clock
Ctrl-B 3 = RViz
Ctrl-B d = detach
```

To pause/resume playback, switch to the rosbag tmux window and press Space. RViz shows time but does not control `rosbag play`.

## Run FAST-LIO2 Baseline

```bash
./run.sh --algo fastlio2 --per 0
```

This runs FAST-LIO2 on the exact dataset without perturbations.

Output:

```text
data/results/fast_lio2/per_0/trajectory.csv
```

## Run FAST-LIO2 Perturbations

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
data/results/fast_lio2/per_1/trajectory.csv
data/results/fast_lio2/per_2/trajectory.csv
...
data/results/fast_lio2/per_6/trajectory.csv
```

tmux windows:

```text
Ctrl-B 0 = roscore, TF, custom bridge, perturbation adapter
Ctrl-B 1 = FAST-LIO2 and CSV recorder
Ctrl-B 2 = rosbag playback
Ctrl-B 3 = live topic status/rates and CSV row count
Ctrl-B 4 = RViz
Ctrl-B d = detach
```

To reduce RViz lag, the adapted LiDAR topic is enabled by default. Raw bag LiDAR and registered clouds are available but disabled in RViz.

## Evaluate

Full bag:

```bash
./run.sh --algo fastlio2 --per 0 --eval
```

Short test:

```bash
./run.sh --algo fastlio2 --per 0 --eval --duration 10
```

`--summary` and `--evaluate` are aliases for `--eval`.

Evaluation mode runs the bag once, records the FAST-LIO2 output, closes ROS/RViz when playback ends, and writes plots plus text reports.

Output example:

```text
data/results/fast_lio2/per_1_fast_lio2_20260609_153012/
  trajectory.csv
  metrics.json
  analysis.txt
  trajectory_baseline_vs_run.png
  component_errors_over_time.png
  segment_rmse.png
  segment_component_rmse.png
  perturbation_window_component_rmse.png
  error_timeseries.csv
  segment_metrics.csv
  perturbation_window_metrics.csv
```

`analysis.txt` includes overall error, worst x/y/z/yaw component, scene-by-scene error from `road_segments.yaml`, and perturbation-window analysis for `per_1` to `per_6`.

It also updates:

```text
data/results/fast_lio2/per_<N>/trajectory.csv
data/results/fast_lio2/robustness_ranking.txt
```

## Edit Inputs

Road segments:

```text
wrappers/localization_benchmark/config/road_segments.yaml
```

Perturbation cases:

```text
wrappers/localization_benchmark/config/perturbations/per_0.yaml
wrappers/localization_benchmark/config/perturbations/per_1.yaml
...
wrappers/localization_benchmark/config/perturbations/per_6.yaml
```

Supported perturbations:

```text
lidar: point_dropout, scan_dropout, range_noise, rain, sensor_off
imu: bias, gaussian_noise, dropout, sensor_off
camera_right: low_light, rain, motion_blur, frame_dropout, sensor_off
```

## LVI-SAM

LVI-SAM runs from this same folder, but with separate command files and Docker image.

```bash
./build_lvisam.sh
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

Output:

```text
data/results/lvi_sam/per_<N>/trajectory.csv
data/results/lvi_sam/robustness_ranking.txt
```

The LVI-SAM runner reuses the common bridge, perturbation adapter, RViz config, recorder, evaluator, road segments, and perturbation YAML files.
