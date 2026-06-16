# Adaptive-W LVIO Integration Notes

Adaptive-W LVIO is now an independent benchmark frontend. It no longer launches
FAST-LIO2 and no longer subscribes to `/Odometry`.

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

## Architecture

```text
UrbanNav bag
  /velodyne_points
  /imu/data
  /zed2/camera/right/image_raw
        │
        ▼
localization_benchmark bridge + perturbation adapter
  /cloud_registered_raw
  /livox/imu
  /camera/right/image_raw
        │
        ▼
Adaptive-W LVIO node
  LiDAR scan-to-scan ICP + IMU yaw prior + camera/IMU/LiDAR health weighting
        │
        ▼
/adaptive_w_lvio/odometry/mapping
/adaptive_w_lvio/mapping/path
/adaptive_w_lvio/cloud_registered
/adaptive_w_lvio/debug/weights
        │
        ▼
localization_output_recorder
  /data/results/adaptive_w_lvio/per_N/trajectory.csv
```

## Important note

This is still a lightweight benchmark implementation, not the original paper's
full GTSAM/eigendecomposition estimator. But it is now doing localisation itself
from LiDAR/IMU/camera streams instead of wrapping FAST-LIO2 output.
