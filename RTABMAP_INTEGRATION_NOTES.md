# RTAB-Map Integration

Added RTAB-Map as a third benchmarked algorithm using FAST-LIO2 as the odometry frontend.

## Commands

```bash
./build_rtabmap.sh
./run_rtabmap.sh --per 0
./run_rtabmap.sh --per 0 --eval
./run_rtabmap.sh --per 1 --eval --duration 20
```

`run.sh` also accepts RTAB-Map when the FAST-LIO2 image has been rebuilt with the updated Dockerfile:

```bash
./build.sh
./run.sh --algo rtabmap --per 0
./run.sh --algo rtabmap --per 0 --eval
```

## Topics

RTAB-Map consumes:

- `/Odometry` from FAST-LIO2, converted to `/rtabmap/input_odom`
- `/cloud_registered_raw` as `scan_cloud`

Benchmark output:

- `/rtabmap/odometry/mapping`
- `/rtabmap/mapping/path`
- `/rtabmap/cloud_map`
- `/data/results/rtab_map/per_N/trajectory.csv`

The adapter applies RTAB-Map's `map -> odom` correction when available so the recorded odometry follows the RTAB-Map map frame.
