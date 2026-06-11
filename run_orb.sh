#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-orbslam3-urbannav:latest}"
CONTAINER_NAME_ENV="${CONTAINER_NAME:-}"
MODE=""
PER=""
EVALUATE="false"
EVAL_DURATION="0"
SKIP_RUNTIME_BUILD="${SKIP_RUNTIME_BUILD:-true}"
DOCKER_CPUS="${DOCKER_CPUS:-}"
DOCKER_MEMORY="${DOCKER_MEMORY:-}"
BAG_RATE="${BAG_RATE:-0.35}"
GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG:-0.0}"
ORB_MODE="${ORB_MODE:-stereo}"
ALGO="orbslam3"

usage() {
    cat <<'USAGE'
Usage:
  ./run_orb.sh --per 0
  ./run_orb.sh --per 0 --eval
  ./run_orb.sh --per 1 --eval --duration 20
  ./run_orb.sh 0 --eval                 # positional shorthand
  ./run_orb.sh --shell

Environment overrides:
  ORB_MODE=stereo              Default. Metric scale from ZED2 stereo pair.
  ORB_MODE=mono                Right-camera monocular mode. Scale may drift.
  BAG_RATE=0.35                Rosbag playback speed
  GT_YAW_OFFSET_DEG=0.0         GT yaw offset used by RViz/eval
  SKIP_RUNTIME_BUILD=true       Use ORB-SLAM3 already built into image
  DOCKER_CPUS=8 DOCKER_MEMORY=16g Optional resource limits
USAGE
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --per)
            MODE="per"
            PER="${2:-}"
            shift 2
            ;;
        --per=*)
            MODE="per"
            PER="${1#*=}"
            shift
            ;;
        --summary|--eval|--evaluate)
            EVALUATE="true"
            shift
            ;;
        --duration|--seconds)
            EVAL_DURATION="${2:-}"
            shift 2
            ;;
        --duration=*|--seconds=*)
            EVAL_DURATION="${1#*=}"
            shift
            ;;
        --mode)
            ORB_MODE="${2:-}"
            shift 2
            ;;
        --mode=*)
            ORB_MODE="${1#*=}"
            shift
            ;;
        --skip-build)
            SKIP_RUNTIME_BUILD="true"
            shift
            ;;
        --runtime-build)
            SKIP_RUNTIME_BUILD="false"
            shift
            ;;
        --shell)
            MODE="shell"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        [0-6])
            MODE="per"
            PER="$1"
            shift
            ;;
        *)
            echo "ERROR: unknown argument: $1"
            usage
            exit 2
            ;;
    esac
done

if [ -z "${MODE}" ]; then
    usage
    exit 2
fi
if [ "${MODE}" = "per" ] && ! [[ "${PER}" =~ ^[0-6]$ ]]; then
    echo "ERROR: --per must be a number from 0 to 6"
    exit 2
fi
if ! [[ "${EVAL_DURATION}" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    echo "ERROR: --duration must be a positive number of seconds, or 0 for full bag"
    exit 2
fi
if [ "${ORB_MODE}" != "stereo" ] && [ "${ORB_MODE}" != "mono" ]; then
    echo "ERROR: ORB_MODE / --mode must be stereo or mono"
    exit 2
fi

if [ -n "${CONTAINER_NAME_ENV}" ]; then
    CONTAINER_NAME="${CONTAINER_NAME_ENV}"
elif [ "${MODE}" = "per" ]; then
    CONTAINER_NAME="orbslam3_run_${PER}"
else
    CONTAINER_NAME="orbslam3_run"
fi

if [ -z "${DISPLAY:-}" ] && [ -S /tmp/.X11-unix/X1 ]; then
    export DISPLAY=:1
fi

mkdir -p "${SCRIPT_DIR}/data/results/orb_slam3" "${SCRIPT_DIR}/data/output"
chmod +x "${SCRIPT_DIR}"/wrappers/orbslam3_urbannav/scripts/*.py "${SCRIPT_DIR}"/wrappers/orbslam3_urbannav/scripts/*.sh || true
chmod +x "${SCRIPT_DIR}"/wrappers/localization_benchmark/scripts/*.py || true
chmod +x "${SCRIPT_DIR}"/wrappers/fast-lio_urbannav/scripts/*.py || true

xhost +local:docker 2>/dev/null || true
docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

TTY_ARGS=()
if [ -t 0 ]; then
    TTY_ARGS=(-it)
fi

case "${MODE}" in
    per)
        if [ "${EVALUATE}" = "true" ]; then
            CMD=(/workspace/scripts/container_run_summary.sh "${PER}" "${EVAL_DURATION}" "${ALGO}")
        else
            CMD=(/workspace/scripts/container_run_per.sh "${PER}" --attach "${ALGO}")
        fi
        ;;
    shell)
        CMD=(bash)
        ;;
esac

RESOURCE_ARGS=()
if [ -n "${DOCKER_CPUS}" ]; then
    RESOURCE_ARGS+=(--cpus="${DOCKER_CPUS}")
fi
if [ -n "${DOCKER_MEMORY}" ]; then
    RESOURCE_ARGS+=(--memory="${DOCKER_MEMORY}")
fi

echo "Starting ${CONTAINER_NAME} mode=${MODE}${PER:+ per_${PER}} algo=ORB-SLAM3 eval=${EVALUATE} ORB_MODE=${ORB_MODE}"
echo "BAG_RATE=${BAG_RATE} GT_YAW_OFFSET_DEG=${GT_YAW_OFFSET_DEG} SKIP_RUNTIME_BUILD=${SKIP_RUNTIME_BUILD}"

docker run "${TTY_ARGS[@]}" \
    --name "${CONTAINER_NAME}" \
    --network host \
    --privileged \
    "${RESOURCE_ARGS[@]}" \
    -e DISPLAY="${DISPLAY:-:0}" \
    -e ROS_MASTER_URI=http://localhost:11311 \
    -e ROS_HOSTNAME=localhost \
    -e HOST_UID="$(id -u)" \
    -e HOST_GID="$(id -g)" \
    -e SKIP_RUNTIME_BUILD="${SKIP_RUNTIME_BUILD}" \
    -e BAG_RATE="${BAG_RATE}" \
    -e GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG}" \
    -e ORB_MODE="${ORB_MODE}" \
    -e ORB_SLAM3_ROOT="/root/ORB_SLAM3" \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "${SCRIPT_DIR}/data":/data \
    -v "${SCRIPT_DIR}":/workspace \
    -v "${SCRIPT_DIR}/wrappers/orbslam3_urbannav":/root/catkin_ws/src/orbslam3_urbannav \
    -v "${SCRIPT_DIR}/wrappers/custom_localization_msgs":/root/catkin_ws/src/custom_localization_msgs \
    -v "${SCRIPT_DIR}/wrappers/localization_benchmark":/root/catkin_ws/src/localization_benchmark \
    -v "${SCRIPT_DIR}/wrappers/fast-lio_urbannav":/root/catkin_ws/src/fast_lio_urbannav \
    "${IMAGE_NAME}" \
    "${CMD[@]}"
