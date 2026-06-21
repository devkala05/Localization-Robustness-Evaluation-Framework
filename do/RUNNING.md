# Building, running, and diagnosis

## Prerequisites

- Ubuntu host with Docker and adequate disk space.
- NVIDIA is not required by these Dockerfiles.
- X11 access only when `RVIZ=true`.
- The E2O bag must contain `/lidar103/velodyne_points`, `/mavros/imu/data`, and `/camera/color/image_raw` with usable timestamps.

Check the bag before building:

```bash
rosbag info /path/to/one_loop.bag
rosbag check /path/to/one_loop.bag
```

## Build commands

```bash
./build.sh all
./build.sh fusion
./build.sh fast_livo2
./build.sh orbslam3
./build.sh all --no-cache       # only for deliberate clean rebuilds
```

The Docker context excludes output/build artifacts through `.dockerignore`. Unchanged dependency layers are reused by default.

## Required run modes

```bash
./run.sh fast_livo2 e2o /path/to/one_loop.bag
./run.sh orbslam3 e2o /path/to/one_loop.bag
./run.sh fusion e2o /path/to/one_loop.bag
./run.sh fusion_navigation e2o /path/to/one_loop.bag
```

Standalone ORB defaults to its native scale (`ORB_STANDALONE_SCALE=1.0`). A
reference scale may be supplied explicitly, but monocular initialization scale
changes between runs and can drift. Fusion always receives native monocular
scale and estimates Sim(3) from FAST-LIVO2 overlap.

Run with visualization:

```bash
RVIZ=true ./run.sh fusion e2o /path/to/one_loop.bag
```

Run an existing navigation launch file through the safety gate:

```bash
TF_MODE=direct \
NAVIGATION_LAUNCH_FILE=/workspace/navigation/my_navigation.launch \
./run.sh fusion_navigation e2o /path/to/one_loop.bag
```

The supplied archive had no concrete planner/controller package. The command above is therefore an integration hook, not a claim that a specific navigation stack was runtime-validated.

## Bag playback only

When manually debugging an already-started ROS graph:

```bash
rosparam set /use_sim_time true
rosbag play --clock --rate 1.0 /path/to/one_loop.bag --topics \
  /lidar103/velodyne_points /mavros/imu/data /camera/color/image_raw
```

## Runtime checks

```bash
rostopic list
rostopic hz /livox/lidar
rostopic hz /livox/imu
rostopic hz /camera/right/image_raw
rostopic hz /fast_livo2/odometry
rostopic hz /orbslam3/camera_odometry
rostopic hz /fused_localization/odometry
rostopic echo -n 1 /fused_localization/status
rostopic echo -n 1 /localization_health/summary
rostopic echo -n 1 /fused_localization/events
rosnode info /laserMapping
rosnode info /orbslam3_mono
roswtf
rosrun tf2_tools view_frames.py
rosrun rqt_graph rqt_graph
```

Or collect most of these into a directory:

```bash
./scripts/diagnose_runtime.sh
```

`rostopic hz` is intentionally a live command; stop it after enough samples. Check that the two independent odometry topics have different publishers and that the fused topic publisher is only `/e2o_localization_fusion`.

## Evaluation

```bash
./evaluation/evaluate.sh data/output/<run_id>
```

Generated files include:

- `metrics.json` and `summary.md`;
- `trajectory_xy.png`;
- `source_timeline.png`;
- `health_sensor_timeline.png`.

## Common failures

- **No FAST-LIVO2 output:** inspect `time` and `ring` PointCloud2 fields, LiDAR scan-line assumption, IMU rate, camera encoding, and FAST container logs.
- **No ORB tracking:** verify image encoding/resolution/intrinsics, camera rate, exposure/motion blur, and vocabulary/config paths.
- **ORB cannot become fallback:** metric alignment is not ready. Check healthy overlap, adequate translational motion, scale bounds, and alignment RMSE in fused status.
- **Repeated failover:** increase stabilization/dwell thresholds only after diagnosing input timestamps and health reasons.
- **TF loop:** use `view_frames.py`; make sure only the selected TF mode owns each authoritative edge.
- **Timestamp lag:** bag playback must publish `/clock`; all containers use host networking and `/use_sim_time`.
- **Calibration mismatch:** run `./scripts/validate_configuration.py` and replace identity/zero assumptions with measured values.

The supplied files contain LiDAR-to-camera calibration but no measured
IMU-to-LiDAR transform. FAST-LIVO2 still uses the explicitly documented identity
assumption for that transform; obtain a proper inertial calibration before
treating the trajectory as accuracy-validated.
