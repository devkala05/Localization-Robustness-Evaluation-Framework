# Run Guide

Use one runner for every algorithm:

```bash
./run --algo <name> --per <0..6> --gps <on|off> [--eval] [--duration seconds]
```

Canonical algorithm names:

```text
fastlio2
lvisam
fastlivo2
rtabmap
adaptive_w_lvio
orbslam3
r3live
```

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

## Run examples

```bash
./run --algo fastlio2 --per 0 --gps off --eval --duration 30
./run --algo adaptive_w_lvio --per 0 --gps on --eval --duration 30
./run --algo orbslam3 --per 0 --gps off --orb-mode stereo --eval
```

## Data

Required:

```text
data/UrbanNav-HK_TST-20210517_sensors.bag
data/UrbanNav_TST_GT_raw.txt
```

Optional GPS CSV:

```text
data/gnss/urbannav_tst_gnss.csv
```

## Standard outputs

```text
/<algo>/odometry/local
/<algo>/path/local
/<algo>/odometry/output
/<algo>/path/output
/<algo>/status
```
