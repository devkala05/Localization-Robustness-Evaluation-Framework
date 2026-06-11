#!/bin/bash
set -euo pipefail

source /opt/ros/noetic/setup.bash
# Source packages are bind-mounted/read from image; do not delete them here.
cd /root/catkin_ws

echo "Checking dataset files..."
test -f /data/UrbanNav-HK_TST-20210517_sensors.bag
test -f /data/UrbanNav_TST_GT_raw.txt

echo "Building mounted ROS packages..."
catkin build livox_ros_driver fast_lio custom_localization_msgs localization_benchmark fast_lio_urbannav adaptive_w_lvio_urbannav -DCMAKE_BUILD_TYPE=Release
source /root/catkin_ws/devel/setup.bash

echo "Checking ROS packages..."
rospack find livox_ros_driver >/dev/null
rospack find fast_lio >/dev/null
rospack find custom_localization_msgs >/dev/null
rospack find localization_benchmark >/dev/null
rospack find fast_lio_urbannav >/dev/null
rospack find adaptive_w_lvio_urbannav >/dev/null

echo "Checking custom message types..."
rosmsg show custom_localization_msgs/CustomPointCloud >/dev/null
rosmsg show custom_localization_msgs/CustomImu >/dev/null
rosmsg show custom_localization_msgs/CustomImage >/dev/null
rosmsg show custom_localization_msgs/LocalizationOutput >/dev/null

echo "Checking perturbation files..."
for per in 0 1 2 3 4 5 6; do
    test -f "/root/catkin_ws/src/localization_benchmark/config/perturbations/per_${per}.yaml"
done

echo "Checking algorithm config..."
python3 /workspace/scripts/algorithm_config.py \
    --config /root/catkin_ws/src/localization_benchmark/config/algorithms.yaml \
    --algo fastlio2 >/dev/null
python3 /workspace/scripts/algorithm_config.py \
    --config /root/catkin_ws/src/localization_benchmark/config/algorithms.yaml \
    --algo adaptive_w_lvio >/dev/null

echo "Build/check passed."
