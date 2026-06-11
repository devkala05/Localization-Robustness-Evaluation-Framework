# FAST-LIVO2 integration

Added from `example.zip` into this combined FAST-LIO2 + LVI-SAM codebase.

Commands:

```bash
./build_fastlivo2.sh
./run_fastlivo2.sh --per 0
./run_fastlivo2.sh --per 0 --eval
./run_fastlivo2.sh --per 1 --eval --duration 20
```

FAST-LIVO2 uses the same perturbation/evaluation framework as FAST-LIO2:

- Input bag topics: `/velodyne_points`, `/imu/data`, `/zed2/camera/right/image_raw`
- Perturbed/native topics: `/livox/lidar`, `/livox/imu`, `/camera/right/image_raw`
- Output recorded for evaluation: `/Odometry`
- Result folder: `/data/results/fast_livo2/per_X/trajectory.csv`

The adapter preserves bag timestamps. For FAST-LIVO2 only, it converts the Velodyne per-point `time` field from seconds to microseconds using `point_time_scale: 1000000.0`, matching the working reference wrapper.
