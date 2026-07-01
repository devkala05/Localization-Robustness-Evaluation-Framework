#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE="${1:-}"
DATASET="${2:-}"
BAG_ARG="${3:-}"

FUSION_IMAGE="e2o-localization-fusion:latest"
FAST_IMAGE="fastlivo2-e2o:latest"
ORB_IMAGE="orbslam3-e2o:latest"
LVISAM_IMAGE="lvisam-e2o:latest"

INPUT_OVERLAY_CMD='for f in e2o_sensor_adapter.py e2o_static_tf_publisher.py; do cp "/workspace/wrappers/localization_benchmark/scripts/${f}" "/root/catkin_ws/devel/.private/localization_benchmark/lib/localization_benchmark/${f}" && chmod +x "/root/catkin_ws/devel/.private/localization_benchmark/lib/localization_benchmark/${f}"; done && source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH} && rospack profile >/dev/null && exec roslaunch /workspace/wrappers/localization_benchmark/launch/e2o_input_pipeline.launch "$@"'
ORB_OVERLAY_CMD='cp /workspace/wrappers/orbslam3_e2o/scripts/pose_republisher_node.py /root/catkin_ws/devel/.private/orbslam3_e2o/lib/orbslam3_e2o/pose_republisher_node.py && chmod +x /root/catkin_ws/devel/.private/orbslam3_e2o/lib/orbslam3_e2o/pose_republisher_node.py && source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH} && rospack profile >/dev/null && exec roslaunch /workspace/wrappers/orbslam3_e2o/launch/algorithm.launch "$@"'
FUSION_OVERLAY_CMD='for f in fusion_math.py localization_health_monitor.py fusion_node.py cmd_vel_safety_gate.py multi_trajectory_recorder.py pose_fault_injector.py; do cp "/workspace/wrappers/e2o_localization_fusion/scripts/${f}" "/root/catkin_ws/devel/.private/e2o_localization_fusion/lib/e2o_localization_fusion/${f}"; done && source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH} && rospack profile >/dev/null && exec roslaunch "$@"'

usage() {
  cat <<'USAGE'
Usage:
  ./run.sh fast_livo2 e2o /path/to/one_loop.bag
  ./run.sh orbslam3 e2o /path/to/one_loop.bag
  ./run.sh lvisam e2o /path/to/one_loop.bag
  ./run.sh fusion e2o /path/to/one_loop.bag
  ./run.sh lvisam_fusion e2o /path/to/one_loop.bag
  ./run.sh fusion_navigation e2o /path/to/one_loop.bag

Modes:
  fast_livo2          FAST-LIVO2 only, plus health/recorder.
  orbslam3           ORB-SLAM3 only, plus health/recorder.
  lvisam             LVI-SAM only, plus health/recorder.
  fusion             FAST-LIVO2 + ORB-SLAM3 fusion.
  lvisam_fusion      LVI-SAM + ORB-SLAM3 fusion.
  fusion_2           Backwards-compatible alias for lvisam_fusion.
  fusion_navigation  FAST-LIVO2 + ORB-SLAM3 fusion with navigation safety gate.

Environment:
  BAG_RATE, RVIZ=true|false, TF_MODE=direct|map_to_odom|none
  PRIMARY_SOURCE=fast_livo2|lvisam|orbslam3
  NAVIGATION_LAUNCH_FILE=/workspace/...
  FAULT_INJECTION=true|false
  EVALUATE_AFTER_RUN=true|false, EVAL_GT=/path/to/reference.csv
  Default evaluation reference: data/e2o/ground_truth/ref.csv
  LIDAR_TOPIC, IMU_TOPIC, CAMERA_TOPIC
  SENSOR_CONFIG, FAST_CONFIG, ORB_CONFIG
  LVISAM_LIDAR_CONFIG, LVISAM_CAMERA_CONFIG, FUSION_CONFIG
  LVISAM_ENABLE_VISUAL=false|true, LVISAM_TF_TOPIC, LVISAM_TF_STATIC_TOPIC
USAGE
}

fail() {
  echo "$*" >&2
  exit 2
}

is_mode() {
  [[ "$MODE" == "$1" ]]
}

is_lvisam_fusion_mode() {
  is_mode lvisam_fusion || is_mode fusion_2
}

is_known_mode() {
  case "$MODE" in
    fast_livo2|orbslam3|lvisam|fusion|lvisam_fusion|fusion_2|fusion_navigation) return 0 ;;
    *) return 1 ;;
  esac
}

needs_fast() {
  is_mode fast_livo2 || is_mode fusion || is_mode fusion_navigation
}

needs_orb() {
  is_mode orbslam3 || is_mode fusion || is_lvisam_fusion_mode || is_mode fusion_navigation
}

needs_lvisam() {
  is_mode lvisam || is_lvisam_fusion_mode
}

uses_fusion_node() {
  is_mode fusion || is_lvisam_fusion_mode || is_mode fusion_navigation
}

default_bag_rate() {
  if [[ -n "${BAG_RATE:-}" ]]; then
    printf '%s\n' "$BAG_RATE"
  elif is_mode fast_livo2 || is_mode fusion || is_mode fusion_navigation || is_mode lvisam || is_lvisam_fusion_mode; then
    # The pinned CPU implementation processes this LIVO dataset below real time.
    # Slow offline playback prevents its large native subscriber queues building lag.
    printf '0.5\n'
  else
    printf '1.0\n'
  fi
}

default_primary_source() {
  if [[ -n "${PRIMARY_SOURCE:-}" ]]; then
    printf '%s\n' "$PRIMARY_SOURCE"
  elif is_lvisam_fusion_mode; then
    printf 'lvisam\n'
  else
    printf 'fast_livo2\n'
  fi
}

default_fusion_config() {
  if [[ -n "${FUSION_CONFIG:-}" ]]; then
    printf '%s\n' "$FUSION_CONFIG"
  elif is_lvisam_fusion_mode; then
    printf '/workspace/wrappers/e2o_localization_fusion/config/fusion_2.yaml\n'
  else
    printf '/workspace/wrappers/e2o_localization_fusion/config/fusion.yaml\n'
  fi
}

require_image() {
  local image="$1" hint="$2"
  docker image inspect "$image" >/dev/null 2>&1 || {
    echo "Missing ${image}; run ${hint}" >&2
    exit 1
  }
}

start_container() {
  local name="$1" image="$2"
  shift 2
  docker rm -f "$name" >/dev/null 2>&1 || true
  docker run -d --name "$name" "${COMMON_DOCKER_ARGS[@]}" "$image" "$@" >/dev/null
  CONTAINERS+=("$name")
}

start_input_pipeline() {
  start_container "${STACK}_input" "$FUSION_IMAGE" \
    bash -lc "$INPUT_OVERLAY_CMD" _ \
      config:="$SENSOR_CONFIG" \
      source_lidar_topic:="$LIDAR_TOPIC" \
      source_imu_topic:="$IMU_TOPIC" \
      source_camera_topic:="$CAMERA_TOPIC" \
      source_depth_topic:="$DEPTH_TOPIC"
}

fault_or_direct_topic() {
  local fault_topic="$1" direct_topic="$2"
  if [[ "$FAULT_INJECTION" == "true" ]]; then
    printf '%s\n' "$fault_topic"
  else
    printf '%s\n' "$direct_topic"
  fi
}

start_fast_livo2() {
  start_container "${STACK}_fast" "$FAST_IMAGE" \
    roslaunch fast_livo2_e2o algorithm.launch \
      config_path:="$FAST_CONFIG" \
      pcd_save_en:="$FAST_SAVE_PCD" \
      output_topic:="$(fault_or_direct_topic /fault/raw/fast_livo2 /fast_livo2/odometry)" \
      pcd_path:="${OUT_CONTAINER}/fast_livo2_map.pcd"
}

start_orbslam3() {
  start_container "${STACK}_orb" "$ORB_IMAGE" \
    bash -lc "$ORB_OVERLAY_CMD" _ \
      camera_config:="$ORB_CONFIG" \
      output_odom_topic:="$(fault_or_direct_topic /fault/raw/orbslam3 /orbslam3/camera_odometry)"
}

start_lvisam() {
  local lvisam_tf_topic="${LVISAM_TF_TOPIC:-/tf}"
  local lvisam_tf_static_topic="${LVISAM_TF_STATIC_TOPIC:-/tf_static}"
  if ! is_mode lvisam; then
    lvisam_tf_topic="${LVISAM_TF_TOPIC:-/native/lvisam/tf}"
    lvisam_tf_static_topic="${LVISAM_TF_STATIC_TOPIC:-/native/lvisam/tf_static}"
  fi
  start_container "${STACK}_lvisam" "$LVISAM_IMAGE" \
    roslaunch lvisam_e2o algorithm.launch \
      lidar_config:="$LVISAM_LIDAR_CONFIG" \
      camera_config:="$LVISAM_CAMERA_CONFIG" \
      output_topic:="$(fault_or_direct_topic /fault/raw/lvisam /lvisam/odometry)" \
      enable_visual:="$LVISAM_ENABLE_VISUAL" \
      tf_topic:="$lvisam_tf_topic" \
      tf_static_topic:="$lvisam_tf_static_topic"
}

start_fusion() {
  start_container "${STACK}_fusion" "$FUSION_IMAGE" \
    bash -lc "$FUSION_OVERLAY_CMD" _ \
      /workspace/wrappers/e2o_localization_fusion/launch/fusion.launch \
      config:="$FUSION_CONFIG" \
      output_dir:="$OUT_CONTAINER" \
      tf_mode:="$TF_MODE" \
      primary_source:="$PRIMARY_SOURCE" \
      enable_fault_injection:="$FAULT_INJECTION"
}

start_fusion_navigation() {
  local nav_file="${NAVIGATION_LAUNCH_FILE:-}"
  local nav_args=(start_navigation:=false)
  if [[ -n "$nav_file" ]]; then
    nav_args=(start_navigation:=true navigation_launch_file:="$nav_file")
  fi
  start_container "${STACK}_fusion_nav" "$FUSION_IMAGE" \
    bash -lc "$FUSION_OVERLAY_CMD" _ \
      /workspace/wrappers/e2o_localization_fusion/launch/fusion_navigation.launch \
      config:="$FUSION_CONFIG" \
      output_dir:="$OUT_CONTAINER" \
      tf_mode:="$TF_MODE" \
      primary_source:="$PRIMARY_SOURCE" \
      enable_fault_injection:="$FAULT_INJECTION" \
      "${nav_args[@]}"
}

start_health_only() {
  start_container "${STACK}_health" "$FUSION_IMAGE" \
    bash -lc "$FUSION_OVERLAY_CMD" _ \
      /workspace/wrappers/e2o_localization_fusion/launch/health_only.launch \
      config:="$FUSION_CONFIG" \
      output_dir:="$OUT_CONTAINER" \
      enable_fault_injection:="$FAULT_INJECTION"
}

default_rviz_config() {
  case "$MODE" in
    fast_livo2) printf '/workspace/rviz/e2o_fast_livo2.rviz\n' ;;
    orbslam3) printf '/workspace/rviz/e2o_orbslam3.rviz\n' ;;
    lvisam) printf '/workspace/rviz/e2o_lvisam.rviz\n' ;;
    *) printf '/workspace/rviz/e2o_fusion.rviz\n' ;;
  esac
}

start_rviz() {
  [[ "$RVIZ" == "true" ]] || return 0
  [[ -n "$RVIZ_CONFIG" ]] || RVIZ_CONFIG="$(default_rviz_config)"
  xhost +local:docker >/dev/null 2>&1 || true
  docker rm -f "${STACK}_rviz" >/dev/null 2>&1 || true
  docker run -d --name "${STACK}_rviz" "${COMMON_DOCKER_ARGS[@]}" \
    -e DISPLAY="${DISPLAY:-:0}" \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    "$FUSION_IMAGE" rviz -d "$RVIZ_CONFIG" >/dev/null
  CONTAINERS+=("${STACK}_rviz")
}

cleanup() {
  local code=$?
  set +e
  for ((idx=${#CONTAINERS[@]}-1; idx>=0; idx--)); do
    docker stop -t 5 "${CONTAINERS[$idx]}" >/dev/null 2>&1 || true
    docker rm -f "${CONTAINERS[$idx]}" >/dev/null 2>&1 || true
  done
  if [[ "$code" -eq 0 && "${EVALUATE_AFTER_RUN:-true}" == "true" ]]; then
    echo "[run] evaluating output=${OUT_HOST}"
    if [[ -n "${EVAL_GT:-}" ]]; then
      "${ROOT}/evaluation/evaluate.sh" "$OUT_HOST" "$EVAL_GT"
    else
      "${ROOT}/evaluation/evaluate.sh" "$OUT_HOST"
    fi
    code=$?
  fi
  echo "[run] output=${OUT_HOST}"
  exit "$code"
}

write_metadata() {
  cat > "$OUT_HOST/run_metadata.env" <<EOF
RUN_ID=${RUN_ID}
MODE=${MODE}
DATASET=e2o
BAG=${BAG}
BAG_RATE=${BAG_RATE}
TF_MODE=${TF_MODE}
PRIMARY_SOURCE=${PRIMARY_SOURCE}
FAULT_INJECTION=${FAULT_INJECTION}
EVALUATE_AFTER_RUN=${EVALUATE_AFTER_RUN}
EVAL_GT=${EVAL_GT}
FAST_SAVE_PCD=${FAST_SAVE_PCD}
LIDAR_TOPIC=${LIDAR_TOPIC}
IMU_TOPIC=${IMU_TOPIC}
CAMERA_TOPIC=${CAMERA_TOPIC}
DEPTH_TOPIC=${DEPTH_TOPIC}
SENSOR_CONFIG=${SENSOR_CONFIG}
FAST_CONFIG=${FAST_CONFIG}
ORB_CONFIG=${ORB_CONFIG}
LVISAM_LIDAR_CONFIG=${LVISAM_LIDAR_CONFIG}
LVISAM_CAMERA_CONFIG=${LVISAM_CAMERA_CONFIG}
LVISAM_ENABLE_VISUAL=${LVISAM_ENABLE_VISUAL}
FUSION_CONFIG=${FUSION_CONFIG}
STACK=${STACK}
FAST_CONTAINER=${STACK}_fast
ORB_CONTAINER=${STACK}_orb
FUSION_CONTAINER=${STACK}_fusion
FUSION_NAV_CONTAINER=${STACK}_fusion_nav
LVISAM_CONTAINER=${STACK}_lvisam
EOF
}

check_started_containers() {
  sleep "${STARTUP_DELAY_SEC:-10}"
  for name in "${CONTAINERS[@]}"; do
    [[ "$(docker inspect -f '{{.State.Running}}' "$name" 2>/dev/null || echo false)" == "true" ]] || {
      echo "Container failed before bag playback: ${name}" >&2
      docker logs "$name" >&2 || true
      exit 1
    }
  done
}

play_bag() {
  local bag_dir bag_file
  bag_dir="$(dirname "$BAG")"
  bag_file="$(basename "$BAG")"
  docker run --rm --network host \
    -e ROS_MASTER_URI=http://localhost:11311 \
    -e ROS_HOSTNAME=localhost \
    -v "${bag_dir}:/bags:ro" \
    "$FUSION_IMAGE" \
    rosbag play --quiet --clock --rate "$BAG_RATE" "/bags/${bag_file}" --topics \
      "$LIDAR_TOPIC" "$IMU_TOPIC" "$CAMERA_TOPIC" "$DEPTH_TOPIC"
  sleep 3
}

if [[ -z "$MODE" || -z "$DATASET" || -z "$BAG_ARG" ]]; then
  usage
  exit 2
fi
is_known_mode || fail "Unknown mode: ${MODE}"
[[ "$DATASET" == "e2o" ]] || fail "Only the E2O dataset is supported."
BAG="$(realpath "$BAG_ARG")"
[[ -f "$BAG" ]] || fail "Bag not found: ${BAG}"

BAG_RATE="$(default_bag_rate)"
RVIZ="${RVIZ:-false}"
RVIZ_CONFIG="${RVIZ_CONFIG:-}"
TF_MODE="${TF_MODE:-direct}"
PRIMARY_SOURCE="$(default_primary_source)"
if is_lvisam_fusion_mode && [[ "$PRIMARY_SOURCE" == "fast_livo2" ]]; then
  fail "lvisam_fusion starts LVI-SAM + ORB-SLAM3 only; use PRIMARY_SOURCE=lvisam or PRIMARY_SOURCE=orbslam3."
fi

FAULT_INJECTION="${FAULT_INJECTION:-false}"
EVALUATE_AFTER_RUN="${EVALUATE_AFTER_RUN:-true}"
EVAL_GT="${EVAL_GT:-${ROOT}/data/e2o/ground_truth/ref.csv}"
FAST_SAVE_PCD="${FAST_SAVE_PCD:-false}"
LIDAR_TOPIC="${LIDAR_TOPIC:-/lidar103/velodyne_points}"
IMU_TOPIC="${IMU_TOPIC:-/mavros/imu/data}"
CAMERA_TOPIC="${CAMERA_TOPIC:-/camera/color/image_raw}"
DEPTH_TOPIC="${DEPTH_TOPIC:-/camera/depth/image_rect_raw}"
SENSOR_CONFIG="${SENSOR_CONFIG:-/workspace/wrappers/localization_benchmark/config/e2o.yaml}"
FAST_CONFIG="${FAST_CONFIG:-/workspace/wrappers/fast_livo2_e2o/config/fast_livo2_e2o.yaml}"
ORB_CONFIG="${ORB_CONFIG:-/workspace/wrappers/orbslam3_e2o/config/e2o_front_mono_orbslam3.yaml}"
LVISAM_LIDAR_CONFIG="${LVISAM_LIDAR_CONFIG:-/workspace/wrappers/lvisam_e2o/config/params_lidar_e2o.yaml}"
LVISAM_CAMERA_CONFIG="${LVISAM_CAMERA_CONFIG:-/workspace/wrappers/lvisam_e2o/config/params_camera_e2o.yaml}"
LVISAM_ENABLE_VISUAL="${LVISAM_ENABLE_VISUAL:-false}"
FUSION_CONFIG="$(default_fusion_config)"

RUN_ID="$(date +%Y%m%d_%H%M%S)_${MODE}_$$"
OUT_HOST="${ROOT}/data/output/${RUN_ID}"
OUT_CONTAINER="/data/output/${RUN_ID}"
STACK="e2o_loc_${RUN_ID}"
CONTAINERS=()
COMMON_DOCKER_ARGS=(--network host -e ROS_MASTER_URI=http://localhost:11311 -e ROS_HOSTNAME=localhost \
  -v "${ROOT}/data/output:/data/output" -v "${ROOT}:/workspace:ro")

mkdir -p "$OUT_HOST"
write_metadata
trap cleanup EXIT INT TERM

require_image "$FUSION_IMAGE" "./build.sh fusion"
needs_fast && require_image "$FAST_IMAGE" "./build.sh fast_livo2"
needs_orb && require_image "$ORB_IMAGE" "./build.sh orbslam3"
needs_lvisam && require_image "$LVISAM_IMAGE" "./build.sh lvisam"

start_container "${STACK}_roscore" "$FUSION_IMAGE" roscore
sleep 2
start_input_pipeline
needs_fast && start_fast_livo2
needs_orb && start_orbslam3
needs_lvisam && start_lvisam

if is_mode fusion_navigation; then
  start_fusion_navigation
elif uses_fusion_node; then
  start_fusion
else
  start_health_only
fi
start_rviz

check_started_containers
echo "[run] mode=${MODE} dataset=e2o bag=${BAG} rate=${BAG_RATE} output=${OUT_HOST}"
play_bag
