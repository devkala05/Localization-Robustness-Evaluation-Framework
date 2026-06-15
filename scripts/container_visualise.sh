#!/bin/bash
set -euo pipefail

# Standalone dataset/ground-truth visualiser used inside the FAST-LIO image.
# It deliberately uses the same dataset registry and adapter layer as ./run.sh.
DATASET_ID="${DATASET_ID:-e2o}"
ATTACH="--attach"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dataset) DATASET_ID="${2:-}"; shift 2;;
    --dataset=*) DATASET_ID="${1#*=}"; shift;;
    --attach) ATTACH="--attach"; shift;;
    --no-attach) ATTACH="--no-attach"; shift;;
    *) echo "ERROR: unknown argument: $1" >&2; exit 2;;
  esac
done

eval "$(python3 /workspace/scripts/dataset_config.py \
  --config /workspace/wrappers/localization_benchmark/config/datasets.yaml \
  --dataset "${DATASET_ID}")"

ROS_PORT="${ROS_PORT:-11311}"
ROS_MASTER_URI_VALUE="http://localhost:${ROS_PORT}"
SESSION="visualise_${DATASET_ID}"
SETUP="source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash"
ROS_ENV="export ROS_MASTER_URI=${ROS_MASTER_URI_VALUE} && export ROS_HOSTNAME=localhost"
BAG_PATH="${BAG_PATH_OVERRIDE:-${DATASET_DEFAULT_BAG}}"
GT_PATH="${GT_PATH_OVERRIDE:-${DATASET_DEFAULT_GT}}"
BAG_RATE="${BAG_RATE:-0.5}"
GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG:-0.0}"
PERTURBATION_CONFIG="${DATASET_PERTURBATIONS_DIR}/per_0.yaml"

source /opt/ros/noetic/setup.bash
cd /root/catkin_ws
catkin build custom_localization_msgs localization_benchmark fast_lio_urbannav >/tmp/localization_build.log
source /root/catkin_ws/devel/setup.bash

test -f "${BAG_PATH}" || { echo "ERROR: bag not found: ${BAG_PATH}" >&2; exit 2; }
test -f "${GT_PATH}" || { echo "ERROR: ground truth not found: ${GT_PATH}" >&2; exit 2; }
test -f "${DATASET_STATIC_TF_YAML}" || { echo "ERROR: TF YAML not found: ${DATASET_STATIC_TF_YAML}" >&2; exit 2; }

BRIDGE_CMD="roslaunch localization_benchmark custom_bridge.launch dataset:=${DATASET_LABEL} source_lidar_topic:=${DATASET_SOURCE_LIDAR_TOPIC} source_imu_topic:=${DATASET_SOURCE_IMU_TOPIC} source_camera_topic:=${DATASET_SOURCE_CAMERA_TOPIC} source_left_camera_topic:=${DATASET_SOURCE_LEFT_CAMERA_TOPIC}"
ADAPTER_CMD="roslaunch localization_benchmark custom_fastlio_adapter.launch run_id:=0 perturbation_config:=${PERTURBATION_CONFIG} native_lidar_frame_id:=${DATASET_LIDAR_FRAME} native_imu_frame_id:=${DATASET_IMU_FRAME} camera_frame_id:=${DATASET_CAMERA_FRAME} camera_info_yaml:=${DATASET_CAMERA_INFO_YAML} point_time_field:=${DATASET_POINT_TIME_FIELD} point_time_unit:=${DATASET_POINT_TIME_UNIT} publish_left_camera:=false"
TF_CMD="rosrun localization_benchmark dataset_tf_broadcaster.py _config_path:=${DATASET_STATIC_TF_YAML} _publish_map_odom:=true _publish_camera_init_map:=true _publish_base_link_body:=true"

# shellcheck disable=SC2086  # DATASET_BAG_TOPICS is intentionally word-split into ROS topics.
BAG_CMD="rosbag play --clock --rate ${BAG_RATE} ${BAG_PATH} --topics ${DATASET_BAG_TOPICS}"

STATUS_PATTERN="cloud_registered_raw|livox/imu|camera/right|ground_truth|${DATASET_SOURCE_LIDAR_TOPIC#/}|${DATASET_SOURCE_IMU_TOPIC#/}"

tmux kill-session -t "${SESSION}" 2>/dev/null || true
tmux new-session -d -s "${SESSION}" -x 240 -y 60
tmux rename-window -t "${SESSION}:0" "run"
ROSCORE_PANE="${SESSION}:0.0"
tmux send-keys -t "${ROSCORE_PANE}" "${SETUP} && ${ROS_ENV} && roscore -p ${ROS_PORT}" Enter
sleep 3
export ROS_MASTER_URI="${ROS_MASTER_URI_VALUE}"
export ROS_HOSTNAME=localhost
rosparam set /use_sim_time true

TF_PANE="$(tmux split-window -h -t "${ROSCORE_PANE}" -P -F '#{pane_id}')"
tmux send-keys -t "${TF_PANE}" "${SETUP} && ${ROS_ENV} && ${TF_CMD}" Enter
BRIDGE_PANE="$(tmux split-window -v -t "${ROSCORE_PANE}" -P -F '#{pane_id}')"
tmux send-keys -t "${BRIDGE_PANE}" "${SETUP} && ${ROS_ENV} && ${BRIDGE_CMD}" Enter
ADAPTER_PANE="$(tmux split-window -v -t "${TF_PANE}" -P -F '#{pane_id}')"
tmux send-keys -t "${ADAPTER_PANE}" "${SETUP} && ${ROS_ENV} && ${ADAPTER_CMD}" Enter

BAG_PANE="$(tmux new-window -t "${SESSION}" -n bag -P -F '#{pane_id}')"
tmux send-keys -t "${BAG_PANE}" "${SETUP} && ${ROS_ENV} && echo 'Press Space here to pause/resume rosbag playback.' && sleep 8 && ${BAG_CMD}" Enter

STATUS_PANE="$(tmux new-window -t "${SESSION}" -n status -P -F '#{pane_id}')"
tmux send-keys -t "${STATUS_PANE}" "${SETUP} && ${ROS_ENV} && watch -n 2 'echo CLOCK; timeout 1 rostopic echo -n 1 /clock 2>/dev/null || true; echo; echo TOPICS; rostopic list | egrep \"${STATUS_PATTERN}\" || true; echo; echo RATES; timeout 1 rostopic hz /cloud_registered_raw /livox/imu /camera/right/image_raw 2>/dev/null || true'" Enter

RVIZ_PANE="$(tmux new-window -t "${SESSION}" -n rviz -P -F '#{pane_id}')"
tmux send-keys -t "${RVIZ_PANE}" "${SETUP} && ${ROS_ENV} && rosrun fast_lio_urbannav ground_truth_path_node.py _ground_truth_path:=${GT_PATH} _topic:=/ground_truth_path _odom_topic:=/ground_truth_odometry _frame_id:=${DATASET_WORLD_FRAME} _publish_rate:=10.0 _yaw_offset_deg:=${GT_YAW_OFFSET_DEG} _publish_full_path:=true & rosrun localization_benchmark bag_clock_marker.py _frame_id:=${DATASET_WORLD_FRAME} & LIBGL_ALWAYS_SOFTWARE=1 MESA_LOADER_DRIVER_OVERRIDE=llvmpipe rviz -d \$(rospack find localization_benchmark)/config/benchmark_paths.rviz" Enter

tmux select-window -t "${SESSION}:3"
echo "Started ${DATASET_DISPLAY} visualisation in tmux session ${SESSION}"
echo "bag=${BAG_PATH} gt=${GT_PATH} lidar=${DATASET_SOURCE_LIDAR_TOPIC} imu=${DATASET_SOURCE_IMU_TOPIC}"
echo "tmux windows: 0 run, 1 bag, 2 status, 3 rviz; detach with Ctrl-B d"
if [ "${ATTACH}" = "--attach" ]; then tmux attach-session -t "${SESSION}:3"; fi
