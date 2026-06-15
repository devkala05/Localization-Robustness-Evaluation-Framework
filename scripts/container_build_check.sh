#!/bin/bash
set -euo pipefail

source /opt/ros/noetic/setup.bash
# Source packages are bind-mounted/read from image; do not delete them here.
cd /root/catkin_ws

echo "Checking dataset-independent configs..."
test -f /root/catkin_ws/src/localization_benchmark/config/datasets.yaml
test -f /root/catkin_ws/src/localization_benchmark/config/datasets/e2o/front_camera_info.yaml
test -f /root/catkin_ws/src/localization_benchmark/config/datasets/e2o/static_transforms.yaml

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
    test -f "/root/catkin_ws/src/localization_benchmark/config/perturbations/e2o/per_${per}.yaml"
done

echo "Checking algorithm config..."
python3 /workspace/scripts/algorithm_config.py \
    --config /root/catkin_ws/src/localization_benchmark/config/algorithms.yaml \
    --algo fastlio2 --dataset e2o >/dev/null
python3 /workspace/scripts/algorithm_config.py \
    --config /root/catkin_ws/src/localization_benchmark/config/algorithms.yaml \
    --algo adaptive_w_lvio --dataset e2o >/dev/null
python3 /workspace/scripts/algorithm_config.py \
    --config /root/catkin_ws/src/localization_benchmark/config/algorithms.yaml \
    --algo r3live --dataset e2o >/dev/null

python3 /workspace/scripts/algorithm_config.py \
    --config /root/catkin_ws/src/localization_benchmark/config/algorithms.yaml \
    --algo lvisam --dataset e2o >/dev/null

python3 /workspace/scripts/algorithm_config.py \
    --config /root/catkin_ws/src/localization_benchmark/config/algorithms.yaml \
    --algo fastlivo2 --dataset e2o >/dev/null

python3 /workspace/scripts/algorithm_config.py \
    --config /root/catkin_ws/src/localization_benchmark/config/algorithms.yaml \
    --algo rtabmap --dataset e2o >/dev/null

python3 /workspace/scripts/algorithm_config.py \
    --config /root/catkin_ws/src/localization_benchmark/config/algorithms.yaml \
    --algo orbslam3 --dataset e2o >/dev/null

echo "Build/check passed."
