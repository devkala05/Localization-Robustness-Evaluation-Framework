# Adaptive-W LVIO

Adaptive-W LVIO is integrated as an independent benchmark frontend. It consumes the common UrbanNav bridge/adapter topics and publishes benchmark-normalized odometry without wrapping FAST-LIO2 `/Odometry`.

## Build And Run

```bash
./build_adaptive_w_lvio.sh
./run --algo adaptive_w_lvio --per 0 --gps off --eval
./run --algo adaptive_w_lvio --per 0 --gps on --eval
```

## Inputs

```text
/cloud_registered_raw
/livox/imu
/camera/right/image_raw
```

The adapter publishes camera data and camera info for this integration.

## Outputs

```text
/adaptive_w_lvio/odometry/mapping
/adaptive_w_lvio/mapping/path
/adaptive_w_lvio/debug/weights
/adaptive_w_lvio/odometry/local
/adaptive_w_lvio/path/local
/adaptive_w_lvio/odometry/output
/adaptive_w_lvio/path/output
```

Results are written to `data/results/adaptive_w_lvio/`.

## Notes

This wrapper is a lightweight benchmark implementation: LiDAR scan-to-scan ICP with IMU yaw prior and adaptive camera/IMU/LiDAR health weighting. It is not the full original paper implementation.
