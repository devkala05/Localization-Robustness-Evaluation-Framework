# ORB-SLAM3 UrbanNav Integration

Added ORB-SLAM3 as a benchmark module using the same runner/result structure as the other algorithms.

## Build

```bash
./build_orbslam3.sh
./build_orbslam3.sh --no-cache
```

The first build compiles Pangolin and ORB-SLAM3, so it is much heavier than wrapper-only builds.

## Run

```bash
./run --algo orbslam3 --per 0
./run --algo orbslam3 --per 0 --eval
./run --algo orbslam3 --per 1 --eval --duration 20
```

Generic dispatcher also works:

```bash
./run --algo orbslam3 --per 0
./run --algo orbslam3 --per 0 --eval
```

## Mode

Default is stereo for metric-scale localisation:

```bash
ORB_MODE=stereo ./run --algo orbslam3 --per 0 --eval
```

Monocular is available, but scale may drift and metric evaluation is usually not reliable:

```bash
ORB_MODE=mono ./run --algo orbslam3 --per 0
```

## Topics

Input from adapter:

```text
/camera/left/image_raw
/camera/right/image_raw
```

Benchmark output:

```text
/orbslam3/odometry/mapping
/orbslam3/mapping/path
/orbslam3/tracking_status
```

Results:

```text
/data/results/orb_slam3/per_N/trajectory.csv
```
