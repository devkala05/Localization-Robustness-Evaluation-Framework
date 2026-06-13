# UrbanNav Localization Benchmark

Research-grade ROS1/Noetic Docker benchmark for UrbanNav-HK TST localization under perturbations.

## Build

```bash
./build_fastlio2.sh
./build_lvisam.sh
./build_fastlivo2.sh
./build_rtabmap.sh
./build_adaptive_w_lvio.sh
./build_orbslam3.sh
./build_r3live.sh
```

## Run

```bash
./run --algo <name> --per <0..6> --gps off --eval --duration 30
./run --algo <name> --per <0..6> --gps on  --eval --duration 30
```

Canonical names: `fastlio2`, `lvisam`, `fastlivo2`, `rtabmap`, `adaptive_w_lvio`, `orbslam3`, `r3live`.

GPS-on defaults to `data/gnss/urbannav_tst_gnss.csv`.

## TF policy

Single dynamic TF authority: `standard_output_republisher.py` publishes `camera_init -> body`. Algorithm-native dynamic TF is disabled or remapped. Static calibration publishes `map -> camera_init` and `body -> sensors/gnss_antenna`.

## Output contract

Every algorithm publishes:

```text
/<algo>/odometry/local
/<algo>/path/local
/<algo>/odometry/output
/<algo>/path/output
/<algo>/status
```
