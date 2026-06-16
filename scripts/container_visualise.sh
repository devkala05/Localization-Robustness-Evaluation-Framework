#!/bin/bash
set -euo pipefail

ROS_PORT="${ROS_PORT:-11311}"
ROS_MASTER_URI_VALUE="http://localhost:${ROS_PORT}"

ATTACH="${1:---attach}"
SESSION="visualise_dataset"
SETUP="source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash"
ROS_ENV="export ROS_MASTER_URI=${ROS_MASTER_URI_VALUE} && export ROS_HOSTNAME=localhost"
BAG_PATH="/data/UrbanNav-HK_TST-20210517_sensors.bag"
GT_PATH="/data/UrbanNav_TST_GT_raw.txt"
BAG_RATE="${BAG_RATE:-0.5}"
GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG:-0.0}"

source /opt/ros/noetic/setup.bash
rm -rf /root/catkin_ws/src/fast_lio_urbannav
cd /root/catkin_ws
catkin build custom_localization_msgs localization_benchmark fast_lio_urbannav >/tmp/localization_build.log
source /root/catkin_ws/devel/setup.bash

test -f "${BAG_PATH}"
test -f "${GT_PATH}"

tmux kill-session -t "${SESSION}" 2>/dev/null || true
tmux new-session -d -s "${SESSION}" -x 240 -y 60

tmux rename-window -t "${SESSION}:0" "run"
ROSCORE_PANE="${SESSION}:0.0"
tmux send-keys -t "${ROSCORE_PANE}" "${SETUP} && ${ROS_ENV} && roscore -p ${ROS_PORT}" Enter
sleep 3
export ROS_MASTER_URI=${ROS_MASTER_URI_VALUE}
export ROS_HOSTNAME=localhost
rosparam set /use_sim_time true

TF_PANE="$(tmux split-window -h -t "${ROSCORE_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${TF_PANE}" "${SETUP} && ${ROS_ENV} && rosrun fast_lio_urbannav tf_broadcaster_node.py _publish_map_odom:=true" Enter

BRIDGE_PANE="$(tmux split-window -v -t "${ROSCORE_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${BRIDGE_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark custom_bridge.launch" Enter

ADAPTER_PANE="$(tmux split-window -v -t "${TF_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${ADAPTER_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark custom_fastlio_adapter.launch run_id:=0 perturbation_config:=/root/catkin_ws/src/localization_benchmark/config/perturbations/per_0.yaml" Enter

BAG_PANE="$(tmux new-window -t "${SESSION}" -n "bag" -P -F "#{pane_id}")"
tmux send-keys -t "${BAG_PANE}" "${SETUP} && ${ROS_ENV} && echo 'In this bag window, press Space to pause/resume rosbag playback.' && sleep 8 && rosbag play --clock --rate ${BAG_RATE} ${BAG_PATH} --topics /velodyne_points /imu/data /zed2/camera/right/image_raw" Enter

STATUS_PANE="$(tmux new-window -t "${SESSION}" -n "status" -P -F "#{pane_id}")"
tmux send-keys -t "${STATUS_PANE}" "${SETUP} && ${ROS_ENV} && watch -n 2 'echo CLOCK; timeout 1 rostopic echo -n 1 /clock 2>/dev/null || true; echo; echo TOPICS; rostopic list | egrep \"velodyne_points|mycar|cloud_registered_raw|livox/imu|camera/right|ground_truth\" || true; echo; echo RATES; timeout 1 rostopic hz /velodyne_points /cloud_registered_raw /livox/imu /camera/right/image_raw 2>/dev/null || true'" Enter

RVIZ_PANE="$(tmux new-window -t "${SESSION}" -n "rviz" -P -F "#{pane_id}")"
tmux send-keys -t "${RVIZ_PANE}" "${SETUP} && ${ROS_ENV} && rosrun fast_lio_urbannav ground_truth_path_node.py _ground_truth_path:=${GT_PATH} _topic:=/ground_truth_path _odom_topic:=/ground_truth_odometry _frame_id:=camera_init _publish_rate:=10.0 _yaw_offset_deg:=${GT_YAW_OFFSET_DEG} _publish_full_path:=true & rosrun localization_benchmark bag_clock_marker.py _frame_id:=camera_init & LIBGL_ALWAYS_SOFTWARE=1 MESA_LOADER_DRIVER_OVERRIDE=llvmpipe rviz -d \$(rospack find localization_benchmark)/config/benchmark_paths.rviz" Enter

tmux select-window -t "${SESSION}:3"
echo "Started dataset visualisation in tmux session ${SESSION}"
echo "tmux windows: 0 run, 1 bag, 2 status, 3 rviz"
echo "RViz shows BAG /clock as cyan text. Use that time in road_segments.yaml."
echo "To pause playback, switch to tmux window 1 and press Space."
echo "Detach tmux with: Ctrl-B d"
if [ "${ATTACH}" = "--attach" ]; then
    tmux attach-session -t "${SESSION}:3"
fi
