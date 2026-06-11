#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="fastlio2-urbannav:latest"
CONTAINER_NAME="fastlio2_urbannav_run"
MODE=""
PER=""
ALGO="fastlio2"
EVALUATE="false"
EVAL_DURATION="0"
SKIP_RUNTIME_BUILD="false"
DOCKER_CPUS="${DOCKER_CPUS:-4}"
DOCKER_MEMORY="${DOCKER_MEMORY:-10g}"

usage() {
    cat <<'EOF'
Usage:
  ./run.sh --visualise=true     Show rosbag LiDAR, camera, /clock status, and ground truth in RViz.
  ./run.sh --algo fastlio2 --per 0
  ./run.sh --algo rtabmap --per 0
  ./run.sh --algo rtabmap --per 0 --eval
  ./run.sh --algo adaptive_w_lvio --per 0
  ./run.sh --algo adaptive_w_lvio --per 0 --eval
  ./run.sh --algo orbslam3 --per 0
  ./run.sh --algo orbslam3 --per 0 --eval
  ./run.sh --per 1 --eval       Run one bag pass, save plots/report, then close ROS/RViz.
  ./run.sh --algo fastlio2 --per 1 --eval --duration 10
  ./run.sh --per 1 --evaluate   Alias for --eval.
  ./run.sh --per 1 --summary    Alias for --eval.
  ./run.sh --shell              Open a shell in the container.

Algorithms are configured in:
  wrappers/localization_benchmark/config/algorithms.yaml

Safety limits:
  DOCKER_CPUS=4 DOCKER_MEMORY=10g are used by default.
  Override them only if you know your machine has enough headroom.

Use --skip-build after ./build.sh succeeds.

LVI-SAM, FAST-LIVO2 and RTAB-Map also have separate command files:
  ./build_lvisam.sh && ./run_lvisam.sh 0
  ./build_fastlivo2.sh && ./run_fastlivo2.sh --per 0
  ./build_rtabmap.sh && ./run_rtabmap.sh --per 0
  ./build_adap_w.sh && ./run_adap_w.sh --per 0
  ./build_orb.sh && ./run_orb.sh --per 0
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --visualise=true|--visualize=true)
            MODE="visualise"
            shift
            ;;
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
        --algo)
            ALGO="${2:-}"
            shift 2
            ;;
        --algo=*)
            ALGO="${1#*=}"
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
        --skip-build)
            SKIP_RUNTIME_BUILD="true"
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

case "${ALGO}" in
    fastlio2|fast_lio2|fast-lio2|rtabmap|rtab_map|rtab-map|adap_w|adap-w|adaptive_w|adaptive-w|adaptive_w_lvio|adaptive-w-lvio|adaptivewlvio|orb|orbslam3|orb_slam3|orb-slam3)
        ;;
    *)
        echo "ERROR: run.sh --algo supports fastlio2, rtabmap, adaptive_w_lvio, or orbslam3."
        echo "For LVI-SAM, use ./run_lvisam.sh 0. For FAST-LIVO2, use ./run_fastlivo2.sh --per 0."
        exit 2
        ;;
esac

case "${ALGO}" in
    orb|orbslam3|orb_slam3|orb-slam3)
        ORB_ARGS=()
        if [ "${MODE}" = "per" ]; then
            ORB_ARGS=(--per "${PER}")
            if [ "${EVALUATE}" = "true" ]; then
                ORB_ARGS+=(--eval)
            fi
            if [ "${EVAL_DURATION}" != "0" ]; then
                ORB_ARGS+=(--duration "${EVAL_DURATION}")
            fi
        elif [ "${MODE}" = "shell" ]; then
            ORB_ARGS=(--shell)
        else
            echo "ERROR: ORB-SLAM3 supports --per/--eval or --shell via run.sh."
            exit 2
        fi
        exec "${SCRIPT_DIR}/run_orb.sh" "${ORB_ARGS[@]}"
        ;;
esac

if [ -z "${DISPLAY:-}" ] && [ -S /tmp/.X11-unix/X1 ]; then
    export DISPLAY=:1
fi

mkdir -p "${SCRIPT_DIR}/.catkin_cache/build" "${SCRIPT_DIR}/.catkin_cache/devel" "${SCRIPT_DIR}/.catkin_cache/logs"

xhost +local:docker 2>/dev/null || true
docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

TTY_ARGS=()
if [ -t 0 ]; then
    TTY_ARGS=(-it)
fi

case "${MODE}" in
    visualise)
        CMD=(/workspace/scripts/container_visualise.sh)
        ;;
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

echo "Starting ${CONTAINER_NAME} with mode: ${MODE}${PER:+ ${PER}} algo: ${ALGO}"
docker run "${TTY_ARGS[@]}" \
    --name "${CONTAINER_NAME}" \
    --network host \
    --privileged \
    --cpus="${DOCKER_CPUS}" \
    --memory="${DOCKER_MEMORY}" \
    -e DISPLAY="${DISPLAY:-:0}" \
    -e ROS_MASTER_URI=http://localhost:11311 \
    -e ROS_HOSTNAME=localhost \
    -e HOST_UID="$(id -u)" \
    -e HOST_GID="$(id -g)" \
    -e SKIP_RUNTIME_BUILD="${SKIP_RUNTIME_BUILD}" \
    -e BAG_RATE="${BAG_RATE:-0.5}" \
    -e GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG:-0.0}" \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "${SCRIPT_DIR}/data":/data \
    -v "${SCRIPT_DIR}":/workspace \
    -v "${SCRIPT_DIR}/.catkin_cache/build":/root/catkin_ws/build \
    -v "${SCRIPT_DIR}/.catkin_cache/devel":/root/catkin_ws/devel \
    -v "${SCRIPT_DIR}/.catkin_cache/logs":/root/catkin_ws/logs \
    -v "${SCRIPT_DIR}/wrappers/fast-lio_urbannav":/root/catkin_ws/src/fast-lio_urbannav \
    -v "${SCRIPT_DIR}/wrappers/custom_localization_msgs":/root/catkin_ws/src/custom_localization_msgs \
    -v "${SCRIPT_DIR}/wrappers/localization_benchmark":/root/catkin_ws/src/localization_benchmark \
    -v "${SCRIPT_DIR}/wrappers/rtabmap_urbannav":/root/catkin_ws/src/rtabmap_urbannav \
    -v "${SCRIPT_DIR}/wrappers/adaptive_w_lvio_urbannav":/root/catkin_ws/src/adaptive_w_lvio_urbannav \
    "${IMAGE_NAME}" \
    "${CMD[@]}"
