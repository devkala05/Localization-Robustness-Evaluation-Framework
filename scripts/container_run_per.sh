#!/bin/bash
set -euo pipefail

PER="${1:-0}"
ATTACH="${2:---attach}"
ALGO="${3:-fastlio2}"

if ! [[ "${PER}" =~ ^[0-6]$ ]]; then
    echo "ERROR: --per must be a number from 0 to 6"
    exit 2
fi

ALGO_CONFIG="/root/catkin_ws/src/localization_benchmark/config/algorithms.yaml"
eval "$(python3 /workspace/scripts/algorithm_config.py --config "${ALGO_CONFIG}" --algo "${ALGO}")"

if [ -z "${ALGO_LAUNCH}" ] || [ -z "${ALGO_OUTPUT_TOPIC}" ]; then
    echo "ERROR: ${ALGO_ID} must define launch and output_topic in ${ALGO_CONFIG}"
    exit 2
fi

SESSION="${ALGO_RESULT_ID}_per_${PER}"
SETUP="source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash"
ROS_ENV="export ROS_MASTER_URI=http://localhost:11311 && export ROS_HOSTNAME=localhost"
BAG_PATH="/data/UrbanNav-HK_TST-20210517_sensors.bag"
BAG_RATE="${BAG_RATE:-0.5}"
GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG:-0.0}"
GT_PATH="/data/UrbanNav_TST_GT_raw.txt"
CONFIG_PATH="/root/catkin_ws/src/localization_benchmark/config/perturbations/per_${PER}.yaml"
RESULT_DIR="/data/results/${ALGO_RESULT_ID}/per_${PER}"
BASELINE_CSV="/data/results/${ALGO_RESULT_ID}/per_0/trajectory.csv"
RVIZ_CONFIG="${ALGO_RVIZ_CONFIG:-/root/catkin_ws/src/localization_benchmark/config/benchmark_paths.rviz}"

source /opt/ros/noetic/setup.bash
# Source packages are bind-mounted/read from image; do not delete them here.
cd /root/catkin_ws
if [ "${SKIP_RUNTIME_BUILD:-false}" = "true" ]; then
    source /root/catkin_ws/devel/setup.bash
    for pkg in ${ALGO_BUILD_PACKAGES}; do
        rospack find "${pkg}" >/dev/null || {
            echo "ERROR: --skip-build was used, but ROS package '${pkg}' is not available in /root/catkin_ws/devel."
            echo "Run ./build.sh once, then retry with --skip-build."
            exit 1
        }
    done
else
    echo "Building runtime packages for ${ALGO_DISPLAY}. Use --skip-build after this succeeds."
    catkin build ${ALGO_BUILD_PACKAGES} -j"${ALGO_BUILD_JOBS}" -p"${ALGO_BUILD_JOBS}" >/tmp/localization_build.log || {
        echo "ERROR: failed to build packages for ${ALGO_DISPLAY}: ${ALGO_BUILD_PACKAGES}"
        echo "Check /tmp/localization_build.log inside the container."
        exit 1
    }
    source /root/catkin_ws/devel/setup.bash
fi

test -f "${BAG_PATH}"
test -f "${GT_PATH}"
test -f "${CONFIG_PATH}"
mkdir -p "${RESULT_DIR}"

tmux kill-session -t "${SESSION}" 2>/dev/null || true
tmux new-session -d -s "${SESSION}" -x 240 -y 60

tmux rename-window -t "${SESSION}:0" "run"
ROSCORE_PANE="${SESSION}:0.0"
tmux send-keys -t "${ROSCORE_PANE}" "${SETUP} && ${ROS_ENV} && roscore" Enter
sleep 3
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=localhost
rosparam set /use_sim_time true

TF_PANE="$(tmux split-window -h -t "${ROSCORE_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${TF_PANE}" "${SETUP} && ${ROS_ENV} && ${ALGO_TF_COMMAND}" Enter

BRIDGE_PANE="$(tmux split-window -v -t "${ROSCORE_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${BRIDGE_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark custom_bridge.launch" Enter

ADAPTER_PANE="$(tmux split-window -v -t "${TF_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${ADAPTER_PANE}" "${SETUP} && ${ROS_ENV} && ${ALGO_ADAPTER_LAUNCH} run_id:=${PER} perturbation_config:=${CONFIG_PATH} native_lidar_topic:=${ALGO_NATIVE_LIDAR_TOPIC} native_imu_topic:=${ALGO_NATIVE_IMU_TOPIC} native_camera_topic:=${ALGO_NATIVE_CAMERA_TOPIC} point_time_scale:=${ALGO_POINT_TIME_SCALE}" Enter

ALGO_PANE="$(tmux new-window -t "${SESSION}" -n "algo" -P -F "#{pane_id}")"
tmux send-keys -t "${ALGO_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch ${ALGO_LAUNCH}" Enter
RECORDER_PANE="$(tmux split-window -h -t "${ALGO_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${RECORDER_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark record_output.launch algorithm:=${ALGO_RESULT_ID} run_id:=${PER} source_topic:=${ALGO_OUTPUT_TOPIC} csv_path:=${RESULT_DIR}/trajectory.csv" Enter

BAG_PANE="$(tmux new-window -t "${SESSION}" -n "bag" -P -F "#{pane_id}")"
tmux send-keys -t "${BAG_PANE}" "${SETUP} && ${ROS_ENV} && echo 'Waiting 8s for bridge, adapter, FAST-LIO, recorder, and RViz...' && echo 'In this bag window, press Space to pause/resume rosbag playback.' && sleep 8 && rosbag play --clock --rate ${BAG_RATE} ${BAG_PATH} --topics /velodyne_points /imu/data /zed2/camera/right/image_raw" Enter

STATUS_PANE="$(tmux new-window -t "${SESSION}" -n "status" -P -F "#{pane_id}")"
tmux send-keys -t "${STATUS_PANE}" "${SETUP} && ${ROS_ENV} && watch -n 2 'echo RESULT; [ -f ${RESULT_DIR}/trajectory.csv ] && wc -l ${RESULT_DIR}/trajectory.csv || true; echo; echo ALGO_OUTPUT ${ALGO_OUTPUT_TOPIC}; echo; echo TOPICS; rostopic list | egrep \"velodyne_points|mycar|cloud_registered_raw|cloud_registered$|livox/imu|Odometry|odometry|path$|camera/right|ground_truth\" || true; echo; echo RATES; timeout 1 rostopic hz /velodyne_points ${ALGO_NATIVE_LIDAR_TOPIC} ${ALGO_NATIVE_IMU_TOPIC} ${ALGO_OUTPUT_TOPIC} /camera/right/image_raw 2>/dev/null || true'" Enter

RVIZ_PANE="$(tmux new-window -t "${SESSION}" -n "rviz" -P -F "#{pane_id}")"
tmux send-keys -t "${RVIZ_PANE}" "${SETUP} && ${ROS_ENV} && rosrun fast_lio_urbannav ground_truth_path_node.py _ground_truth_path:=${GT_PATH} _topic:=/ground_truth_path _odom_topic:=/ground_truth_odometry _frame_id:=camera_init _publish_rate:=10.0 _yaw_offset_deg:=${GT_YAW_OFFSET_DEG} _publish_full_path:=true & rosrun localization_benchmark bag_clock_marker.py _frame_id:=camera_init & rosrun localization_benchmark path_from_csv.py _csv_path:=${BASELINE_CSV} _topic:=/benchmark/baseline_path _frame_id:=camera_init & rosrun localization_benchmark path_from_csv.py _csv_path:=${RESULT_DIR}/trajectory.csv _topic:=/benchmark/selected_run_path _frame_id:=camera_init & LIBGL_ALWAYS_SOFTWARE=1 MESA_LOADER_DRIVER_OVERRIDE=llvmpipe rviz -d ${RVIZ_CONFIG}" Enter

tmux select-window -t "${SESSION}:4"
echo "Started ${ALGO_DISPLAY} perturbation case per_${PER}"
echo "Algorithm key: ${ALGO_ID}"
echo "Launch: roslaunch ${ALGO_LAUNCH}"
echo "Output topic recorded: ${ALGO_OUTPUT_TOPIC}"
echo "Config: ${CONFIG_PATH}"
echo "Results: ${RESULT_DIR}/trajectory.csv"
echo "tmux windows: 0 run, 1 algo, 2 bag, 3 status, 4 rviz"
echo "RViz shows BAG /clock as cyan text. Use that time in road_segments.yaml."
echo "To pause playback, switch to tmux window 2 and press Space."
echo "Detach tmux with: Ctrl-B d"
if [ "${ATTACH}" = "--attach" ]; then
    tmux attach-session -t "${SESSION}:4"
fi
