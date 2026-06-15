#!/bin/bash
set -euo pipefail

PER="${1:-0}"
DURATION="${2:-0}"
ALGO="${3:-fastlio2}"
ROS_PORT="${ROS_PORT:-11311}"
ROS_MASTER_URI_VALUE="http://localhost:${ROS_PORT}"

if ! [[ "${PER}" =~ ^[0-6]$ ]]; then
    echo "ERROR: --per must be a number from 0 to 6"
    exit 2
fi

if ! [[ "${DURATION}" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    echo "ERROR: duration must be a number of seconds, or 0 for full bag"
    exit 2
fi

SETUP="source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash"
ROS_ENV="export ROS_MASTER_URI=${ROS_MASTER_URI_VALUE} && export ROS_HOSTNAME=localhost"
BAG_PATH="/data/UrbanNav-HK_TST-20210517_sensors.bag"
GT_PATH="/data/UrbanNav_TST_GT_raw.txt"
CONFIG_PATH="/root/catkin_ws/src/localization_benchmark/config/perturbations/per_${PER}.yaml"
SEGMENTS_PATH="/root/catkin_ws/src/localization_benchmark/config/road_segments.yaml"
ALGO_CONFIG="/root/catkin_ws/src/localization_benchmark/config/algorithms.yaml"
eval "$(python3 /workspace/scripts/algorithm_config.py --config "${ALGO_CONFIG}" --algo "${ALGO}")"

if [ -z "${ALGO_LAUNCH}" ] || [ -z "${ALGO_OUTPUT_TOPIC}" ]; then
    echo "ERROR: ${ALGO_ID} must define launch and output_topic in ${ALGO_CONFIG}"
    exit 2
fi

RESULTS_ROOT="/data/results/${ALGO_RESULT_ID}"
STAMP="$(date +%Y%m%d_%H%M%S)"
RESULT_DIR="${RESULTS_ROOT}/per_${PER}_${ALGO_RESULT_ID}_${STAMP}"
LATEST_DIR="${RESULTS_ROOT}/per_${PER}"
CSV_PATH="${RESULT_DIR}/trajectory.csv"
BASELINE_CSV="${RESULTS_ROOT}/per_0/trajectory.csv"
RVIZ_CONFIG="${ALGO_RVIZ_CONFIG:-/root/catkin_ws/src/localization_benchmark/config/benchmark_paths.rviz}"
BAG_PATH="${BAG_PATH_OVERRIDE:-${BAG_PATH}}"
GT_PATH="${GT_PATH_OVERRIDE:-${GT_PATH}}"
GPS_ENABLE="${GPS_ENABLE:-off}"
GPS_SOURCE="${GPS_SOURCE:-auto}"
GPS_FILE="${GPS_FILE:-}"
GPS_TOPIC="${GPS_TOPIC:-/gps/fix_raw}"
GPS_REQUIRED="${GPS_REQUIRED:-false}"
GPS_USE_Z="${GPS_USE_Z:-off}"
GPS_ALPHA="${GPS_ALPHA:-0.08}"
case "${GPS_ENABLE}" in on|true|1|yes) GPS_BOOL="true" ;; *) GPS_BOOL="false" ;; esac
case "${GPS_USE_Z}" in on|true|1|yes) GPS_USE_Z_BOOL="true" ;; *) GPS_USE_Z_BOOL="false" ;; esac
PIDS=()

cleanup() {
    set +e
    rosnode kill /localization_output_recorder >/dev/null 2>&1
    sleep 1
    for pid in "${PIDS[@]:-}"; do
        kill "${pid}" >/dev/null 2>&1
    done
    pkill -TERM -f "rviz|roslaunch|rosrun|roscore|rosmaster|rosout" >/dev/null 2>&1
    if [ -n "${HOST_UID:-}" ] && [ -n "${HOST_GID:-}" ] && [ -d "${RESULT_DIR:-}" ]; then
        chown -R "${HOST_UID}:${HOST_GID}" "${RESULT_DIR}" "${LATEST_DIR}" "${RESULTS_ROOT}/robustness_ranking.txt" >/dev/null 2>&1
    fi
}
trap cleanup EXIT

source /opt/ros/noetic/setup.bash
# Source packages are bind-mounted/read from image; do not delete them here.
cd /root/catkin_ws
if [ "${SKIP_RUNTIME_BUILD:-false}" = "true" ]; then
    source /root/catkin_ws/devel/setup.bash
    for pkg in ${ALGO_BUILD_PACKAGES}; do
        rospack find "${pkg}" >/dev/null || {
            echo "ERROR: --skip-build was used, but ROS package '${pkg}' is not available in /root/catkin_ws/devel."
            echo "Run the matching ./build_<algorithm>.sh once, then retry with --skip-build."
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
test -f "${SEGMENTS_PATH}"
mkdir -p "${RESULT_DIR}" "${LATEST_DIR}"

if [ "${ALGO_STANDARD_NS}" = "rtabmap" ]; then
    RTABMAP_DATABASE_PATH="${RESULT_DIR}/rtabmap.db"
    rm -f "${RTABMAP_DATABASE_PATH}"
    ALGO_LAUNCH_ARGS="${ALGO_LAUNCH_ARGS} rtabmap_database_path:=${RTABMAP_DATABASE_PATH} delete_db_on_start:=true"
fi

if [ "${ALGO_STANDARD_NS}" = "r3live" ]; then
    case "${R3LIVE_RUN_VISUAL:-true}" in
        true|on|1|yes) R3LIVE_VISUAL_BOOL="true"; R3LIVE_NATIVE_ROLE="mapping" ;;
        *) R3LIVE_VISUAL_BOOL="false"; R3LIVE_NATIVE_ROLE="stable" ;;
    esac
    # Do not use FAST-LIO2 fallback for benchmark output. If native R3LIVE does
    # not publish, the watchdog/mux will show that clearly instead of recording
    # a FAST-LIO2 trajectory as R3LIVE.
    ALGO_LAUNCH_ARGS="enable_fastlio_fallback:=false run_visual:=${R3LIVE_VISUAL_BOOL} native_role:=${R3LIVE_NATIVE_ROLE}"
fi

echo "[benchmark] mode=summary algo=${ALGO_DISPLAY} key=${ALGO_ID} case=per_${PER}"
echo "[benchmark] output=${RESULT_DIR}"
echo "[benchmark] topics native=${ALGO_OUTPUT_TOPIC} selected=${ALGO_SELECTED_OUTPUT_TOPIC}"
echo "[benchmark] gps=${GPS_BOOL} source=${GPS_SOURCE} file=${GPS_FILE:-none}"
if [ "${DURATION}" != "0" ]; then
    echo "[benchmark] duration=${DURATION}s"
fi

bash -lc "${SETUP} && ${ROS_ENV} && roscore -p ${ROS_PORT}" &
PIDS+=("$!")
sleep 3
export ROS_MASTER_URI=${ROS_MASTER_URI_VALUE}
export ROS_HOSTNAME=localhost
rosparam set /use_sim_time true

bash -lc "${SETUP} && ${ROS_ENV} && ${ALGO_TF_COMMAND}" &
PIDS+=("$!")

bash -lc "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark custom_bridge.launch" &
PIDS+=("$!")

bash -lc "${SETUP} && ${ROS_ENV} && ${ALGO_ADAPTER_LAUNCH} run_id:=${PER} perturbation_config:=${CONFIG_PATH} native_lidar_topic:=${ALGO_NATIVE_LIDAR_TOPIC} native_imu_topic:=${ALGO_NATIVE_IMU_TOPIC} native_camera_topic:=${ALGO_NATIVE_CAMERA_TOPIC} point_time_scale:=${ALGO_POINT_TIME_SCALE} ${ALGO_ADAPTER_ARGS}" &
PIDS+=("$!")

bash -lc "${SETUP} && ${ROS_ENV} && roslaunch ${ALGO_LAUNCH} ${ALGO_LAUNCH_ARGS}" &
PIDS+=("$!")

STD_PUBLISH_TF=true
# RTAB-Map and Adaptive-W already publish or manage their own local frame outputs.
# Keep BenchmarkOutput TF off for them to avoid duplicate camera_init->body authority
# and TF_REPEATED_DATA warnings.
if [ "${ALGO_STANDARD_NS}" = "rtabmap" ] || [ "${ALGO_STANDARD_NS}" = "adaptive_w_lvio" ]; then
    STD_PUBLISH_TF=false
fi

bash -lc "${SETUP} && ${ROS_ENV} && rosrun localization_benchmark standard_output_republisher.py _source_topic:=${ALGO_OUTPUT_TOPIC} _algo_ns:=${ALGO_STANDARD_NS} _local_odom_topic:=${ALGO_LOCAL_ODOM_TOPIC} _local_path_topic:=${ALGO_LOCAL_PATH_TOPIC} _output_odom_topic:=${ALGO_SELECTED_OUTPUT_TOPIC} _output_path_topic:=${ALGO_SELECTED_PATH_TOPIC} _status_topic:=/${ALGO_STANDARD_NS}/benchmark_status _gps_enabled:=${GPS_BOOL} _publish_tf:=${STD_PUBLISH_TF:-true} _tf_child_frame:=body" &
PIDS+=("$!")

bash -lc "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark gps_provider.launch gps_enable:=${GPS_BOOL} gps_source:=${GPS_SOURCE} gps_file:=${GPS_FILE} gps_topic:=${GPS_TOPIC} gps_required:=${GPS_REQUIRED}" &
PIDS+=("$!")

bash -lc "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark gps_fusion.launch gps_enable:=${GPS_BOOL} algo_ns:=${ALGO_STANDARD_NS} local_odom_topic:=${ALGO_LOCAL_ODOM_TOPIC} output_odom_topic:=${ALGO_SELECTED_OUTPUT_TOPIC} output_path_topic:=${ALGO_SELECTED_PATH_TOPIC} status_topic:=${ALGO_STATUS_TOPIC} use_z:=${GPS_USE_Z_BOOL} position_alpha:=${GPS_ALPHA}" &
PIDS+=("$!")

bash -lc "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark record_output.launch algorithm:=${ALGO_RESULT_ID} run_id:=${PER} source_topic:=${ALGO_SELECTED_OUTPUT_TOPIC} csv_path:=${CSV_PATH}" &
PIDS+=("$!")

bash -lc "${SETUP} && ${ROS_ENV} && rosrun fast_lio_urbannav ground_truth_path_node.py _ground_truth_path:=${GT_PATH} _topic:=/ground_truth_path _odom_topic:=/ground_truth_odometry _frame_id:=camera_init _publish_rate:=10.0 _yaw_offset_deg:=${GT_YAW_OFFSET_DEG:-0.0} _publish_full_path:=true" &
PIDS+=("$!")

bash -lc "${SETUP} && ${ROS_ENV} && rosrun localization_benchmark bag_clock_marker.py _frame_id:=camera_init" &
PIDS+=("$!")

if [ -f "${BASELINE_CSV}" ]; then
    bash -lc "${SETUP} && ${ROS_ENV} && rosrun localization_benchmark path_from_csv.py _csv_path:=${BASELINE_CSV} _topic:=/benchmark/baseline_path _frame_id:=camera_init" &
    PIDS+=("$!")
fi

bash -lc "${SETUP} && ${ROS_ENV} && LIBGL_ALWAYS_SOFTWARE=1 MESA_LOADER_DRIVER_OVERRIDE=llvmpipe rviz -d ${RVIZ_CONFIG}" &
PIDS+=("$!")

echo "[benchmark] waiting_for_nodes=8s"
sleep 8

BAG_DURATION_ARGS=()
if [ "${DURATION}" != "0" ]; then
    BAG_DURATION_ARGS=(--duration="${DURATION}")
fi

echo "[benchmark] playing_rosbag bag=${BAG_PATH} rate=${BAG_RATE:-0.35}"
bash -lc "${SETUP} && ${ROS_ENV} && rosbag play --clock --rate ${BAG_RATE:-0.35} ${BAG_DURATION_ARGS[*]} ${BAG_PATH} --topics ${ALGO_BAG_TOPICS}"

echo "[benchmark] bag_finished evaluating=true"
rosnode kill /localization_output_recorder >/dev/null 2>&1 || true
sleep 3

cp "${CSV_PATH}" "${LATEST_DIR}/trajectory.csv"

BASELINE_ARGS=()
if [ -f "${BASELINE_CSV}" ]; then
    BASELINE_ARGS=(--baseline-csv "${BASELINE_CSV}")
fi

rosrun localization_benchmark evaluate_run.py \
    --gt "${GT_PATH}" \
    --run-csv "${CSV_PATH}" \
    --gt-yaw-offset-deg "${GT_YAW_OFFSET_DEG:-0.0}" \
    --algorithm-note "${ALGO_NOTES:-}" \
    --gps-mode "${GPS_ENABLE}" \
    --gps-source "${GPS_SOURCE}" \
    --rtk-mode "${RTK_MODE:-auto}" \
    "${BASELINE_ARGS[@]}" \
    --segments "${SEGMENTS_PATH}" \
    --perturbations "${CONFIG_PATH}" \
    --out-dir "${RESULT_DIR}"

rosrun localization_benchmark summarize_robustness.py \
    --results-root "${RESULTS_ROOT}" \
    --out "${RESULTS_ROOT}/robustness_ranking.txt"

if [ -n "${HOST_UID:-}" ] && [ -n "${HOST_GID:-}" ]; then
    chown -R "${HOST_UID}:${HOST_GID}" "${RESULT_DIR}" "${LATEST_DIR}" "${RESULTS_ROOT}/robustness_ranking.txt" >/dev/null 2>&1 || true
fi

echo "[benchmark] summary_complete"
echo "[benchmark] csv=${CSV_PATH}"
echo "[benchmark] analysis=${RESULT_DIR}/analysis.txt"
echo "[benchmark] result_dir=${RESULT_DIR}"
echo "[benchmark] ranking=${RESULTS_ROOT}/robustness_ranking.txt"
