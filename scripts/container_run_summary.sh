#!/bin/bash
set -euo pipefail

PER="${1:-0}"
DURATION="${2:-0}"
ALGO="${3:-fastlio2}"

if ! [[ "${PER}" =~ ^[0-6]$ ]]; then
    echo "ERROR: --per must be a number from 0 to 6"
    exit 2
fi

if ! [[ "${DURATION}" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    echo "ERROR: duration must be a number of seconds, or 0 for full bag"
    exit 2
fi

SETUP="source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash"
ROS_ENV="export ROS_MASTER_URI=http://localhost:11311 && export ROS_HOSTNAME=localhost"
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
test -f "${SEGMENTS_PATH}"
mkdir -p "${RESULT_DIR}" "${LATEST_DIR}"

echo "Starting one-pass summary run"
echo "Algorithm: ${ALGO_DISPLAY} (${ALGO_ID})"
echo "Case: per_${PER}"
echo "Config: ${CONFIG_PATH}"
echo "Output: ${RESULT_DIR}"
if [ "${DURATION}" != "0" ]; then
    echo "Duration limit: ${DURATION}s"
fi

bash -lc "${SETUP} && ${ROS_ENV} && roscore" &
PIDS+=("$!")
sleep 3
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=localhost
rosparam set /use_sim_time true

bash -lc "${SETUP} && ${ROS_ENV} && ${ALGO_TF_COMMAND}" &
PIDS+=("$!")

bash -lc "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark custom_bridge.launch" &
PIDS+=("$!")

bash -lc "${SETUP} && ${ROS_ENV} && ${ALGO_ADAPTER_LAUNCH} run_id:=${PER} perturbation_config:=${CONFIG_PATH} native_lidar_topic:=${ALGO_NATIVE_LIDAR_TOPIC} native_imu_topic:=${ALGO_NATIVE_IMU_TOPIC} native_camera_topic:=${ALGO_NATIVE_CAMERA_TOPIC} point_time_scale:=${ALGO_POINT_TIME_SCALE}" &
PIDS+=("$!")

bash -lc "${SETUP} && ${ROS_ENV} && roslaunch ${ALGO_LAUNCH}" &
PIDS+=("$!")

bash -lc "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark record_output.launch algorithm:=${ALGO_RESULT_ID} run_id:=${PER} source_topic:=${ALGO_OUTPUT_TOPIC} csv_path:=${CSV_PATH}" &
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

echo "Waiting 8s for ROS nodes and RViz..."
sleep 8

BAG_DURATION_ARGS=()
if [ "${DURATION}" != "0" ]; then
    BAG_DURATION_ARGS=(--duration="${DURATION}")
fi

echo "Playing rosbag once. RViz shows /clock in the Time panel."
bash -lc "${SETUP} && ${ROS_ENV} && rosbag play --clock --rate ${BAG_RATE:-0.35} ${BAG_DURATION_ARGS[*]} ${BAG_PATH} --topics /velodyne_points /imu/data /zed2/camera/right/image_raw"

echo "Bag finished. Closing recorder and evaluating..."
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

echo "Summary complete"
echo "CSV: ${CSV_PATH}"
echo "Analysis: ${RESULT_DIR}/analysis.txt"
echo "Generated files are in: ${RESULT_DIR}"
echo "Ranking: ${RESULTS_ROOT}/robustness_ranking.txt"
