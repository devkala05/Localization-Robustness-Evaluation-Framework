# e2o Faculty Loop Localization Evaluation Codebase

Docker/ROS Noetic codebase for the e2o mapping/ORB-SLAM dataset recorded around New Faculty Residence and Old Faculty Residence.

This is intentionally **not tied to a fixed bag filename**. Put any ROS1 `.bag` file under `data/`, then use `./run.sh ... --bag <name>` only if there are multiple bags.

## Dataset profile

| Field | Value |
|---|---|
| Purpose | Mapping, ORB-SLAM |
| Recorded | 2024-06-12 10:14:00 |
| Platform | e2o |
| Duration | 571 s |
| Size | 30.79 GB |
| Location | New Faculty Residence, Old Faculty Residence |
| Conditions | Morning, no traffic, moderate vegetation, no inclined planes, two loop closures |

Expected topics:

```text
/camera/color/image_raw        sensor_msgs/Image        front camera
/lidar102/velodyne_points      sensor_msgs/PointCloud2  left lidar
/lidar103/velodyne_points      sensor_msgs/PointCloud2  middle lidar
/lidar104/velodyne_points      sensor_msgs/PointCloud2  right lidar
/merged/velodyne_points        sensor_msgs/PointCloud2  merged lidars
```

## What this repo provides

- ROS Noetic Docker environment.
- Automatic `.bag` discovery under `data/`.
- Bag inspection and topic health checks.
- Front-camera `CameraInfo` publisher using the supplied calibration.
- Static TF publisher for the supplied LiDAR/camera extrinsics.
- Ground-truth extraction tool for hidden/available pose, odom, GPS, path, or TF topics.
- Ground-truth TUM publisher for RViz and later evaluation.
- TUM recorder for algorithm outputs.
- ATE evaluation script with Umeyama alignment and plots.
- ORB-SLAM3 adapter scaffold.

## Important ground-truth note

The metadata supplied for this bag lists only image and point-cloud topics. That means the repo can **extract ground truth only if the actual bag contains an additional hidden/reference topic**, such as `/ground_truth`, `/odom`, `/ins`, `/gps`, `/novatel`, `/tf`, or similar.

If no such topic exists, this codebase will clearly report that no extractable ground truth is present. It will not fabricate ground truth from ORB-SLAM or from the camera/LiDAR streams.

For true benchmarking, use one of these as reference:

- RTK/INS trajectory
- surveyed GNSS/INS trajectory
- motion-capture or total-station reference
- carefully reviewed offline SLAM/map trajectory, saved as TUM

TUM format:

```text
timestamp tx ty tz qx qy qz qw
```

## Quick start

### 1. Build

```bash
cd e2o_faculty_loop_localization_eval
./build.sh
```

### 2. Add your bag

Any filename is okay:

```bash
mkdir -p data/raw
cp /path/to/your_dataset.bag data/raw/
```

Example:

```bash
cp /path/to/one_loop.bag data/raw/
```

### 3. Inspect topics and hidden ground-truth candidates

```bash
./run.sh inspect
```

If multiple `.bag` files exist:

```bash
./run.sh inspect --bag one_loop.bag
```

### 4. Try to extract ground truth

Auto mode:

```bash
./run.sh gt --bag one_loop.bag
```

Manual topic mode, after `inspect` shows a candidate:

```bash
./run.sh gt --bag one_loop.bag --gt-topic /your/ground_truth/topic
```

This writes:

```text
data/ground_truth/one_loop_gt.tum
```

For `/tf` extraction:

```bash
./run.sh gt --bag one_loop.bag --gt-topic /tf --tf-parent map --tf-child base_link
```

### 5. Play the bag with calibration, TF, camera info, LiDAR, and RViz

```bash
xhost +local:docker
./run.sh play --bag one_loop.bag
```

Without RViz:

```bash
./run.sh play --bag one_loop.bag --no-rviz
```

### 6. Play bag and publish ground truth path

```bash
./run.sh play-gt --bag one_loop.bag --gt data/ground_truth/one_loop_gt.tum
```

### 7. Record an algorithm output to TUM

In a separate terminal while the algorithm is running:

```bash
./run.sh record /localization/odometry --est data/outputs/my_algo.tum
```

If your algorithm publishes `geometry_msgs/PoseStamped`, edit or use the launch directly:

```bash
./run.sh shell
roslaunch e2o_benchmark_tools record_algorithm_tum.launch \
  topic:=/orb_slam3/camera_pose \
  message_type:=geometry_msgs/PoseStamped \
  output:=/workspace/e2o_eval/data/outputs/orb_slam3.tum
```

### 8. Evaluate

```bash
./run.sh eval --gt data/ground_truth/one_loop_gt.tum --est data/outputs/my_algo.tum
```

Outputs:

```text
data/outputs/evaluation/metrics.json
data/outputs/evaluation/plots/trajectory_xy.png
data/outputs/evaluation/plots/ate_error.png
```

## ORB-SLAM3 adapter

The dataset side is ready for ORB-SLAM3 monocular:

```bash
ORB_SLAM3_VOCAB=/opt/ORB_SLAM3/Vocabulary/ORBvoc.txt \
ORB_SLAM3_ROS_PACKAGE=ORB_SLAM3 \
./run.sh orb-slam3 --bag one_loop.bag
```

ORB-SLAM3 itself is treated as a black-box external dependency. If your ORB-SLAM3 fork has a different ROS node name or output topic, change only:

```text
algorithms/orb_slam3/run_orb_slam3.sh
```

## Project layout

```text
.
├── build.sh
├── run.sh
├── config/
│   ├── calibration/e2o/
│   └── topics/e2o_faculty_loop_topics.yaml
├── data/
│   ├── raw/             # put .bag files here
│   ├── ground_truth/    # extracted/supplied .tum files
│   └── outputs/         # algorithm trajectories + metrics
├── catkin_ws/src/e2o_benchmark_tools/
│   ├── launch/
│   └── scripts/
├── algorithms/
│   └── orb_slam3/
├── scripts/
└── rviz/
```

## Common problems

### `No .bag under data/`

Copy the bag into `data/raw/`:

```bash
cp /path/to/bag.bag data/raw/
```

### Multiple bags found

Pass the bag explicitly:

```bash
./run.sh inspect --bag your_file.bag
```

### RViz opens but fixed frame errors appear

Wait until bag playback starts. If using only LiDAR/camera with no odometry, the fixed frame `map` may not have motion. Static sensor TFs are still published. For path visualization, publish ground truth or algorithm odometry/path.

### Ground truth extraction fails

Run:

```bash
./run.sh inspect --bag your_file.bag
```

If no pose/odom/GPS/TF candidates are listed, the bag simply does not contain ground truth. Add a real `.tum` reference manually under `data/ground_truth/`.
