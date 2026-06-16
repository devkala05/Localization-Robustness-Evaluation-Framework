# RTAB-Map

RTAB-Map is integrated as a map-level correction layer using FAST-LIO2 odometry as its odometry prior plus the UrbanNav right camera and scan cloud.

## Build And Run

```bash
./build_rtabmap.sh
./run --algo rtabmap --per 0 --gps off --eval
./run --algo rtabmap --per 0 --gps on --eval
```

## Inputs

```text
/rtabmap/input_odom
/cloud_registered_raw
/camera/right/image_raw
/camera/right/camera_info
```

## Outputs

```text
/rtabmap/odometry/mapping
/rtabmap/mapping/path
/rtabmap/cloud_map
/rtabmap/odometry/local
/rtabmap/path/local
/rtabmap/odometry/output
/rtabmap/path/output
```

Results are written to `data/results/rtab_map/`.

## Notes

Each evaluated run writes its RTAB-Map database inside the timestamped result directory as `rtabmap.db`, so runs do not reuse stale map state.
