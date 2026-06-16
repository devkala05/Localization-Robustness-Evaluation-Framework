#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="${COMPARE_RVIZ_IMAGE:-fastlio2-urbannav:latest}"
CONTAINER_NAME="${COMPARE_RVIZ_CONTAINER:-compare_rviz}"
ROS_PORT="${ROS_PORT:-11331}"
DOCKER_CPUS="${DOCKER_CPUS:-4}"
DOCKER_MEMORY="${DOCKER_MEMORY:-8g}"
NO_DOCKER="false"
LIST_ONLY="false"
DATASET="${DATASET:-}"
EXPLICIT_RESULTS_ROOT="false"
EXPLICIT_GT="false"
EXPLICIT_YAW="false"
ARGS=()

usage() {
  cat <<'EOF'
Usage:
  ./compare_rviz --algo rtabmap
  ./compare_rviz --algo rtabmap --per 0
  ./compare_rviz --algo rtabmap --per 0 --gps on
  ./compare_rviz --algo all --per 0

Options:
  --algo all|name,list      Algorithm filter. Default all.
  --per N|A-B|list|all      Perturbation filter. Omit for all available.
  --gps all|on|off|unknown  GPS filter. Default all.
  --all-runs                Show every timestamped rerun, not only latest per algo/per/GPS.
  --list                    Print matching runs and exit.
  --results-root PATH       Default data/results.
  --gt PATH                 Default data/UrbanNav_TST_GT_raw.txt.
  --dataset urbannav|e2o    Set default results root, GT, and yaw offset.
  --no-docker               Run on host. Requires ROS Noetic and RViz.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-docker|--host)
      NO_DOCKER="true"; shift ;;
    --list)
      LIST_ONLY="true"; ARGS+=("$1"); shift ;;
    --dataset)
      DATASET="${2:-}"; shift 2 ;;
    --dataset=*)
      DATASET="${1#*=}"; shift ;;
    --results-root|--results-root=*)
      EXPLICIT_RESULTS_ROOT="true"; ARGS+=("$1"); if [ "$1" = "--results-root" ]; then ARGS+=("${2:-}"); shift 2; else shift; fi ;;
    --gt|--gt=*)
      EXPLICIT_GT="true"; ARGS+=("$1"); if [ "$1" = "--gt" ]; then ARGS+=("${2:-}"); shift 2; else shift; fi ;;
    --yaw-offset-deg|--yaw-offset-deg=*)
      EXPLICIT_YAW="true"; ARGS+=("$1"); if [ "$1" = "--yaw-offset-deg" ]; then ARGS+=("${2:-}"); shift 2; else shift; fi ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      ARGS+=("$1"); shift ;;
  esac
done

if [ -n "${DATASET}" ]; then
  eval "$(python3 "${SCRIPT_DIR}/scripts/dataset_config.py" --dataset "${DATASET}" --config-dir "${SCRIPT_DIR}/wrappers/localization_benchmark/config/datasets")"
  if [ "${EXPLICIT_RESULTS_ROOT}" = "false" ]; then
    ARGS+=(--results-root "${DATASET_RESULTS_ROOT}")
  fi
  if [ "${EXPLICIT_GT}" = "false" ]; then
    ARGS+=(--gt "${DATASET_GT_PATH}")
  fi
  if [ "${EXPLICIT_YAW}" = "false" ]; then
    ARGS+=(--yaw-offset-deg "${DATASET_GT_YAW_OFFSET_DEG:-0.0}")
  fi
  export GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG:-${DATASET_GT_YAW_OFFSET_DEG:-0.0}}"
fi

DOCKER_ARGS=()
i=0
while [ "${i}" -lt "${#ARGS[@]}" ]; do
  a="${ARGS[$i]}"
  case "$a" in
    --results-root)
      next="${ARGS[$((i+1))]:-}"
      if [[ "$next" == data/* ]]; then next="/data/${next#data/}"; fi
      DOCKER_ARGS+=("$a" "$next")
      i=$((i+2)) ;;
    --results-root=*)
      val="${a#*=}"
      if [[ "$val" == data/* ]]; then val="/data/${val#data/}"; fi
      DOCKER_ARGS+=("--results-root=${val}")
      i=$((i+1)) ;;
    --gt)
      next="${ARGS[$((i+1))]:-}"
      if [[ "$next" == data/* ]]; then next="/data/${next#data/}"; fi
      DOCKER_ARGS+=("$a" "$next")
      i=$((i+2)) ;;
    --gt=*)
      val="${a#*=}"
      if [[ "$val" == data/* ]]; then val="/data/${val#data/}"; fi
      DOCKER_ARGS+=("--gt=${val}")
      i=$((i+1)) ;;
    *)
      DOCKER_ARGS+=("$a")
      i=$((i+1)) ;;
  esac
done

if [ "${LIST_ONLY}" = "true" ]; then
  if [ "${NO_DOCKER}" = "true" ]; then
    exec python3 "${SCRIPT_DIR}/wrappers/localization_benchmark/scripts/compare_rviz_paths.py" "${ARGS[@]}"
  fi
  command -v docker >/dev/null || { echo "ERROR: docker not found. Use --no-docker if ROS Python deps are available on host."; exit 1; }
  exec docker run --rm \
    -v "${SCRIPT_DIR}/data":/data \
    -v "${SCRIPT_DIR}":/workspace \
    "${IMAGE_NAME}" \
    python3 /workspace/wrappers/localization_benchmark/scripts/compare_rviz_paths.py "${DOCKER_ARGS[@]}"
fi

if [ "${NO_DOCKER}" = "true" ]; then
  export ROS_MASTER_URI="${ROS_MASTER_URI:-http://localhost:${ROS_PORT}}"
  export ROS_HOSTNAME="${ROS_HOSTNAME:-localhost}"
  roscore -p "${ROS_PORT}" >/tmp/compare_rviz_roscore.log 2>&1 &
  ROSCORE_PID=$!
  trap 'kill ${ROSCORE_PID} 2>/dev/null || true; pkill -TERM -f compare_rviz_paths.py >/dev/null 2>&1 || true' EXIT INT TERM
  sleep 2
  python3 "${SCRIPT_DIR}/wrappers/localization_benchmark/scripts/compare_rviz_paths.py" "${ARGS[@]}" &
  sleep 2
  exec rviz -d "${SCRIPT_DIR}/wrappers/localization_benchmark/config/compare_rviz.rviz"
fi

command -v docker >/dev/null || { echo "ERROR: docker not found. Use --no-docker if ROS/RViz is installed on host."; exit 1; }
if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  echo "ERROR: Docker image ${IMAGE_NAME} not found. Build once first:"
  echo "  ./build_fastlio2.sh"
  exit 1
fi

if [ -z "${DISPLAY:-}" ] && [ -S /tmp/.X11-unix/X1 ]; then
  export DISPLAY=:1
fi
xhost +local:docker >/dev/null 2>&1 || true
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

TTY_ARGS=()
if [ -t 0 ]; then TTY_ARGS=(-it); fi

exec docker run "${TTY_ARGS[@]}" --rm \
  --name "${CONTAINER_NAME}" \
  --network host \
  --privileged \
  --cpus="${DOCKER_CPUS}" \
  --memory="${DOCKER_MEMORY}" \
  -e DISPLAY="${DISPLAY:-:0}" \
  -e ROS_MASTER_URI="http://localhost:${ROS_PORT}" \
  -e ROS_HOSTNAME=localhost \
  -e GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG:-0.0}" \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v "${SCRIPT_DIR}/data":/data \
  -v "${SCRIPT_DIR}":/workspace \
  "${IMAGE_NAME}" \
  bash -lc "source /opt/ros/noetic/setup.bash; roscore -p ${ROS_PORT} >/tmp/compare_rviz_roscore.log 2>&1 & sleep 2; python3 /workspace/wrappers/localization_benchmark/scripts/compare_rviz_paths.py ${DOCKER_ARGS[*]@Q} & sleep 2; exec rviz -d /workspace/wrappers/localization_benchmark/config/compare_rviz.rviz"
