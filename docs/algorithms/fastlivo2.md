# FAST-LIVO2

FAST-LIVO2 is integrated through `wrappers/fast_livo2_wrapper` and uses the same perturbation, GPS, recording, and evaluation pipeline as the other algorithms.

## Build And Run

```bash
./build_fastlivo2.sh
./run --algo fastlivo2 --per 0 --gps off --eval
./run --algo fastlivo2 --per 0 --gps on --eval
```

## Inputs

```text
/livox/lidar
/livox/imu
/camera/right/image_raw
```

The benchmark adapter converts UrbanNav Velodyne point time from seconds to microseconds with `point_time_scale: 1000000.0`.

## Outputs

```text
/fast_livo2/odometry
/fastlivo2/odometry/local
/fastlivo2/path/local
/fastlivo2/odometry/output
/fastlivo2/path/output
```

Results are written to `data/results/fast_livo2/`.

## Point-Time Rule

The benchmark `./run --algo fastlivo2` path applies point-time scaling exactly once in `custom_fastlio_adapter.launch`. Do not run the standalone `fast_livo2_wrapper/topic_bridge_node.py` on the same input cloud at the same time, because that direct bridge also has seconds-to-microseconds conversion logic.
