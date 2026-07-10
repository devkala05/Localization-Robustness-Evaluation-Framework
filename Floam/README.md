# FLOAM E2O Wrapper

This folder contains a self-contained E2O-style wrapper for the ALIVE FLOAM
implementation from:

```text
~/Desktop/ALIVE_N/alive-dev/src/floam
```

The native source is copied under `native/`. The wrapper package under
`wrappers/floam_e2o` launches map localization. It aliases native `/odom` to:

```text
/floam/odometry
```

It also publishes the RViz trajectory as:

```text
/floam/path
```

Each run records one CSV under:

```text
Floam/output/<run_id>/
```

## Build

From `/home/ayush/Desktop/Localiztion`:

```bash
./Floam/build.sh
```

## Run

```bash
./Floam/run.sh e2o_localization_fusion_framework/data/e2o/one_full_loop.bag
```

Map localization with RViz:

```bash
RVIZ=true ./Floam/run.sh v1/data/e2o/raw/one_full_loop.bag
```

When relocalization is enabled, the run waits for you to set the car pose in
RViz before starting bag playback. Use the `2D Pose Estimate` tool on the PCD
map. That publishes `/initialpose`, matching the ALIVE FLOAM workflow.

For the E2O bag, the wrapper also matches ALIVE's E2O LiDAR TF:

```text
base_link -> velodyne: x=0 y=0 z=0 yaw=0.174533 pitch=0 roll=0
```

RViz uses:

```text
Floam/rviz/e2o_floam.rviz
```

The default map is:

```text
/workspace/maps/full_campus.pcd
```

Override the initial relocalization pose when needed:

```bash
INITIAL_X=12.0 INITIAL_Y=3.5 INITIAL_YAW=1.57 ./Floam/run.sh /path/to/bag.bag
```

If you want the localization launch to initialize from the incoming scan instead
of waiting for a map relocalization pose:

```bash
RELOCALIZATION=false AUTO_INITIALPOSE=false ./Floam/run.sh /path/to/bag.bag
```

For non-interactive tests, you can still provide the initial estimate
automatically:

```bash
AUTO_INITIALPOSE=true INITIAL_X=12.0 INITIAL_Y=3.5 INITIAL_YAW=1.57 ./Floam/run.sh /path/to/bag.bag
```

## Contents

- `native/floam`: ALIVE FLOAM source, excluding the heavy `maps/` directory.
- `native/alive_msgs`: message package needed by ALIVE FLOAM.
- `wrappers/floam_e2o`: launch/config/scripts for E2O-style execution.
- `docker`: Docker image for ROS Noetic catkin build.
- `output`: run outputs created by `run.sh`.
