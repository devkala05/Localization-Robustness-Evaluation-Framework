# Architecture

## Data flow

```text
E2O bag
  ├─ /lidar103/velodyne_points ─┐
  ├─ /mavros/imu/data           ├─ e2o_sensor_adapter ─┬─ /livox/lidar ─┐
  └─ /camera/color/image_raw ───┘                      ├─ /livox/imu   ├─ FAST-LIVO2 ─ /fast_livo2/odometry
                                                       └─ camera topics┘
                                                               └──────── ORB-SLAM3 ─ /orbslam3/camera_odometry

sensor streams + both odometries + ORB tracking state
              └─ localization_health_monitor

healthy independent odometries + health state
              └─ e2o_localization_fusion
                   ├─ fused odometry/pose/path/status/events
                   ├─ authoritative navigation TF
                   └─ navigation_ok ─ cmd_vel_safety_gate ─ /cmd_vel
```

## Black-box boundary

FAST-LIVO2 and ORB-SLAM3 are built from pinned upstream refs. The only ORB build patch publishes the pose already computed by the native ROS RGB-D example; it does not alter tracking or optimization. FAST-LIVO2 is not source-patched. Algorithm TF outputs are remapped away from `/tf` and `/tf_static`, preventing them from competing with the fusion node.

## Packages

### `localization_benchmark`

An E2O-only adapter. It preserves timestamps, converts the PointCloud2 `time` field from seconds to microseconds for FAST-LIVO2, publishes camera calibration, republishes the three required streams, and owns static transforms between `base_link`, LiDAR, and camera frames. Runtime fault modes are external to the estimators.

### `fast_livo2_e2o`

Loads E2O topics/calibration and starts upstream `fastlivo_mapping`. `odometry_alias_node.py` normalizes the native odometry output to `/fast_livo2/odometry`. It does not infer degraded LIO/VIO operation; health requires all configured inputs unless YAML is deliberately changed after verifying native behavior.

### `orbslam3_e2o`

Starts native ORB-SLAM3 RGB-D mode. The input adapter resizes RGB to the depth image dimensions, and the wrapper converts the published camera pose to stamped odometry, rejects non-finite/out-of-order/kinematically impossible samples, and publishes tracking status.

### `e2o_localization_fusion`

A supervisory loose-coupling package. It does not combine raw sensor residuals. It aligns independent trajectories, checks their consistency, selects one healthy source, preserves continuity across switching, and exposes explicit failure state.

## Source-selection states

- `WAITING_FOR_LOCALIZATION`
- `PRIMARY_FAST_LIVO2`
- `PRIMARY_FAST_LIVO2_DEGRADED_DISAGREEMENT`
- `BACKUP_ORB_SLAM3`
- `BACKUP_ORB_SLAM3_DEGRADED_DISAGREEMENT`
- `FAILED_BOTH_UNHEALTHY`

Source changes require health persistence, stabilization, minimum dwell, and—in recovery—cross-estimator consistency. A single recovered pose cannot trigger a switch.

## Repository layout

```text
docker/{fastlivo2,orbslam3,fusion}/
wrappers/{fast_livo2_e2o,orbslam3_e2o,localization_benchmark,e2o_localization_fusion}/
configs/e2o/
evaluation/
navigation/
rviz/
tests/
data/e2o/ground_truth/
build.sh
run.sh
```
