#!/bin/bash
set -euo pipefail

PER="${1:-0}"
if ! [[ "${PER}" =~ ^[0-6]$ ]]; then
    echo "ERROR: per must be a number from 0 to 6"
    exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/data"
IMAGE_NAME="${IMAGE_NAME:-lvisam-urbannav:latest}"
CONTAINER_NAME="lvisam_run_${PER}"

BAG_PATH="${DATA_DIR}/UrbanNav-HK_TST-20210517_sensors.bag"
GT_PATH="${DATA_DIR}/UrbanNav_TST_GT_raw.txt"
CONFIG_PATH="${SCRIPT_DIR}/wrappers/localization_benchmark/config/perturbations/per_${PER}.yaml"
SEGMENTS_PATH="${SCRIPT_DIR}/wrappers/localization_benchmark/config/road_segments.yaml"
RESULT_DIR="${DATA_DIR}/results/lvi_sam/per_${PER}"

test -f "${BAG_PATH}" || { echo "ERROR: missing bag: ${BAG_PATH}"; exit 1; }
test -f "${GT_PATH}" || { echo "ERROR: missing GT: ${GT_PATH}"; exit 1; }
test -f "${CONFIG_PATH}" || { echo "ERROR: missing perturbation config: ${CONFIG_PATH}"; exit 1; }
test -f "${SEGMENTS_PATH}" || { echo "ERROR: missing road segments: ${SEGMENTS_PATH}"; exit 1; }

BAG_RATE="${BAG_RATE:-0.35}"
GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG:-0.0}"

xhost +local:docker 2>/dev/null || true
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

if ! mkdir -p "${RESULT_DIR}" 2>/dev/null; then
    echo "Host cannot create ${RESULT_DIR}; creating it through Docker and fixing ownership."
    docker run --rm \
        -e HOST_UID="$(id -u)" \
        -e HOST_GID="$(id -g)" \
        -v "${DATA_DIR}":/data \
        "${IMAGE_NAME}" \
        bash -lc "mkdir -p /data/results/lvi_sam/per_${PER} && chown -R \"\${HOST_UID}:\${HOST_GID}\" /data/results"
fi

echo "Starting LVI-SAM per_${PER}"
echo "Results: ${RESULT_DIR}"
echo "Bag rate: ${BAG_RATE}x (timestamps stay original /clock)"
echo "GT yaw offset: ${GT_YAW_OFFSET_DEG} deg"

DOCKER_ARGS=(
    --name "${CONTAINER_NAME}"
    --network host
    --privileged
    ${DOCKER_CPUS:+--cpus=${DOCKER_CPUS}}
    --memory="${DOCKER_MEMORY:-10g}"
    -e DISPLAY="${DISPLAY:-:0}"
    -e ROS_MASTER_URI=http://localhost:11311
    -e ROS_HOSTNAME=localhost
    -e HOST_UID="$(id -u)"
    -e HOST_GID="$(id -g)"
    -e BAG_RATE="${BAG_RATE}"
    -e GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG}"
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw
    -v "${DATA_DIR}":/data
    -v "${SCRIPT_DIR}/wrappers/localization_benchmark":/root/catkin_ws/src/localization_benchmark:ro
    -v "${SCRIPT_DIR}/wrappers/fast-lio_urbannav":/root/catkin_ws/src/fast_lio_urbannav:ro
    -v "${SCRIPT_DIR}/wrappers/lvi_sam_urbannav":/root/catkin_ws/src/lvi_sam_urbannav:ro
    -v "${SCRIPT_DIR}/algorithms/lvi_sam/config":/root/catkin_ws/src/lvi_sam/config:ro
    -v "${SCRIPT_DIR}/wrappers/localization_benchmark/config/perturbations":/workspace/perturbations:ro
    -v "${SEGMENTS_PATH}":/workspace/road_segments.yaml:ro
)

docker run -d "${DOCKER_ARGS[@]}" "${IMAGE_NAME}" bash -lc "
set -euo pipefail
source /opt/ros/noetic/setup.bash
source /root/catkin_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=localhost

cleanup() {
    set +e
    rosnode kill /localization_output_recorder >/dev/null 2>&1
    pkill -TERM -f 'roslaunch|rosrun|roscore|rosmaster|rosout|rviz' >/dev/null 2>&1
    if [ -n \"\${HOST_UID:-}\" ] && [ -n \"\${HOST_GID:-}\" ]; then
        chown -R \"\${HOST_UID}:\${HOST_GID}\" /data/results/lvi_sam/per_${PER} >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

roscore &
sleep 3
rosparam set /use_sim_time true

rosrun fast_lio_urbannav tf_broadcaster_node.py _publish_map_odom:=false _publish_camera_init_map:=true _publish_base_link_body:=true &
roslaunch localization_benchmark custom_bridge.launch &
sleep 2

roslaunch localization_benchmark custom_fastlio_adapter.launch \
    run_id:=${PER} \
    perturbation_config:=/workspace/perturbations/per_${PER}.yaml \
    native_lidar_topic:=/cloud_registered_raw \
    native_imu_topic:=/livox/imu \
    native_camera_topic:=/camera/right/image_raw &
sleep 2

roslaunch lvi_sam_urbannav lvisam_urbannav.launch &
sleep 3

roslaunch localization_benchmark record_output.launch \
    algorithm:=lvi_sam \
    run_id:=${PER} \
    source_topic:=/lvi_sam/odometry/mapping \
    csv_path:=/data/results/lvi_sam/per_${PER}/trajectory.csv &
sleep 2

rosrun fast_lio_urbannav ground_truth_path_node.py \
    _ground_truth_path:=/data/UrbanNav_TST_GT_raw.txt \
    _topic:=/ground_truth_path \
    _odom_topic:=/ground_truth_odometry \
    _frame_id:=camera_init \
    _publish_rate:=10.0 \
    _yaw_offset_deg:="${GT_YAW_OFFSET_DEG}" \
    _publish_full_path:=true &

rosrun localization_benchmark bag_clock_marker.py _frame_id:=camera_init &

if [ -f /data/results/lvi_sam/per_0/trajectory.csv ]; then
    rosrun localization_benchmark path_from_csv.py \
        _csv_path:=/data/results/lvi_sam/per_0/trajectory.csv \
        _topic:=/benchmark/baseline_path \
        _frame_id:=camera_init &
fi

rosrun localization_benchmark path_from_csv.py \
    _csv_path:=/data/results/lvi_sam/per_${PER}/trajectory.csv \
    _topic:=/benchmark/selected_run_path \
    _frame_id:=camera_init &

LIBGL_ALWAYS_SOFTWARE=1 MESA_LOADER_DRIVER_OVERRIDE=llvmpipe \
    rviz -d \$(rospack find localization_benchmark)/config/benchmark_paths.rviz &
sleep 2

rosbag play --clock --rate "${BAG_RATE}" /data/UrbanNav-HK_TST-20210517_sensors.bag \
    --topics /velodyne_points /imu/data /zed2/camera/right/image_raw

rosnode kill /localization_output_recorder >/dev/null 2>&1 || true
sleep 2

BASELINE_ARGS=()
if [ -f /data/results/lvi_sam/per_0/trajectory.csv ] && [ \"${PER}\" != \"0\" ]; then
    BASELINE_ARGS=(--baseline-csv /data/results/lvi_sam/per_0/trajectory.csv)
fi

rosrun localization_benchmark evaluate_run.py \
    --gt /data/UrbanNav_TST_GT_raw.txt \
    --run-csv /data/results/lvi_sam/per_${PER}/trajectory.csv \
    \"\${BASELINE_ARGS[@]}\" \
    --segments /workspace/road_segments.yaml \
    --perturbations /workspace/perturbations/per_${PER}.yaml \
    --out-dir /data/results/lvi_sam/per_${PER}

rosrun localization_benchmark summarize_robustness.py \
    --results-root /data/results/lvi_sam \
    --out /data/results/lvi_sam/robustness_ranking.txt || true

echo 'LVI-SAM per_${PER} complete.'
"

docker logs -f "${CONTAINER_NAME}"
