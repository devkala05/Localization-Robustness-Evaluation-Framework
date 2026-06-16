# R3LIVE Integration Notes

R3LIVE is integrated for UrbanNav-HK_TST-20210517 as a production **stable LIO-first** benchmark participant.

## Why LIO-first by default

Upstream R3LIVE supports a full LiDAR-Inertial-Visual estimator, but spinning-LiDAR + visual operation on UrbanNav is fragile without source-level front-end validation. Therefore this wrapper defaults to:

```text
run_visual=false
native R3LIVE stable role: LiDAR front-end first, full mapping second
FAST-LIO2 fallback frontend: enabled
```

This keeps `/r3live/odometry/mapping` alive and comparable instead of silently producing an empty path.

## Input topics

The common benchmark bridge/adapter publishes:

```text
/velodyne_points + /imu/data + /zed2/camera/right/image_raw
    -> /mycar/* custom messages
    -> custom_fastlio_adapter
    -> /cloud_registered_raw, /livox/imu, /camera/right/image_raw, /camera/image_raw
```

R3LIVE uses `/cloud_registered_raw` / `/livox/imu` in the stable benchmark path. `/camera/image_raw` remains available for experimental visual mode.

## Point time scale

For R3LIVE, `point_time_scale` is intentionally `1.0`. UrbanNav Velodyne point time is already relative seconds, matching the FAST-LIO/FAST-LIO2 Velodyne path.

## Output topics

The wrapper exposes the standard native and benchmark topics:

```text
/r3live/odometry/mapping       native wrapper output
/r3live/mapping/path           native wrapper path
/r3live/odometry/local         standardized local odometry
/r3live/path/local             standardized local path
/r3live/odometry/output        selected output, local or GPS-fused
/r3live/path/output            selected output path
```

`trajectory_mux_node.py` subscribes to common upstream odometry names:

```text
/r3live/odometry
/Odometry
/aft_mapped_to_init
/aft_mapped_to_init_odom
```

If native R3LIVE publishes nothing, the FAST-LIO2 fallback `/Odometry` keeps the benchmark output live and the status pane makes this visible.
