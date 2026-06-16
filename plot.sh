#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${PLOT_IMAGE:-fastlio2-urbannav:latest}"
CONTAINER_NAME="offline_trajectory_rviz"
DOCKER_CPUS="${DOCKER_CPUS:-4}"
DOCKER_MEMORY="${DOCKER_MEMORY:-8g}"

usage() {
  cat <<'EOF'
Usage:
  ./plot.sh --per 0 --algo all
  ./plot.sh --per 0 --algo fast_lio2,lvisam,r3live

Default behavior opens RViz and publishes saved CSV trajectories:
  data/results/<algo>/per_<N>/trajectory.csv

Options:
  --dataset NAME          urbannav or e2o. E2O defaults to data/results/e2o and data/odometry.csv.
  --per N                 Required. Perturbation/run id.
  --algo all|name,list    Required-ish. Default all.
  --results-root PATH     Default data/results on host, /data/results in Docker.
  --gt PATH               Default data/UrbanNav_TST_GT_raw.txt on host, /data/... in Docker.
  --static                Old matplotlib backend: save PNGs instead of RViz.
  --no-docker             Run ROS/RViz on host instead of Docker. Requires sourced ROS Noetic.

Env:
  PLOT_IMAGE=fastlio2-urbannav:latest
  ROS_PORT=11321
EOF
}

STATIC="false"
NO_DOCKER="false"
DATASET="${DATASET:-}"
ARGS=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dataset)
      DATASET="${2:-}"; shift 2;;
    --dataset=*)
      DATASET="${1#*=}"; shift;;
    --static|--matplotlib|--png)
      STATIC="true"; shift;;
    --no-docker|--host)
      NO_DOCKER="true"; shift;;
    -h|--help)
      usage; exit 0;;
    *)
      ARGS+=("$1"); shift;;
  esac
done

HAS_GT="false"
HAS_RESULTS_ROOT="false"
for a in "${ARGS[@]}"; do
  case "$a" in
    --gt|--gt=*) HAS_GT="true";;
    --results-root|--results-root=*) HAS_RESULTS_ROOT="true";;
  esac
done

case "$(printf '%s' "${DATASET}" | tr '[:upper:]' '[:lower:]')" in
  e2o|e20|e2o/urban|e20/urban|one_full_loop|e2o_one_full_loop)
    if [ "${HAS_RESULTS_ROOT}" = "false" ]; then
      ARGS+=(--results-root data/results/e2o)
    fi
    if [ "${HAS_GT}" = "false" ]; then
      ARGS+=(--gt data/odometry.csv)
    fi
    ;;
esac

if [ "${STATIC}" = "true" ]; then
  exec python3 "${SCRIPT_DIR}/wrappers/localization_benchmark/scripts/trajectory_analysis.py" plot3d "${ARGS[@]}" --no-show
fi

# Translate common host-relative paths into Docker paths unless user explicitly set absolute paths.
DOCKER_ARGS=()
i=0
while [ $i -lt ${#ARGS[@]} ]; do
  a="${ARGS[$i]}"
  case "$a" in
    --results-root)
      next="${ARGS[$((i+1))]:-}"
      if [[ "$next" == data/* ]]; then next="/data/${next#data/}"; fi
      DOCKER_ARGS+=("$a" "$next")
      i=$((i+2))
      ;;
    --results-root=*)
      val="${a#*=}"
      if [[ "$val" == data/* ]]; then val="/data/${val#data/}"; fi
      DOCKER_ARGS+=("--results-root=${val}")
      i=$((i+1))
      ;;
    --gt)
      next="${ARGS[$((i+1))]:-}"
      if [[ "$next" == data/* ]]; then next="/data/${next#data/}"; fi
      DOCKER_ARGS+=("$a" "$next")
      i=$((i+2))
      ;;
    --gt=*)
      val="${a#*=}"
      if [[ "$val" == data/* ]]; then val="/data/${val#data/}"; fi
      DOCKER_ARGS+=("--gt=${val}")
      i=$((i+1))
      ;;
    *)
      DOCKER_ARGS+=("$a")
      i=$((i+1))
      ;;
  esac
done

if [ "${NO_DOCKER}" = "true" ]; then
  export ROS_MASTER_URI="${ROS_MASTER_URI:-http://localhost:${ROS_PORT:-11321}}"
  export ROS_HOSTNAME="${ROS_HOSTNAME:-localhost}"
  roscore -p "${ROS_PORT:-11321}" >/tmp/offline_plot_roscore.log 2>&1 &
  ROSCORE_PID=$!
  trap 'kill ${ROSCORE_PID} 2>/dev/null || true; pkill -TERM -f offline_rviz_paths.py >/dev/null 2>&1 || true' EXIT INT TERM
  sleep 2
  python3 "${SCRIPT_DIR}/wrappers/localization_benchmark/scripts/offline_rviz_paths.py" "${ARGS[@]}" &
  sleep 2
  exec rviz -d "${SCRIPT_DIR}/wrappers/localization_benchmark/config/offline_trajectory_compare.rviz"
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
  -e ROS_PORT="${ROS_PORT:-11321}" \
  -e GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG:-0.0}" \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v "${SCRIPT_DIR}/data":/data \
  -v "${SCRIPT_DIR}":/workspace \
  -v "${SCRIPT_DIR}/.catkin_cache/build":/root/catkin_ws/build \
  -v "${SCRIPT_DIR}/.catkin_cache/devel":/root/catkin_ws/devel \
  -v "${SCRIPT_DIR}/.catkin_cache/logs":/root/catkin_ws/logs \
  -v "${SCRIPT_DIR}/wrappers/fast-lio_urbannav":/root/catkin_ws/src/fast_lio_urbannav \
  -v "${SCRIPT_DIR}/wrappers/custom_localization_msgs":/root/catkin_ws/src/custom_localization_msgs \
  -v "${SCRIPT_DIR}/wrappers/localization_benchmark":/root/catkin_ws/src/localization_benchmark \
  "${IMAGE_NAME}" \
  /workspace/scripts/container_plot_rviz.sh "${DOCKER_ARGS[@]}"
