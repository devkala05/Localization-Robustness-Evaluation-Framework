#!/usr/bin/env bash
set -euo pipefail
source /opt/ros/humble/setup.bash
if [ -f /algo_ws/install/setup.bash ]; then
  source /algo_ws/install/setup.bash
fi
ros2 launch fast_livo2 fast_livo2.launch.py output_topic:=/localization/odometry
