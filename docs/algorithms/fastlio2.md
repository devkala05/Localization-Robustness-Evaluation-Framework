# FAST-LIO2

FAST-LIO2 is the base LiDAR-inertial benchmark image and provides shared ROS package dependencies used by several wrappers.

## Build And Run

```bash
./build_fastlio2.sh
./run --algo fastlio2 --per 0 --gps off --eval
./run --algo fastlio2 --per 0 --gps on --eval
```

## Inputs

```text
/cloud_registered_raw
/livox/imu
```

UrbanNav `/velodyne_points` and `/imu/data` are bridged through the common custom message path and adapted for FAST-LIO2.

## Outputs

```text
/Odometry
/fastlio2/odometry/local
/fastlio2/path/local
/fastlio2/odometry/output
/fastlio2/path/output
/fastlio2/status
```

Results are written to `data/results/fast_lio2/`.

## Notes

FAST-LIO2 has no native GPS input in this wrapper. `--gps on` uses the shared external GPS provider, quality gate, and fusion/output selection pipeline.
