# Final fixes from example.zip reference

This codebase uses the working FAST-LIVO2 UrbanNav reference wrapper logic for calibration/time/frame handling and applies the same assumptions to FAST-LIO2 and LVI-SAM.

Key fixes:

- No artificial camera delay. Camera image and camera_info keep the original bag timestamp.
- Ground truth `/ground_truth_path` is live `/clock`-synchronised, so RViz does not show the future route as the current car position.
- Ground truth is rotated by `GT_YAW_OFFSET_DEG=90.0` by default to match the algorithm/RViz frame convention seen in the UrbanNav bag.
- LiDAR ring count is set to 32 because the UrbanNav center `/velodyne_points` cloud uses rings `0..31`.
- Velodyne point `time` is treated as seconds (`time_scale: 1.0`, `pointTimeScale: 1.0`).
- FAST-LIO2 LiDAR-IMU extrinsic sign now follows the reference FAST-LIVO2 config convention: `[0, 0, 0.28]`.
- LVI-SAM TF mode avoids a duplicate `map -> odom` static transform because LVI-SAM publishes `map -> odom` dynamically.
- Camera publishing is enabled in perturbation runs and `/camera/right/camera_info` is published with the same timestamp as `/camera/right/image_raw`.
- LVI-SAM run uses `BAG_RATE=0.35` by default to prevent compute lag while preserving actual bag timestamps.

Run examples:

```bash
./build.sh
BAG_RATE=0.5 ./run.sh --algo fastlio2 --per 0

./build_lvisam.sh
BAG_RATE=0.35 GT_YAW_OFFSET_DEG=90.0 ./run_lvisam.sh 0
```

Check:

```bash
rostopic echo -n1 /camera/right/image_raw/header
rostopic echo -n1 /camera/right/camera_info/header
rostopic hz /cloud_registered_raw
rostopic hz /lvi_sam/lidar/mapping/cloud_registered
rostopic hz /ground_truth_path
```
