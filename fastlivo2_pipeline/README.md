# FAST-LIVO2 Black-Box Testing Pipeline — UrbanNav Dataset

A complete, production-ready Dockerized ROS Noetic pipeline for running
**FAST-LIVO2** (hku-mars/FAST-LIVO2) on the **UrbanNav-HK-TST-20210517**
dataset without modifying any FAST-LIVO2 source code.

For the exact working run commands and debugging notes, see
[`RUNNING.md`](RUNNING.md).

---

## Topic Mapping Table

| UrbanNav Topic (rosbag) | Msg Type | Frame ID | Hz | → Wrapper → | FAST-LIVO2 Topic | Frame ID | Timestamp Policy |
|---|---|---|---|---|---|---|---|
| `/velodyne_points` | `sensor_msgs/PointCloud2` | `velodyne` | ~10 | bridge | `/livox/lidar` | `velodyne` | **Preserved exactly** |
| `/imu/data` | `sensor_msgs/Imu` | `imu_link` | ~200 | bridge | `/livox/imu` | `body` | **Preserved exactly** |
| `/zed2/camera/right/image_raw` | `sensor_msgs/Image` | `camera_right` | ~10 | bridge | `/camera/right/image_raw` | `camera_right` | **Preserved exactly** |

### FAST-LIVO2 Output Topics

| Topic | Msg Type | Frame ID | Hz | Description |
|---|---|---|---|---|
| `/path` | `nav_msgs/Path` | `camera_init` | variable | Full accumulated trajectory |
| `/Odometry` | `nav_msgs/Odometry` | `camera_init` | ~10 | Current pose + velocity |
| `/cloud_registered` | `sensor_msgs/PointCloud2` | `camera_init` | ~10 | Registered scan (world frame) |
| `/cloud_registered_body` | `sensor_msgs/PointCloud2` | `body` | ~10 | Registered scan (body frame) |
| `/tf` | `tf2_msgs/TFMessage` | — | ~100 | `camera_init` → `body` dynamic TF |

---

## TF Tree

```
map (static)
└── odom (identity, static)

camera_init (FAST-LIVO2 world frame, dynamic at runtime)
└── body  (IMU frame, dynamic at runtime)
    ├── velodyne         (centre Velodyne VLP-16, static from extrinsic.yaml)
    │   ├── velodyne_left   (left VLP-16, static)
    │   └── velodyne_right  (right VLP-16, static)
    ├── camera_left      (ZED2 left, static from extrinsic.yaml)
    │   └── camera_left_optical
    └── camera_right     (ZED2 right, static from extrinsic.yaml)
        └── camera_right_optical
```

---

## Black-Box Constraints

- **No FAST-LIVO2 source code modifications** of any kind.
- Wrapper only patches `header.frame_id` — all sensor data forwarded verbatim.
- Timestamps are **never modified**.
- Message order is **preserved** (subscriber callbacks are synchronous).
- No GPS, ground truth, wheel odometry, or external map is forwarded.

---

## Directory Structure

```
fastlivo2_pipeline/
├── Dockerfile                          # Ubuntu 20.04 + ROS Noetic + FAST-LIVO2 build
├── docker-compose.yml                  # Multi-container orchestration
├── build.sh                            # Build Docker image
├── run.sh                              # Interactive container shell
├── run_pipeline.sh                     # Full tmux-based automation
├── .docker/
│   └── entrypoint.sh                   # Container entrypoint
├── data/
│   ├── UrbanNav-HK-TST-20210517.bag    # ← Place your rosbag here
│   └── output/                         # ← Pipeline results written here
└── wrappers/
    └── fast_livo2_wrapper/             # ROS catkin package
        ├── CMakeLists.txt
        ├── package.xml
        ├── config/
        │   ├── fast_livo2_urbannav.yaml  # FAST-LIVO2 sensor config
        │   └── fast_livo2.rviz           # RViz configuration
        ├── launch/
        │   ├── topic_bridge.launch       # TF + topic converter
        │   ├── fast_livo2.launch         # FAST-LIVO2 node
        │   ├── record_outputs.launch     # Output recording
        │   └── full_pipeline.launch      # All-in-one launch
        ├── scripts/
        │   ├── topic_bridge_node.py      # Core wrapper (UrbanNav → FAST-LIVO2)
        │   ├── tf_broadcaster_node.py    # Static TF from extrinsic.yaml
        │   ├── output_recorder_node.py   # TUM/CSV/bag recording
        │   ├── trajectory_exporter.py    # Post-run TUM/CSV/KITTI export
        │   ├── bag_player.py             # Controlled rosbag playback
        │   └── verify_topics.py          # Pipeline validation
        └── results/
            └── README.md
```

---

## Quick Start

### 1. Build the Docker image

```bash
./build.sh
```

This clones and builds (inside Docker):
- `Sophus` (FAST-LIVO2 upstream prerequisite)
- `rpg_vikit` (`vikit_common` / `vikit_ros` FAST-LIVO2 prerequisites)
- `livox_ros_driver` (dependency of FAST-LIVO2 CMakeLists)
- `fast_livo` (FAST-LIVO2 catkin package; black box — no modifications)
- `fast_livo2_wrapper` (this package)

### 2. Place your rosbag

```bash
cp /path/to/UrbanNav-HK-TST-20210517_sensors.bag ./data/
```

### 3. Run the full pipeline

```bash
./run.sh ./run_pipeline.sh /data/UrbanNav-HK-TST-20210517_sensors.bag
```

Or with custom options:

```bash
./run.sh ./run_pipeline.sh /data/UrbanNav-HK-TST-20210517_sensors.bag 0.5 10
#                                                                      ^rate ^start_delay
```

### 4. Single roslaunch (inside container)

```bash
./run.sh
# Inside container:
roslaunch fast_livo2_wrapper full_pipeline.launch \
    bag_path:=/data/UrbanNav-HK-TST-20210517_sensors.bag \
    rate:=1.0 rviz:=true
```

---

## Expected Workflow

```
1. Docker starts     → entrypoint sources ROS + catkin_ws
2. roscore starts    → ROS master at localhost:11311
3. Bridge starts     → tf_broadcaster_node + topic_bridge_node
4. Recorder starts   → subscribes to FAST-LIVO2 output topics
5. FAST-LIVO2 starts → loads config YAML, waits for sensor data
6. Rosbag plays      → /velodyne_points + /imu/data + /zed2/.../image_raw
7. Bridge converts   → /livox/lidar + /livox/imu + /camera/right/image_raw
8. FAST-LIVO2 runs   → publishes /path, /Odometry, /cloud_registered, /tf
9. RViz visualises   → trajectory, map cloud, TF tree, camera image
10. Recorder saves   → trajectory_tum.txt, odometry.csv, fast_livo2_output.bag
```

---

## Validation

```bash
# Inside container, after pipeline starts:
rosrun fast_livo2_wrapper verify_topics.py _timeout:=30.0
```

Expected output:
```
  PASS  /velodyne_points                    10.0 Hz  (need  5.0)
  PASS  /imu/data                          200.0 Hz  (need 50.0)
  PASS  /zed2/camera/right/image_raw        10.0 Hz  (need  5.0)
  PASS  /livox/lidar                        10.0 Hz  (need  5.0)
  PASS  /livox/imu                         200.0 Hz  (need 50.0)
  PASS  /camera/right/image_raw             10.0 Hz  (need  5.0)
  PASS  /path                               10.0 Hz  (need  1.0)
  PASS  /Odometry                           10.0 Hz  (need  5.0)
  PASS  /cloud_registered                   10.0 Hz  (need  1.0)
  PASS  /cloud_registered_body              10.0 Hz  (need  1.0)
  ALL CHECKS PASSED — pipeline is healthy.
```

---

## Output Files

| File | Format | Description |
|---|---|---|
| `trajectory_tum.txt` | TUM | `timestamp tx ty tz qx qy qz qw` |
| `odometry.csv` | CSV | Pose + velocity, 14 columns |
| `trajectory.csv` | CSV | Trajectory poses |
| `trajectory_kitti.txt` | KITTI | 3×4 `[R|t]` matrix per frame |
| `fast_livo2_output.bag` | rosbag | All output topics for replay |
| `fast_livo2_map.pcd` | PCD | Final accumulated point-cloud map |

---

## FAST-LIVO2 Build Notes

FAST-LIVO2 has a CMakeLists.txt `find_package(livox_ros_driver REQUIRED)` even
when using Velodyne LiDAR. The Dockerfile builds `livox_ros_driver` first, then
`fast_livo`, then `fast_livo2_wrapper`. All three are in the same catkin workspace.
It also installs FAST-LIVO2's upstream Sophus and `rpg_vikit` prerequisites before
the catkin build.

The `preprocess.lidar_type: 2` in the YAML selects the Velodyne driver path inside
FAST-LIVO2 — no source code change is needed.
