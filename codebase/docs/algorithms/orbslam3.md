# ORB-SLAM3

ORB-SLAM3 is integrated through the upstream `UZ-SLAMLab/ORB_SLAM3` ROS examples. The default benchmark mode is now `stereo_inertial`, not visual-only stereo.

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

`stereo_inertial` is the recommended benchmark mode. `stereo` and `mono` are kept for visual-only ablations.

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
