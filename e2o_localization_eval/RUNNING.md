# Running The e2o Localization Eval

This project is set up for the `one_full_loop.bag` dataset in `data/raw/`.
The default RViz view shows:

- LiDAR 103 only: `/lidar103/velodyne_points`
- front camera image: `/camera/color/image_raw`
- ground-truth path: `/ground_truth/path`
- moving vehicle TF: `map -> base_link -> velodyne103 -> velodyne`

## Build

```bash
cd /home/ayush/Desktop/Localiztion/e2o_localization_eval
./build.sh
```

## Inspect The Bag

```bash
./run.sh inspect --bag one_full_loop.bag
```

Expected useful topics:

```text
/camera/color/image_raw
/lidar103/velodyne_points
/mavros/global_position/global
/mavros/imu/data
```

## Generate Ground Truth

The current GT file was generated from GPS position plus IMU orientation:

```bash
./run.sh gt --bag one_full_loop.bag \
  --gt-topic /mavros/global_position/global \
  --orientation-topic /mavros/imu/data
```

This writes:

```text
data/ground_truth/one_full_loop_gt.tum
```

The TUM rows are:

```text
timestamp tx ty tz qx qy qz qw
```

Position comes from `/mavros/global_position/global` converted to a local ENU-style frame. Orientation comes from `/mavros/imu/data`.

## Play With RViz

Use this command for the current visualization:

```bash
xhost +local:docker
./run.sh play-gt --bag one_full_loop.bag --gt data/ground_truth/one_full_loop_gt.tum
```

This publishes the GT path and a moving TF so LiDAR 103 moves with the vehicle.

## Notes

- `./run.sh play` only plays the raw sensors. It does not publish the GT path.
- Use `./run.sh play-gt ...` when you want the path and moving LiDAR.
- RViz point cloud decay is set to `0`, so only the current LiDAR scan is shown.
- The GT is good for visualization and approximate trajectory playback. It is GPS+IMU based, not survey-grade RTK/INS ground truth.

## Cleanup

Generated Catkin outputs can be safely removed:

```bash
rm -rf catkin_ws/build catkin_ws/devel catkin_ws/logs
```

They are recreated by `./build.sh` or by running the container again.
