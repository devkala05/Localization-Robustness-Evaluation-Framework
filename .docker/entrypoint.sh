#!/bin/bash
set -e

source /opt/ros/noetic/setup.bash

if [ -f /root/catkin_ws/devel/setup.bash ]; then
    source /root/catkin_ws/devel/setup.bash
fi

export ROS_MASTER_URI="${ROS_MASTER_URI:-http://localhost:11311}"
export ROS_HOSTNAME="${ROS_HOSTNAME:-localhost}"

exec "$@"
