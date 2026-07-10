#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BAG="${1:-}"

if [[ -z "$BAG" || "${BAG}" == "-h" || "${BAG}" == "--help" ]]; then
  cat >&2 <<'USAGE'
Usage:
  ./Floam/run.sh /path/to/e2o.bag

Environment:
  BAG_RATE=0.5
  RVIZ=true
  RVIZ_IMAGE=e2o-localization-runtime:latest
  RVIZ_CONFIG=/workspace/Floam/rviz/e2o_floam.rviz
  LIDAR_TOPIC=/lidar103/velodyne_points
  LIDAR_FRAME=velodyne
  LIDAR_YAW=0.174533
  MAP_FILE=/workspace/maps/full_campus.pcd
  RELOCALIZATION=true
  AUTO_INITIALPOSE=false
  WAIT_FOR_INITIALPOSE=true
  INITIAL_Z_SEARCH_MIN=0.0 INITIAL_Z_SEARCH_MAX=15.0 INITIAL_Z_OFFSET=1.5 INITIAL_Z_FALLBACK=0.0
  INITIAL_X=0.0 INITIAL_Y=0.0 INITIAL_Z=0.0 INITIAL_ROLL=0.0 INITIAL_PITCH=0.0 INITIAL_YAW=0.0
USAGE
  exit 2
fi

BAG="$(realpath "$BAG")"
[[ -f "$BAG" ]] || {
  echo "Bag not found: $BAG" >&2
  exit 2
}

docker image inspect floam-e2o:latest >/dev/null 2>&1 || {
  echo "Missing floam-e2o:latest; run ./Floam/build.sh" >&2
  exit 1
}

BAG_RATE="${BAG_RATE:-0.5}"
RVIZ="${RVIZ:-false}"
RVIZ_IMAGE="${RVIZ_IMAGE:-e2o-localization-runtime:latest}"
RVIZ_CONFIG="${RVIZ_CONFIG:-/workspace/Floam/rviz/e2o_floam.rviz}"
LIDAR_TOPIC="${LIDAR_TOPIC:-/lidar103/velodyne_points}"
LIDAR_FRAME="${LIDAR_FRAME:-velodyne}"
LIDAR_X="${LIDAR_X:-0.0}"
LIDAR_Y="${LIDAR_Y:-0.0}"
LIDAR_Z="${LIDAR_Z:-0.0}"
LIDAR_YAW="${LIDAR_YAW:-0.174533}"
LIDAR_PITCH="${LIDAR_PITCH:-0.0}"
LIDAR_ROLL="${LIDAR_ROLL:-0.0}"
MAP_FILE="${MAP_FILE:-/workspace/maps/full_campus.pcd}"
RELOCALIZATION="${RELOCALIZATION:-true}"
AUTO_INITIALPOSE="${AUTO_INITIALPOSE:-false}"
WAIT_FOR_INITIALPOSE="${WAIT_FOR_INITIALPOSE:-auto}"
INITIALPOSE_TIMEOUT_SEC="${INITIALPOSE_TIMEOUT_SEC:-0}"
INITIAL_X="${INITIAL_X:-0.0}"
INITIAL_Y="${INITIAL_Y:-0.0}"
INITIAL_Z="${INITIAL_Z:-0.0}"
INITIAL_ROLL="${INITIAL_ROLL:-0.0}"
INITIAL_PITCH="${INITIAL_PITCH:-0.0}"
INITIAL_YAW="${INITIAL_YAW:-0.0}"
INITIAL_Z_SEARCH_MIN="${INITIAL_Z_SEARCH_MIN:-0.0}"
INITIAL_Z_SEARCH_MAX="${INITIAL_Z_SEARCH_MAX:-15.0}"
INITIAL_Z_OFFSET="${INITIAL_Z_OFFSET:-1.5}"
INITIAL_Z_FALLBACK="${INITIAL_Z_FALLBACK:-0.0}"

RUN_ID="$(date +%Y%m%d_%H%M%S)_floam_$$"
OUT_HOST="${ROOT}/Floam/output/${RUN_ID}"
OUT_CONTAINER="/data/output/${RUN_ID}"
STACK="floam_${RUN_ID}"
mkdir -p "$OUT_HOST"

COMMON_ARGS=(
  --network host
  -e ROS_MASTER_URI=http://localhost:11311
  -e ROS_HOSTNAME=localhost
  -v "${ROOT}:/workspace:ro"
  -v "${ROOT}/Floam/output:/data/output"
)

CONTAINERS=()
cleanup() {
  local code=$?
  trap - EXIT INT TERM
  for ((idx=${#CONTAINERS[@]}-1; idx>=0; idx--)); do
    local name="${CONTAINERS[$idx]}"
    if docker inspect "$name" >/dev/null 2>&1; then
      docker logs "$name" >"${OUT_HOST}/${name}.log" 2>&1 || true
    fi
    docker rm -f "$name" >/dev/null 2>&1 || true
  done
  echo "[floam] output=${OUT_HOST}"
  exit "$code"
}
trap cleanup EXIT INT TERM

start_rviz() {
  [[ "$RVIZ" == "true" ]] || return 0
  docker image inspect "$RVIZ_IMAGE" >/dev/null 2>&1 || {
    echo "Missing ${RVIZ_IMAGE}; build e2o runtime or set RVIZ_IMAGE to an image containing rviz." >&2
    exit 1
  }
  xhost +local:docker >/dev/null 2>&1 || true
  docker run -d --name "${STACK}_rviz" "${COMMON_ARGS[@]}" \
    -e DISPLAY="${DISPLAY:-:0}" \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    "$RVIZ_IMAGE" rviz -d "$RVIZ_CONFIG" >/dev/null
  CONTAINERS+=("${STACK}_rviz")
}

is_true() {
  [[ "${1,,}" == "true" || "${1}" == "1" || "${1,,}" == "yes" ]]
}

should_wait_for_initialpose() {
  if [[ "${WAIT_FOR_INITIALPOSE,,}" != "auto" ]]; then
    is_true "$WAIT_FOR_INITIALPOSE"
    return
  fi
  is_true "$RELOCALIZATION" && ! is_true "$AUTO_INITIALPOSE"
}

wait_for_initialpose() {
  should_wait_for_initialpose || return 0
  echo "[floam] waiting for /initialpose before bag playback"
  echo "[floam] in RViz, use '2D Pose Estimate' on the full-campus map to set the car pose"
  local wait_cmd='source /opt/ros/noetic/setup.bash; source /root/catkin_ws/devel/setup.bash; rostopic echo -n 1 /initialpose >/dev/null'
  if [[ "$INITIALPOSE_TIMEOUT_SEC" != "0" ]]; then
    docker run --rm "${COMMON_ARGS[@]}" floam-e2o:latest \
      bash -lc "timeout ${INITIALPOSE_TIMEOUT_SEC}s bash -lc '$wait_cmd'"
  else
    docker run --rm "${COMMON_ARGS[@]}" floam-e2o:latest \
      bash -lc "$wait_cmd"
  fi
  echo "[floam] received /initialpose; starting bag playback"
}

docker run -d --name "${STACK}_roscore" "${COMMON_ARGS[@]}" floam-e2o:latest roscore >/dev/null
CONTAINERS+=("${STACK}_roscore")
sleep 2

docker run -d --name "${STACK}_algo" "${COMMON_ARGS[@]}" floam-e2o:latest \
  roslaunch floam_e2o algorithm.launch \
    lidar_topic:="${LIDAR_TOPIC}" \
    lidar_frame:="${LIDAR_FRAME}" \
    lidar_x:="${LIDAR_X}" \
    lidar_y:="${LIDAR_Y}" \
    lidar_z:="${LIDAR_Z}" \
    lidar_yaw:="${LIDAR_YAW}" \
    lidar_pitch:="${LIDAR_PITCH}" \
    lidar_roll:="${LIDAR_ROLL}" \
    map_file:="${MAP_FILE}" \
    pose_topic:="/pose" \
    output_dir:="${OUT_CONTAINER}" \
    node_start_delay:="5.0" \
    relocalization:="${RELOCALIZATION}" \
    auto_initialpose:="${AUTO_INITIALPOSE}" \
    initial_z_search_min:="${INITIAL_Z_SEARCH_MIN}" \
    initial_z_search_max:="${INITIAL_Z_SEARCH_MAX}" \
    initial_z_offset:="${INITIAL_Z_OFFSET}" \
    initial_z_fallback:="${INITIAL_Z_FALLBACK}" \
    initial_x:="${INITIAL_X}" \
    initial_y:="${INITIAL_Y}" \
    initial_z:="${INITIAL_Z}" \
    initial_roll:="${INITIAL_ROLL}" \
    initial_pitch:="${INITIAL_PITCH}" \
    initial_yaw:="${INITIAL_YAW}" >/dev/null
CONTAINERS+=("${STACK}_algo")

start_rviz

sleep 8
for name in "${CONTAINERS[@]}"; do
  if [[ "$(docker inspect -f '{{.State.Running}}' "$name" 2>/dev/null || echo false)" != "true" ]]; then
    echo "Container failed before bag playback: ${name}" >&2
    docker logs "$name" >&2 || true
    exit 1
  fi
done

cat > "${OUT_HOST}/run_metadata.env" <<EOF
RUN_ID=${RUN_ID}
BAG=${BAG}
BAG_RATE=${BAG_RATE}
LIDAR_TOPIC=${LIDAR_TOPIC}
LIDAR_FRAME=${LIDAR_FRAME}
LIDAR_X=${LIDAR_X}
LIDAR_Y=${LIDAR_Y}
LIDAR_Z=${LIDAR_Z}
LIDAR_YAW=${LIDAR_YAW}
LIDAR_PITCH=${LIDAR_PITCH}
LIDAR_ROLL=${LIDAR_ROLL}
MAP_FILE=${MAP_FILE}
RELOCALIZATION=${RELOCALIZATION}
AUTO_INITIALPOSE=${AUTO_INITIALPOSE}
WAIT_FOR_INITIALPOSE=${WAIT_FOR_INITIALPOSE}
INITIALPOSE_TIMEOUT_SEC=${INITIALPOSE_TIMEOUT_SEC}
INITIAL_X=${INITIAL_X}
INITIAL_Y=${INITIAL_Y}
INITIAL_Z=${INITIAL_Z}
INITIAL_ROLL=${INITIAL_ROLL}
INITIAL_PITCH=${INITIAL_PITCH}
INITIAL_YAW=${INITIAL_YAW}
INITIAL_Z_SEARCH_MIN=${INITIAL_Z_SEARCH_MIN}
INITIAL_Z_SEARCH_MAX=${INITIAL_Z_SEARCH_MAX}
INITIAL_Z_OFFSET=${INITIAL_Z_OFFSET}
INITIAL_Z_FALLBACK=${INITIAL_Z_FALLBACK}
RVIZ=${RVIZ}
RVIZ_IMAGE=${RVIZ_IMAGE}
RVIZ_CONFIG=${RVIZ_CONFIG}
EOF

wait_for_initialpose

echo "[floam] playing ${BAG} at rate=${BAG_RATE}"
docker run --rm --network host \
  -e ROS_MASTER_URI=http://localhost:11311 \
  -e ROS_HOSTNAME=localhost \
  -v "$(dirname "$BAG"):/bags:ro" \
  floam-e2o:latest \
  rosbag play --quiet --clock --rate "${BAG_RATE}" "/bags/$(basename "$BAG")" --topics "${LIDAR_TOPIC}"

sleep 3
