# Localization Robustness Evaluation Framework — UrbanNav + E2O

ROS1 Noetic/Docker benchmark for seven localization integrations under repeatable sensor perturbations. The original UrbanNav workflow is preserved, and the same framework can now run the E2O Faculty Loop dataset through a minimally invasive adapter layer.

## Algorithms

```text
fastlio2  lvisam  fastlivo2  rtabmap  adaptive_w_lvio  orbslam3  r3live
```

## E2O setup

Place the external bag here:

```text
data/e2o/raw/one_full_loop.bag
```

The supplied TUM reference is already located at:

```text
data/e2o/ground_truth/one_full_loop_gt.tum
```

Build all images or one image:

```bash
./build.sh all
./build.sh fastlio2
```

Inspect the actual bag before running algorithms:

```bash
./inspect_bag.sh --dataset e2o --strict
```

Run an interactive baseline:

```bash
./run.sh --dataset e2o --algo fastlio2 --per 0 --gps off
```

Run and evaluate a complete bag or a short smoke test:

```bash
./run.sh --dataset e2o --algo fastlio2 --per 0 --gps off --eval
./run.sh --dataset e2o --algo fastlio2 --per 0 --gps off --eval --duration 60
```

Repeat by changing `--algo`. E2O defaults to `/lidar103/velodyne_points`, `/mavros/imu/data`, and `/camera/color/image_raw`.

## UrbanNav compatibility

```bash
./run.sh --dataset urbannav --algo fastlio2 --per 0 --gps off --eval
```

## Standard output contract

Every integration publishes:

```text
/<algo>/odometry/local
/<algo>/path/local
/<algo>/odometry/output
/<algo>/path/output
/<algo>/status
```

Results are separated by dataset:

```text
data/results/e2o/<algorithm>/...
data/results/urbannav/<algorithm>/...
```

## Calibration warning

The E2O archive contains front-camera intrinsics and lidar103↔camera calibration, but not a verified IMU↔LiDAR transform, IMU noise model, point-time convention, or independent survey-grade ground truth. Identity/zero values are explicitly marked provisional. Read [E2O_ADAPTATION.md](E2O_ADAPTATION.md) before interpreting benchmark scores.
