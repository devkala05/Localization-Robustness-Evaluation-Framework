#!/bin/bash
# Docker entrypoint for FAST-LIVO2 wrapper container.
# Sources both ROS and the catkin workspace, then executes the given command.
set -e

source /opt/ros/noetic/setup.bash
source /root/catkin_ws/devel/setup.bash

export ROS_MASTER_URI="${ROS_MASTER_URI:-http://localhost:11311}"
export ROS_HOSTNAME="${ROS_HOSTNAME:-localhost}"

exec "$@"
