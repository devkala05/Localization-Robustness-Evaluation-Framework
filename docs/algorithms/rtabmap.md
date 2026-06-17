# RTAB-Map ICP

RTAB-Map is integrated as a standalone LiDAR ICP pipeline for the benchmark. It no longer launches FAST-LIO2 and it does not subscribe to FAST-LIO2 `/Odometry`.

## Pipeline

```text
/cloud_registered_raw
  -> /rtabmap/scan_cloud        # sanitized raw/perturbed PointCloud2
  -> rtabmap_odom/icp_odometry
  -> /rtabmap/icp_odom          # RTAB-Map's own ICP odometry
  -> rtabmap_slam/rtabmap
  -> /rtabmap/mapPath
  -> /rtabmap/odometry/mapping  # benchmark-normalized output
```

## Build And Run

```bash
./build_rtabmap.sh
./run --algo rtabmap --per 0 --gps off --eval
./run --algo rtabmap --per 0 --gps on --eval
```

## Inputs

```text
/cloud_registered_raw
```

Camera topics are not required in the default standalone ICP mode. The common benchmark adapter still exists, but for RTAB-Map ICP it is configured with `publish_camera:=false publish_camera_info:=false`.

## Outputs

```text
/rtabmap/icp_odom
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
