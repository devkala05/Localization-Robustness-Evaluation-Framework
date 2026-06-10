# Running FAST-LIVO2 on UrbanNav

This folder runs native FAST-LIVO2 inside Docker on the UrbanNav bag. FAST-LIVO2
source code is not modified. The wrapper only adapts topics, frame IDs, and the
Velodyne per-point time units required by FAST-LIVO2.

## Working Settings

Use these settings for the UrbanNav-HK-TST bag:

```bash
img_en:=1
imu_en:=true
imu_axes_fix:=false
pcd_save_en:=true
```

Important IMU tuning in `wrappers/fast_livo2_wrapper/config/fast_livo2_urbannav.yaml`:

```yaml
imu:
  acc_cov: 0.5
  gyr_cov: 0.3
  b_acc_cov: 0.0001
  b_gyr_cov: 0.0001
```

Do not replace these with the raw Xsens noise-density values. FAST-LIVO2 treats
these as estimator tuning weights.

## Build

From this directory:

```bash
cd /home/ayush/Desktop/Localiztion/fastlivo2_pipeline
./build.sh
```

## Start Container

Start the container once:

```bash
cd /home/ayush/Desktop/Localiztion/fastlivo2_pipeline
./run.sh
```

For every extra terminal, do not run `./run.sh` again. Use:

```bash
docker exec -it fastlivo2_interactive bash
source /opt/ros/noetic/setup.bash
source /root/catkin_ws/devel/setup.bash
```

## Manual Run

Use separate terminals.

Terminal 1, ROS master:

```bash
roscore
```

Terminal 2, bridge:

```bash
docker exec -it fastlivo2_interactive bash
source /opt/ros/noetic/setup.bash
source /root/catkin_ws/devel/setup.bash
roslaunch fast_livo2_wrapper topic_bridge.launch
```

Terminal 3, output recorder:

```bash
docker exec -it fastlivo2_interactive bash
source /opt/ros/noetic/setup.bash
source /root/catkin_ws/devel/setup.bash
roslaunch fast_livo2_wrapper record_outputs.launch
```

Terminal 4, FAST-LIVO2:

```bash
docker exec -it fastlivo2_interactive bash
source /opt/ros/noetic/setup.bash
source /root/catkin_ws/devel/setup.bash
roslaunch fast_livo2_wrapper fast_livo2.launch \
  img_en:=1 imu_en:=true imu_axes_fix:=false pcd_save_en:=true
```

Terminal 5, play bag:

```bash
docker exec -it fastlivo2_interactive bash
source /opt/ros/noetic/setup.bash
source /root/catkin_ws/devel/setup.bash
rosbag play /data/UrbanNav-HK_TST-20210517_sensors.bag --clock
```

For short tests, use:

```bash
rosbag play /data/UrbanNav-HK_TST-20210517_sensors.bag --clock -u 90
```

## RViz

```bash
docker exec -it fastlivo2_interactive bash
source /opt/ros/noetic/setup.bash
source /root/catkin_ws/devel/setup.bash
rviz -d $(rospack find fast_livo2_wrapper)/config/fast_livo2.rviz
```

For colored points, display `/cloud_registered` and set:

```text
Color Transformer: RGB8 or RGB
Fixed Frame: camera_init
```

## Outputs

Outputs are written to:

```text
fastlivo2_pipeline/data/output/
```

Expected files:

```text
trajectory_tum.txt
odometry.csv
fast_livo2_output.bag
fast_livo2_map.pcd
```

Native FAST-LIVO2 odometry topic is:

```text
/aft_mapped_to_init
```

## Diagnostics

Check topic rates:

```bash
rosrun fast_livo2_wrapper verify_topics.py _timeout:=30.0
```

Useful topic checks:

```bash
rostopic hz /livox/lidar
rostopic hz /livox/imu
rostopic hz /camera/right/image_raw
rostopic hz /cloud_registered
rostopic echo -n1 /cloud_registered/fields
```

## Isolation Tests

LiDAR only:

```bash
roslaunch fast_livo2_wrapper fast_livo2.launch \
  img_en:=0 imu_en:=false pcd_save_en:=false
```

LIO only:

```bash
roslaunch fast_livo2_wrapper fast_livo2.launch \
  img_en:=0 imu_en:=true imu_axes_fix:=false pcd_save_en:=false
```

Full LIVO:

```bash
roslaunch fast_livo2_wrapper fast_livo2.launch \
  img_en:=1 imu_en:=true imu_axes_fix:=false pcd_save_en:=false
```

Known-good result from debugging:

```text
LiDAR only: works
LIO only: works with acc_cov=0.5, gyr_cov=0.3
Full LIVO: works with same IMU tuning
imu_axes_fix: keep false
```

## Notes

- FAST-LIVO2 source is native/unmodified.
- The wrapper converts `/velodyne_points` to `/livox/lidar`.
- The wrapper converts `/imu/data` to `/livox/imu`.
- The wrapper converts `/zed2/camera/right/image_raw` to `/camera/right/image_raw`.
- UrbanNav Velodyne point `time` is in seconds; FAST-LIVO2 expects microseconds,
  so the wrapper normalizes only that point-time field.
- No GPS, ground truth, wheel odometry, or external map is fed to FAST-LIVO2.
