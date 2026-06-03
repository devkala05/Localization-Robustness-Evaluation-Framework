#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
if [ -f /algo_ws/install/setup.bash ]; then
  source /algo_ws/install/setup.bash
fi
ros2 run fast_lio fastlio_mapping \
  --ros-args \
  --params-file /algo_ws/fast_lio2_kitti.yaml \
  -r /Odometry:=/localization/odometry \
  -r /path:=/localization/path
