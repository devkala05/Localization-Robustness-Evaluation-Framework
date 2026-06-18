# Adaptive-W LVIO / LVIO-Fusion

Adaptive-W LVIO is now integrated through the upstream `jypjypjypjyp/lvio_fusion` ROS packages. The benchmark wrapper launches the native `lvio_fusion_node`; it no longer runs the previous custom Python ICP estimator and it does not subscribe to FAST-LIO2 `/Odometry`.

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
/camera/left/image_raw
/camera/right/image_raw
```

The adapter publishes stereo camera data, LiDAR and IMU. The native config is `wrappers/adaptive_w_lvio_urbannav/config/lvio_fusion_urbannav.yaml`.

## Native Output And Benchmark Output

```text
/lvio_fusion_node/path                 # native path from upstream LVIO-Fusion
/adaptive_w_lvio/odometry/mapping      # benchmark Odometry republished from native path
/adaptive_w_lvio/mapping/path          # benchmark Path republished from native path
/adaptive_w_lvio/odometry/local
/adaptive_w_lvio/path/local
/adaptive_w_lvio/odometry/output
/adaptive_w_lvio/path/output
```

Results are written to `data/results/adaptive_w_lvio/`.

## Notes

`use_adapt` is kept disabled in the default config because the upstream actor-critic/RL component requires extra old Torch-era dependencies and trained-policy setup that is not bundled with this benchmark image. The launched estimator is still the native upstream LVIO-Fusion frontend/backend; only the final path-to-odometry republisher is custom.
