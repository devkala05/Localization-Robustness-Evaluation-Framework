#!/bin/bash
set -euo pipefail

PER="${1:-0}"
ATTACH="${2:---attach}"
ALGO="${3:-fastlio2}"
ROS_PORT="${ROS_PORT:-11311}"
ROS_MASTER_URI_VALUE="http://localhost:${ROS_PORT}"

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
ROS_ENV="export ROS_MASTER_URI=${ROS_MASTER_URI_VALUE} && export ROS_HOSTNAME=localhost"
BAG_PATH="${BAG_PATH_OVERRIDE:-/data/UrbanNav-HK_TST-20210517_sensors.bag}"
BAG_RATE="${BAG_RATE:-0.5}"
GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG:-0.0}"
GT_PATH="${GT_PATH_OVERRIDE:-/data/UrbanNav_TST_GT_raw.txt}"
CONFIG_PATH="/root/catkin_ws/src/localization_benchmark/config/perturbations/per_${PER}.yaml"
RESULT_DIR="/data/results/${ALGO_RESULT_ID}/per_${PER}"
BASELINE_CSV="/data/results/${ALGO_RESULT_ID}/per_0/trajectory.csv"
RVIZ_CONFIG="${ALGO_RVIZ_CONFIG:-/root/catkin_ws/src/localization_benchmark/config/benchmark_paths.rviz}"
GPS_ENABLE="${GPS_ENABLE:-off}"
GPS_SOURCE="${GPS_SOURCE:-auto}"
GPS_FILE="${GPS_FILE:-}"
GPS_TOPIC="${GPS_TOPIC:-/gps/fix_raw}"
GPS_REQUIRED="${GPS_REQUIRED:-false}"
GPS_USE_Z="${GPS_USE_Z:-off}"
GPS_ALPHA="${GPS_ALPHA:-0.08}"

case "${GPS_ENABLE}" in
    on|true|1|yes) GPS_BOOL="true" ;;
    off|false|0|no) GPS_BOOL="false" ;;
    *) echo "ERROR: GPS_ENABLE/GPS --gps must be on/off"; exit 2 ;;
esac
case "${GPS_USE_Z}" in
    on|true|1|yes) GPS_USE_Z_BOOL="true" ;;
    *) GPS_USE_Z_BOOL="false" ;;
esac

source /opt/ros/noetic/setup.bash
cd /root/catkin_ws
if [ "${SKIP_RUNTIME_BUILD:-false}" = "true" ]; then
    source /root/catkin_ws/devel/setup.bash
    for pkg in ${ALGO_BUILD_PACKAGES}; do
        rospack find "${pkg}" >/dev/null || {
            echo "ERROR: --skip-build was used, but ROS package '${pkg}' is not available."
            echo "Build this image once without --skip-build."
            exit 1
        }
    done
else
    echo "[benchmark] runtime_build algo=${ALGO_DISPLAY}"
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

if [ "${ALGO_STANDARD_NS}" = "rtabmap" ]; then
    RTABMAP_DATABASE_PATH="${RESULT_DIR}/rtabmap.db"
    rm -f "${RTABMAP_DATABASE_PATH}"
    ALGO_LAUNCH_ARGS="${ALGO_LAUNCH_ARGS} rtabmap_database_path:=${RTABMAP_DATABASE_PATH} delete_db_on_start:=true"
fi

if [ "${ALGO_STANDARD_NS}" = "r3live" ]; then
    # Always run native r3live_mapping. The LiDAR-front-end-only executable uses
    # livox_ros_driver/CustomMsg on some upstream builds, while r3live_mapping
    # consumes sensor_msgs/PointCloud2 when lidar_type=0. This avoids silent no-odom
    # runs caused by the wrong executable/message-type pair.
    case "${R3LIVE_RUN_VISUAL:-true}" in
        off|false|0|no) R3LIVE_VISUAL_BOOL="false" ;;
        *) R3LIVE_VISUAL_BOOL="true" ;;
    esac
    ALGO_LAUNCH_ARGS="enable_fastlio_fallback:=false run_visual:=${R3LIVE_VISUAL_BOOL} native_role:=mapping"
fi

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
tmux send-keys -t "${TF_PANE}" "${SETUP} && ${ROS_ENV} && ${ALGO_TF_COMMAND}" Enter

BRIDGE_PANE="$(tmux split-window -v -t "${ROSCORE_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${BRIDGE_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark custom_bridge.launch" Enter

ADAPTER_PANE="$(tmux split-window -v -t "${TF_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${ADAPTER_PANE}" "${SETUP} && ${ROS_ENV} && ${ALGO_ADAPTER_LAUNCH} run_id:=${PER} perturbation_config:=${CONFIG_PATH} native_lidar_topic:=${ALGO_NATIVE_LIDAR_TOPIC} native_imu_topic:=${ALGO_NATIVE_IMU_TOPIC} native_camera_topic:=${ALGO_NATIVE_CAMERA_TOPIC} point_time_scale:=${ALGO_POINT_TIME_SCALE} ${ALGO_ADAPTER_ARGS}" Enter

ALGO_PANE="$(tmux new-window -t "${SESSION}" -n "algo" -P -F "#{pane_id}")"
tmux send-keys -t "${ALGO_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch ${ALGO_LAUNCH} ${ALGO_LAUNCH_ARGS}" Enter

STD_PANE="$(tmux split-window -h -t "${ALGO_PANE}" -P -F "#{pane_id}")"
STD_PUBLISH_TF=true
# RTAB-Map and Adaptive-W already publish or manage their own local frame outputs.
# Keep BenchmarkOutput TF off for them to avoid duplicate camera_init->body authority
# and TF_REPEATED_DATA warnings.
if [ "${ALGO_STANDARD_NS}" = "rtabmap" ] || [ "${ALGO_STANDARD_NS}" = "adaptive_w_lvio" ]; then
    STD_PUBLISH_TF=false
fi
tmux send-keys -t "${STD_PANE}" "${SETUP} && ${ROS_ENV} && rosrun localization_benchmark standard_output_republisher.py _source_topic:=${ALGO_OUTPUT_TOPIC} _algo_ns:=${ALGO_STANDARD_NS} _local_odom_topic:=${ALGO_LOCAL_ODOM_TOPIC} _local_path_topic:=${ALGO_LOCAL_PATH_TOPIC} _output_odom_topic:=${ALGO_SELECTED_OUTPUT_TOPIC} _output_path_topic:=${ALGO_SELECTED_PATH_TOPIC} _status_topic:=/${ALGO_STANDARD_NS}/benchmark_status _gps_enabled:=${GPS_BOOL} _publish_tf:=${STD_PUBLISH_TF:-true} _tf_child_frame:=body" Enter

GPS_PANE="$(tmux split-window -v -t "${STD_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${GPS_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark gps_provider.launch gps_enable:=${GPS_BOOL} gps_source:=${GPS_SOURCE} gps_file:=${GPS_FILE} gps_topic:=${GPS_TOPIC} gps_required:=${GPS_REQUIRED} && true" Enter

SELECT_PANE="$(tmux new-window -t "${SESSION}" -n "select_record" -P -F "#{pane_id}")"
tmux send-keys -t "${SELECT_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark gps_fusion.launch gps_enable:=${GPS_BOOL} algo_ns:=${ALGO_STANDARD_NS} local_odom_topic:=${ALGO_LOCAL_ODOM_TOPIC} output_odom_topic:=${ALGO_SELECTED_OUTPUT_TOPIC} output_path_topic:=${ALGO_SELECTED_PATH_TOPIC} status_topic:=${ALGO_STATUS_TOPIC} use_z:=${GPS_USE_Z_BOOL} position_alpha:=${GPS_ALPHA}" Enter
RECORDER_PANE="$(tmux split-window -h -t "${SELECT_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${RECORDER_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark record_output.launch algorithm:=${ALGO_RESULT_ID} run_id:=${PER} source_topic:=${ALGO_SELECTED_OUTPUT_TOPIC} csv_path:=${RESULT_DIR}/trajectory.csv" Enter

BAG_PANE="$(tmux new-window -t "${SESSION}" -n "bag" -P -F "#{pane_id}")"
tmux send-keys -t "${BAG_PANE}" "${SETUP} && ${ROS_ENV} && echo 'Waiting 8s for bridge, adapter, algorithm, output selector, recorder, and RViz...' && echo 'Press Space here to pause/resume rosbag.' && sleep 8 && rosbag play --clock --rate ${BAG_RATE} ${BAG_PATH} --topics ${ALGO_BAG_TOPICS}" Enter

STATUS_PANE="$(tmux new-window -t "${SESSION}" -n "status" -P -F "#{pane_id}")"
tmux send-keys -t "${STATUS_PANE}" "${SETUP} && ${ROS_ENV} && watch -n 2 'echo RESULT; [ -f ${RESULT_DIR}/trajectory.csv ] && wc -l ${RESULT_DIR}/trajectory.csv || true; echo; echo LOCAL ${ALGO_LOCAL_ODOM_TOPIC}; echo OUTPUT ${ALGO_SELECTED_OUTPUT_TOPIC}; echo GPS ${GPS_BOOL} ${GPS_SOURCE}; echo; echo TOPICS; rostopic list | egrep \"velodyne_points|mycar|cloud_registered|livox|Odometry|odometry|path$|camera/right|camera/image|ground_truth|gps\" || true; echo; echo RATES; timeout 1 rostopic hz ${ALGO_NATIVE_LIDAR_TOPIC} ${ALGO_NATIVE_IMU_TOPIC} ${ALGO_LOCAL_ODOM_TOPIC} ${ALGO_SELECTED_OUTPUT_TOPIC} /camera/right/image_raw /camera/image_raw /gps/fix 2>/dev/null || true'" Enter

RVIZ_PANE="$(tmux new-window -t "${SESSION}" -n "rviz" -P -F "#{pane_id}")"
tmux send-keys -t "${RVIZ_PANE}" "${SETUP} && ${ROS_ENV} && rosrun fast_lio_urbannav ground_truth_path_node.py _ground_truth_path:=${GT_PATH} _topic:=/ground_truth_path _odom_topic:=/ground_truth_odometry _frame_id:=camera_init _publish_rate:=10.0 _yaw_offset_deg:=${GT_YAW_OFFSET_DEG} _publish_full_path:=true & rosrun localization_benchmark bag_clock_marker.py _frame_id:=camera_init & rosrun localization_benchmark path_from_csv.py _csv_path:=${BASELINE_CSV} _topic:=/benchmark/baseline_path _frame_id:=camera_init & rosrun localization_benchmark path_from_csv.py _csv_path:=${RESULT_DIR}/trajectory.csv _topic:=/benchmark/selected_run_path _frame_id:=camera_init & LIBGL_ALWAYS_SOFTWARE=1 MESA_LOADER_DRIVER_OVERRIDE=llvmpipe rviz -d ${RVIZ_CONFIG}" Enter

tmux select-window -t "${SESSION}:5"
echo "[benchmark] mode=interactive algo=${ALGO_DISPLAY} key=${ALGO_ID} case=per_${PER}"
echo "[benchmark] launch=roslaunch ${ALGO_LAUNCH} ${ALGO_LAUNCH_ARGS}"
echo "[benchmark] topics native=${ALGO_OUTPUT_TOPIC} selected=${ALGO_SELECTED_OUTPUT_TOPIC}"
echo "[benchmark] gps=${GPS_BOOL} source=${GPS_SOURCE} file=${GPS_FILE:-none}"
echo "[benchmark] csv=${RESULT_DIR}/trajectory.csv"
echo "[benchmark] tmux=run,algo,select_record,bag,status,rviz detach=Ctrl-B-d"
if [ "${ATTACH}" = "--attach" ]; then
    tmux attach-session -t "${SESSION}:5"
fi
