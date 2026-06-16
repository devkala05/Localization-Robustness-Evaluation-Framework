# RTAB-Map Integration

Added RTAB-Map as a third benchmarked algorithm using FAST-LIO2 as the odometry frontend.

## Commands

```bash
./build_rtabmap.sh
./run --algo rtabmap --per 0
./run --algo rtabmap --per 0 --eval
./run --algo rtabmap --per 1 --eval --duration 20
```

`./run --algo rtabmap` runs RTAB-Map after the RTAB-Map image has been built:

```bash
./build_fastlio2.sh
./run --algo rtabmap --per 0
./run --algo rtabmap --per 0 --eval
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
