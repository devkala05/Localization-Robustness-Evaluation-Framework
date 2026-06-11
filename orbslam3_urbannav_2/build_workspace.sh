#!/bin/bash
# ============================================================
# build_workspace.sh  —  Build the catkin workspace INSIDE
#                         the running Docker container
# ============================================================
set -euo pipefail

CATKIN_WS=/root/catkin_ws
ROS_DISTRO=noetic

echo "═══════════════════════════════════════════════════════"
echo "  Building catkin workspace: ${CATKIN_WS}"
echo "═══════════════════════════════════════════════════════"

source /opt/ros/${ROS_DISTRO}/setup.bash

cd ${CATKIN_WS}

rosdep install --from-paths src --ignore-src -r -y \
    --rosdistro=${ROS_DISTRO} || true

catkin build \
    -DCMAKE_BUILD_TYPE=Release \
    --summarize

echo ""
echo "✓  Workspace built."
echo "Source with: source ${CATKIN_WS}/devel/setup.bash"
