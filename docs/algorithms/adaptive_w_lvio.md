# Adaptive-W LVIO Integration Notes

Adaptive-W LVIO was added as a fifth benchmark algorithm using the same
repository conventions as FAST-LIO2, LVI-SAM, FAST-LIVO2, and RTAB-Map.

## Build

```bash
./build_adaptive_w_lvio.sh
./build_adaptive_w_lvio.sh --no-cache
```

## Run

```bash
./run --algo adaptive_w_lvio --per 0
./run --algo adaptive_w_lvio --per 0 --eval
./run --algo adaptive_w_lvio --per 1 --eval --duration 20
```

Generic runner support is also enabled:

```bash
./run --algo adaptive_w_lvio --per 0
./run --algo adaptive_w_lvio --per 0 --eval
```

## Architecture

```text
UrbanNav bag
  /velodyne_points
  /imu/data
  /zed2/camera/right/image_raw
        │
        ▼
localization_benchmark bridge + custom_fastlio_adapter
  /cloud_registered_raw
  /livox/imu
  /camera/right/image_raw
        │
        ▼
FAST-LIO2 frontend
  /Odometry
  /path
        │
        ▼
Adaptive-W LVIO node
  subscribes: /Odometry, /cloud_registered_raw, /camera/right/image_raw, /livox/imu
  publishes:  /adaptive_w_lvio/odometry/mapping
              /adaptive_w_lvio/mapping/path
              /adaptive_w_lvio/cloud_registered
              /adaptive_w_lvio/debug/weights
        │
        ▼
localization_output_recorder
  /data/results/adaptive_w_lvio/per_N/trajectory.csv
```

## Adaptive-W behavior

The node computes LiDAR, visual, and IMU health weights from timestamp recency
and LiDAR cloud density. When all streams are healthy, it passes FAST-LIO2 pose
through unchanged. During camera/IMU/cloud gaps or sparse LiDAR, it adaptively
smooths pose increments so the recorded output stays stable instead of jumping
on stale/asynchronous measurements.

This keeps the benchmark flow deterministic while exposing the adaptive weights
on `/adaptive_w_lvio/debug/weights` for debugging.


## Academic/reporting disclaimer

Adaptive-W LVIO in this repository is a Python smoothing relay on FAST-LIO2 output. It is not the paper's GTSAM + eigendecomposition estimator. The benchmark result should be described as adaptive pose smoothing under sensor gaps, not degeneracy-aware weight transfer.
