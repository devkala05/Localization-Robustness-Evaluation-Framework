#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-}"
DATASET="${2:-}"
BAG_ARG="${3:-}"
if [[ -z "${MODE}" || -z "${DATASET}" || -z "${BAG_ARG}" ]]; then
  cat <<USAGE
Usage:
  ./run.sh fast_livo2 e2o /path/to/one_loop.bag
  ./run.sh orbslam3 e2o /path/to/one_loop.bag
  ./run.sh lvisam e2o /path/to/one_loop.bag
  ./run.sh fusion e2o /path/to/one_loop.bag
  ./run.sh fusion_navigation e2o /path/to/one_loop.bag
Environment: BAG_RATE, RVIZ=true|false, TF_MODE=direct|map_to_odom|none,
             PRIMARY_SOURCE=fast_livo2|orbslam3, NAVIGATION_LAUNCH_FILE=/workspace/...
             FAULT_INJECTION=true|false, LIDAR_TOPIC, IMU_TOPIC, CAMERA_TOPIC
             SENSOR_CONFIG, FAST_CONFIG, ORB_CONFIG, LVISAM_LIDAR_CONFIG,
             LVISAM_CAMERA_CONFIG, FUSION_CONFIG
USAGE
  exit 2
fi
case "${MODE}" in fast_livo2|orbslam3|lvisam|fusion|fusion_navigation) ;; *) echo "Unknown mode: ${MODE}" >&2; exit 2;; esac
[[ "${DATASET}" == "e2o" ]] || { echo "Only the E2O dataset is supported." >&2; exit 2; }
BAG="$(realpath "${BAG_ARG}")"
[[ -f "${BAG}" ]] || { echo "Bag not found: ${BAG}" >&2; exit 2; }

<<<<<<< Updated upstream
BAG_RATE="${BAG_RATE:-1.0}"
=======
if [[ -n "${BAG_RATE:-}" ]]; then
  BAG_RATE="${BAG_RATE}"
elif [[ "${MODE}" == "fast_livo2" || "${MODE}" == "lvisam" ]]; then
  # The pinned CPU implementation processes this LIVO dataset below real time.
  # Slow offline playback prevents its large native subscriber queues building lag.
  BAG_RATE="0.5"
else
  BAG_RATE="1.0"
fi
>>>>>>> Stashed changes
RVIZ="${RVIZ:-false}"
RVIZ_CONFIG="${RVIZ_CONFIG:-}"
TF_MODE="${TF_MODE:-direct}"
PRIMARY_SOURCE="${PRIMARY_SOURCE:-fast_livo2}"
FAULT_INJECTION="${FAULT_INJECTION:-false}"
FAST_SAVE_PCD="${FAST_SAVE_PCD:-false}"
LIDAR_TOPIC="${LIDAR_TOPIC:-/lidar103/velodyne_points}"
IMU_TOPIC="${IMU_TOPIC:-/mavros/imu/data}"
CAMERA_TOPIC="${CAMERA_TOPIC:-/camera/color/image_raw}"
SENSOR_CONFIG="${SENSOR_CONFIG:-/workspace/wrappers/localization_benchmark/config/e2o.yaml}"
FAST_CONFIG="${FAST_CONFIG:-/workspace/wrappers/fast_livo2_e2o/config/fast_livo2_e2o.yaml}"
ORB_CONFIG="${ORB_CONFIG:-/workspace/wrappers/orbslam3_e2o/config/e2o_front_mono_orbslam3.yaml}"
ORB_STANDALONE_SCALE="${ORB_STANDALONE_SCALE:-1.0}"
LVISAM_LIDAR_CONFIG="${LVISAM_LIDAR_CONFIG:-/workspace/wrappers/lvisam_e2o/config/params_lidar_e2o.yaml}"
LVISAM_CAMERA_CONFIG="${LVISAM_CAMERA_CONFIG:-/workspace/wrappers/lvisam_e2o/config/params_camera_e2o.yaml}"
FUSION_CONFIG="${FUSION_CONFIG:-/workspace/wrappers/e2o_localization_fusion/config/fusion.yaml}"
RUN_ID="$(date +%Y%m%d_%H%M%S)_${MODE}_$$"
OUT_HOST="${ROOT}/data/output/${RUN_ID}"
OUT_CONTAINER="/data/output/${RUN_ID}"
mkdir -p "${OUT_HOST}"
cat > "${OUT_HOST}/run_metadata.env" <<EOF
RUN_ID=${RUN_ID}
MODE=${MODE}
DATASET=e2o
BAG=${BAG}
BAG_RATE=${BAG_RATE}
TF_MODE=${TF_MODE}
PRIMARY_SOURCE=${PRIMARY_SOURCE}
FAULT_INJECTION=${FAULT_INJECTION}
FAST_SAVE_PCD=${FAST_SAVE_PCD}
LIDAR_TOPIC=${LIDAR_TOPIC}
IMU_TOPIC=${IMU_TOPIC}
CAMERA_TOPIC=${CAMERA_TOPIC}
SENSOR_CONFIG=${SENSOR_CONFIG}
FAST_CONFIG=${FAST_CONFIG}
ORB_CONFIG=${ORB_CONFIG}
ORB_STANDALONE_SCALE=${ORB_STANDALONE_SCALE}
LVISAM_LIDAR_CONFIG=${LVISAM_LIDAR_CONFIG}
LVISAM_CAMERA_CONFIG=${LVISAM_CAMERA_CONFIG}
FUSION_CONFIG=${FUSION_CONFIG}
EOF
STACK="e2o_loc_${RUN_ID}"
cat >> "${OUT_HOST}/run_metadata.env" <<EOF
STACK=${STACK}
FAST_CONTAINER=${STACK}_fast
ORB_CONTAINER=${STACK}_orb
FUSION_CONTAINER=${STACK}_fusion
FUSION_NAV_CONTAINER=${STACK}_fusion_nav
LVISAM_CONTAINER=${STACK}_lvisam
EOF
CONTAINERS=()

common_args=(--network host -e ROS_MASTER_URI=http://localhost:11311 -e ROS_HOSTNAME=localhost \
  -v "${ROOT}/data/output:/data/output" -v "${ROOT}:/workspace:ro")
start_container() {
  local name="$1" image="$2"; shift 2
  docker rm -f "${name}" >/dev/null 2>&1 || true
  docker run -d --name "${name}" "${common_args[@]}" "${image}" "$@" >/dev/null
  CONTAINERS+=("${name}")
}
cleanup() {
  local code=$?
  for ((idx=${#CONTAINERS[@]}-1; idx>=0; idx--)); do
    docker stop -t 5 "${CONTAINERS[$idx]}" >/dev/null 2>&1 || true
    docker rm -f "${CONTAINERS[$idx]}" >/dev/null 2>&1 || true
  done
  echo "[run] output=${OUT_HOST}"
  exit "${code}"
}
trap cleanup EXIT INT TERM

for image in e2o-localization-fusion:latest; do
  docker image inspect "${image}" >/dev/null 2>&1 || { echo "Missing ${image}; run ./build.sh fusion" >&2; exit 1; }
done
if [[ "${MODE}" == "fast_livo2" || "${MODE}" == fusion* ]]; then
  docker image inspect fastlivo2-e2o:latest >/dev/null 2>&1 || { echo "Missing fastlivo2-e2o:latest; run ./build.sh fast_livo2" >&2; exit 1; }
fi
if [[ "${MODE}" == "orbslam3" || "${MODE}" == fusion* ]]; then
  docker image inspect orbslam3-e2o:latest >/dev/null 2>&1 || { echo "Missing orbslam3-e2o:latest; run ./build.sh orbslam3" >&2; exit 1; }
fi
if [[ "${MODE}" == "lvisam" ]]; then
  docker image inspect lvisam-e2o:latest >/dev/null 2>&1 || { echo "Missing lvisam-e2o:latest; run ./build.sh lvisam" >&2; exit 1; }
fi

start_container "${STACK}_roscore" e2o-localization-fusion:latest roscore
sleep 2
start_container "${STACK}_input" e2o-localization-fusion:latest \
  bash -lc 'cp /workspace/wrappers/localization_benchmark/scripts/e2o_sensor_adapter.py /root/catkin_ws/devel/.private/localization_benchmark/lib/localization_benchmark/e2o_sensor_adapter.py && cp /workspace/wrappers/localization_benchmark/scripts/e2o_static_tf_publisher.py /root/catkin_ws/devel/.private/localization_benchmark/lib/localization_benchmark/e2o_static_tf_publisher.py && source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH} && rospack profile >/dev/null && exec roslaunch /workspace/wrappers/localization_benchmark/launch/e2o_input_pipeline.launch "$@"' _ \
    config:="${SENSOR_CONFIG}" source_lidar_topic:="${LIDAR_TOPIC}" \
    source_imu_topic:="${IMU_TOPIC}" source_camera_topic:="${CAMERA_TOPIC}"

if [[ "${MODE}" == "fast_livo2" || "${MODE}" == fusion* ]]; then
  start_container "${STACK}_fast" fastlivo2-e2o:latest \
    roslaunch fast_livo2_e2o algorithm.launch config_path:="${FAST_CONFIG}" pcd_save_en:="${FAST_SAVE_PCD}" \
      output_topic:="$( [[ "${FAULT_INJECTION}" == "true" ]] && echo /fault/raw/fast_livo2 || echo /fast_livo2/odometry )" pcd_path:="${OUT_CONTAINER}/fast_livo2_map.pcd"
fi
if [[ "${MODE}" == "orbslam3" || "${MODE}" == fusion* ]]; then
  ORB_POSE_SCALE="1.0"
  [[ "${MODE}" == "orbslam3" ]] && ORB_POSE_SCALE="${ORB_STANDALONE_SCALE}"
  start_container "${STACK}_orb" orbslam3-e2o:latest \
    roslaunch orbslam3_e2o algorithm.launch camera_config:="${ORB_CONFIG}" fixed_pose_scale:="${ORB_POSE_SCALE}" output_odom_topic:="$( [[ "${FAULT_INJECTION}" == "true" ]] && echo /fault/raw/orbslam3 || echo /orbslam3/camera_odometry )"
fi
if [[ "${MODE}" == "lvisam" ]]; then
  start_container "${STACK}_lvisam" lvisam-e2o:latest \
    roslaunch lvisam_e2o algorithm.launch lidar_config:="${LVISAM_LIDAR_CONFIG}" \
      camera_config:="${LVISAM_CAMERA_CONFIG}" output_topic:="/lvisam/odometry"
fi

if [[ "${MODE}" == "fusion" ]]; then
  start_container "${STACK}_fusion" e2o-localization-fusion:latest \
    bash -lc 'for f in fusion_math.py localization_health_monitor.py fusion_node.py cmd_vel_safety_gate.py multi_trajectory_recorder.py pose_fault_injector.py; do cp "/workspace/wrappers/e2o_localization_fusion/scripts/${f}" "/root/catkin_ws/devel/.private/e2o_localization_fusion/lib/e2o_localization_fusion/${f}"; done && source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH} && rospack profile >/dev/null && exec roslaunch /workspace/wrappers/e2o_localization_fusion/launch/fusion.launch "$@"' _ \
      config:="${FUSION_CONFIG}" output_dir:="${OUT_CONTAINER}" \
      tf_mode:="${TF_MODE}" primary_source:="${PRIMARY_SOURCE}" enable_fault_injection:="${FAULT_INJECTION}"
elif [[ "${MODE}" == "fusion_navigation" ]]; then
  NAV_FILE="${NAVIGATION_LAUNCH_FILE:-}"
  NAV_ARGS=(start_navigation:=false)
  if [[ -n "${NAV_FILE}" ]]; then
    NAV_ARGS=(start_navigation:=true navigation_launch_file:="${NAV_FILE}")
  fi
  start_container "${STACK}_fusion_nav" e2o-localization-fusion:latest \
    bash -lc 'for f in fusion_math.py localization_health_monitor.py fusion_node.py cmd_vel_safety_gate.py multi_trajectory_recorder.py pose_fault_injector.py; do cp "/workspace/wrappers/e2o_localization_fusion/scripts/${f}" "/root/catkin_ws/devel/.private/e2o_localization_fusion/lib/e2o_localization_fusion/${f}"; done && source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH} && rospack profile >/dev/null && exec roslaunch /workspace/wrappers/e2o_localization_fusion/launch/fusion_navigation.launch "$@"' _ \
      config:="${FUSION_CONFIG}" output_dir:="${OUT_CONTAINER}" \
      tf_mode:="${TF_MODE}" primary_source:="${PRIMARY_SOURCE}" enable_fault_injection:="${FAULT_INJECTION}" "${NAV_ARGS[@]}"
else
  start_container "${STACK}_health" e2o-localization-fusion:latest \
    bash -lc 'for f in fusion_math.py localization_health_monitor.py fusion_node.py cmd_vel_safety_gate.py multi_trajectory_recorder.py pose_fault_injector.py; do cp "/workspace/wrappers/e2o_localization_fusion/scripts/${f}" "/root/catkin_ws/devel/.private/e2o_localization_fusion/lib/e2o_localization_fusion/${f}"; done && source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH} && rospack profile >/dev/null && exec roslaunch /workspace/wrappers/e2o_localization_fusion/launch/health_only.launch "$@"' _ \
      config:="${FUSION_CONFIG}" output_dir:="${OUT_CONTAINER}" enable_fault_injection:="${FAULT_INJECTION}"
fi

if [[ "${RVIZ}" == "true" ]]; then
  if [[ -z "${RVIZ_CONFIG}" ]]; then
    case "${MODE}" in
      fast_livo2) RVIZ_CONFIG="/workspace/rviz/e2o_fast_livo2.rviz" ;;
      orbslam3) RVIZ_CONFIG="/workspace/rviz/e2o_orbslam3.rviz" ;;
      lvisam) RVIZ_CONFIG="/workspace/rviz/e2o_lvisam.rviz" ;;
      *) RVIZ_CONFIG="/workspace/rviz/e2o_fusion.rviz" ;;
    esac
  fi
  xhost +local:docker >/dev/null 2>&1 || true
  docker rm -f "${STACK}_rviz" >/dev/null 2>&1 || true
  docker run -d --name "${STACK}_rviz" "${common_args[@]}" -e DISPLAY="${DISPLAY:-:0}" \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw e2o-localization-fusion:latest \
    rviz -d "${RVIZ_CONFIG}" >/dev/null
  CONTAINERS+=("${STACK}_rviz")
fi

sleep "${STARTUP_DELAY_SEC:-10}"
for name in "${CONTAINERS[@]}"; do
  [[ "$(docker inspect -f '{{.State.Running}}' "${name}" 2>/dev/null || echo false)" == "true" ]] || {
    echo "Container failed before bag playback: ${name}" >&2
    docker logs "${name}" >&2 || true
    exit 1
  }
done

echo "[run] mode=${MODE} dataset=e2o bag=${BAG} rate=${BAG_RATE} output=${OUT_HOST}"
BAG_DIR="$(dirname "${BAG}")"
BAG_FILE="$(basename "${BAG}")"
docker run --rm --network host -e ROS_MASTER_URI=http://localhost:11311 -e ROS_HOSTNAME=localhost \
  -v "${BAG_DIR}:/bags:ro" e2o-localization-fusion:latest \
  rosbag play --quiet --clock --rate "${BAG_RATE}" "/bags/${BAG_FILE}" --topics \
    "${LIDAR_TOPIC}" "${IMU_TOPIC}" "${CAMERA_TOPIC}"
sleep 3
