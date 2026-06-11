# Running ORB-SLAM3 on UrbanNav

This pipeline can run native ORB-SLAM3 in either monocular or stereo mode.
ORB-SLAM3 source code is not modified.

## Modes

```text
mono    Native ORB_SLAM3/Mono using ZED2 right camera
stereo  Native ORB_SLAM3/Stereo using swapped UrbanNav ZED2 pair
```

Monocular ORB-SLAM3 does not observe metric scale by itself. Stereo ORB-SLAM3
uses the ZED2 baseline and should be used when metric scale matters.

## Calibration Files

Mono config:

```text
wrappers/orbslam3_urbannav/config/zed2_right_mono_orbslam3.yaml
```

Stereo config:

```text
wrappers/orbslam3_urbannav/config/zed2_stereo_urbannav_swapped_orbslam3.yaml
```

UrbanNav's nominal ZED2 order gives negative disparity for ORB-SLAM3. The
wrapper therefore swaps the stereo pair by default:

```text
/zed2/camera/right/image_raw -> /camera/left/image_raw
/zed2/camera/left/image_raw  -> /camera/right/image_raw
```

The mono input is unchanged and still uses the ZED2 right camera.

The ZED2 image topics in the UrbanNav bag are `bgr8`, so both configs use:

```yaml
Camera.RGB: 0
```

Stereo baseline:

```text
baseline = 0.119957520736 m
Camera.bf = 31.6942764475
```

Stereo runs the native ORB-SLAM3 stereo node with rectification disabled by
default because the UrbanNav pair is already horizontally aligned in the
working swapped order:

```text
ORB_SLAM3/Stereo vocabulary settings false
```

The stereo YAML includes `LEFT.K/D/R/P` and `RIGHT.K/D/R/P` from the bag
camera_info messages.

## Build

```bash
cd /home/ayush/Desktop/Localiztion/orbslam3_urbannav_pipeline/orbslam3_urbannav
./build.sh
```

## One-Command Run

Start a mono run:

```bash
./run.sh bash /root/run_pipeline.sh /data/UrbanNav-HK_TST-20210517_sensors.bag mono
```

Start a stereo run:

```bash
./run.sh bash /root/run_pipeline.sh /data/UrbanNav-HK_TST-20210517_sensors.bag stereo
```

Detach from tmux:

```text
Ctrl-B d
```

## Manual Run

Start the container once:

```bash
cd /home/ayush/Desktop/Localiztion/orbslam3_urbannav_pipeline/orbslam3_urbannav
./run.sh
```

For each extra terminal:

```bash
docker exec -it orbslam3_urbannav_run bash
source /opt/ros/noetic/setup.bash
source /root/catkin_ws/devel/setup.bash
```

Terminal 1:

```bash
roscore
```

Terminal 2, wrapper:

```bash
roslaunch orbslam3_urbannav urbannav_wrapper.launch
```

For this UrbanNav bag, keep the default `stereo_swap_lr:=true`. To test the
nominal bag order explicitly:

```bash
roslaunch orbslam3_urbannav urbannav_wrapper.launch stereo_swap_lr:=false
```

Terminal 3, ORB-SLAM3 mono:

```bash
roslaunch orbslam3_urbannav orbslam3_urbannav.launch mode:=mono
```

Terminal 3, ORB-SLAM3 stereo:

```bash
roslaunch orbslam3_urbannav orbslam3_urbannav.launch mode:=stereo
```

To test the original nominal calibration/order instead:

```bash
roslaunch orbslam3_urbannav orbslam3_urbannav.launch mode:=stereo \
  stereo_camera_config:=$(rospack find orbslam3_urbannav)/config/zed2_stereo_orbslam3.yaml \
  stereo_do_rectify:=true
```

Stereo sanity checks:

```bash
rosrun orbslam3_urbannav check_stereo_timestamps.py
rostopic hz /camera/left/image_raw
rostopic hz /camera/right/image_raw
rostopic echo -n1 /camera/left/image_raw/header
rostopic echo -n1 /camera/right/image_raw/header
```

The left and right image stamps in the UrbanNav bag are identical, so native
ORB-SLAM3 stereo synchronization should fire when both topics are being played.

Terminal 4, play bag for mono:

```bash
rosbag play --clock --rate 1.0 /data/UrbanNav-HK_TST-20210517_sensors.bag --topics \
  /zed2/camera/right/image_raw /zed2/camera/right/camera_info
```

Terminal 4, play bag for stereo:

```bash
rosbag play --clock --rate 1.0 /data/UrbanNav-HK_TST-20210517_sensors.bag --topics \
  /zed2/camera/left/image_raw /zed2/camera/left/camera_info \
  /zed2/camera/right/image_raw /zed2/camera/right/camera_info
```

Terminal 5, RViz trajectory viewer:

```bash
roslaunch orbslam3_urbannav rviz_visualizer.launch
```

RViz shows the trajectory from `/orbslam3/path` and the current pose from
`/orbslam3/odometry`. Those topics are produced by `urbannav_wrapper.launch`.
The ORB-SLAM3 ROS example binaries publish `/orb_slam3/camera_pose`; the
wrapper converts that pose stream into RViz-friendly odometry, path, and TF.

If RViz opens but the trajectory does not move, check:

```bash
rostopic info /orb_slam3/camera_pose
rostopic hz /orb_slam3/camera_pose
rostopic hz /orbslam3/path
```

`/orb_slam3/camera_pose` must show `orbslam3_mono` or `orbslam3_stereo` as a
publisher.

For short tests, add:

```bash
--duration 90
```

## Full Pipeline Launch

Inside the container:

```bash
roslaunch orbslam3_urbannav full_pipeline.launch mode:=mono
```

or:

```bash
roslaunch orbslam3_urbannav full_pipeline.launch mode:=stereo
```

## Topics

Wrapper outputs:

```text
/camera/image_raw          right camera alias for mono
/camera/left/image_raw     left camera for stereo
/camera/right/image_raw    right camera for stereo
```

Republished evaluation topics:

```text
/orbslam3/odometry
/orbslam3/path
/orbslam3/tracking_status
```

## Notes

- No LiDAR, IMU, GPS, odometry, or ground truth is forwarded to ORB-SLAM3.
- Mono uses only the right ZED2 camera.
- Stereo uses the left and right ZED2 cameras with native ORB-SLAM3 stereo.
- The wrapper preserves image pixels and timestamps.
