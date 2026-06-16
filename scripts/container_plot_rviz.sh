#!/bin/bash
set -euo pipefail

ROS_PORT="${ROS_PORT:-11321}"
export ROS_MASTER_URI="http://localhost:${ROS_PORT}"
export ROS_HOSTNAME="localhost"
RVIZ_CONFIG="${RVIZ_CONFIG:-/workspace/wrappers/localization_benchmark/config/offline_trajectory_compare.rviz}"

cleanup() {
  pkill -TERM -f "offline_rviz_paths.py|rviz|roscore|rosmaster|rosout" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

source /opt/ros/noetic/setup.bash
# The mounted Python script is run directly, so a fresh catkin install is not required.
if [ -f /root/catkin_ws/devel/setup.bash ]; then
  source /root/catkin_ws/devel/setup.bash || true
fi

roscore -p "${ROS_PORT}" >/tmp/offline_plot_roscore.log 2>&1 &
sleep 2

if [ ! -f "${RVIZ_CONFIG}" ]; then
  echo "ERROR: missing RViz config: ${RVIZ_CONFIG}"
  exit 1
fi

python3 /workspace/wrappers/localization_benchmark/scripts/offline_rviz_paths.py "$@" >/tmp/offline_plot_publisher.log 2>&1 &
sleep 2

echo "Offline trajectory RViz running."
echo "Logs inside container:"
echo "  /tmp/offline_plot_roscore.log"
echo "  /tmp/offline_plot_publisher.log"
echo "Topics:"
echo "  /ground_truth_path"
echo "  /offline/trajectory_markers"
echo "  /offline/<algo>/path"

LIBGL_ALWAYS_SOFTWARE=1 MESA_LOADER_DRIVER_OVERRIDE=llvmpipe rviz -d "${RVIZ_CONFIG}"
