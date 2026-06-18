# ORB-SLAM3

ORB-SLAM3 is integrated through the upstream `UZ-SLAMLab/ORB_SLAM3` ROS examples. UrbanNav defaults to `stereo_inertial`; E2O defaults to `mono_inertial`. Both are metric-scale visual-inertial modes.

## Build And Run

```bash
./build_orbslam3.sh
./run --algo orbslam3 --per 0 --gps off --eval
./run --algo orbslam3 --per 0 --gps on --eval
```

The first build is heavy because Pangolin and ORB-SLAM3 are compiled.

## Modes

```bash
./run --algo orbslam3 --per 0 --orb-mode stereo_inertial --eval
./run --algo orbslam3 --per 0 --orb-mode mono_inertial --eval
./run --algo orbslam3 --per 0 --orb-mode stereo --eval
./run --algo orbslam3 --per 0 --orb-mode mono --eval
```

`stereo_inertial` is the recommended UrbanNav benchmark mode. `mono_inertial` is the required E2O benchmark mode because E2O provides one camera plus IMU. Plain `mono` has arbitrary similarity scale, so it is only a visual-only ablation and must not be compared metrically with LiDAR trajectories or GT.

For E2O, the runner uses the supplied front-camera↔lidar103/body calibration as `IMU.T_b_c1`; it does not apply online ground-truth scale fitting. The E2O IMU-to-lidar103 co-location assumption remains provisional until a measured IMU extrinsic is available.

## Inputs

```text
/camera/left/image_raw
/camera/right/image_raw
/imu
/camera/left/camera_info
/camera/right/camera_info
```

The adapter uses `stereo_swap_lr:=true` so ORB-SLAM3 receives the physical right camera as Camera1 and physical left camera as Camera2, matching the swapped stereo-inertial config.

## Outputs

```text
/orb_slam3/camera_pose                 # patched native ORB-SLAM3 pose publisher
/orbslam3/odometry/mapping             # benchmark Odometry from pose republisher
/orbslam3/mapping/path
/orbslam3/tracking_status
/orbslam3/odometry/local
/orbslam3/path/local
/orbslam3/odometry/output
/orbslam3/path/output
```

Results are written to `data/results/orb_slam3/`.
