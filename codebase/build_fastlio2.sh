#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="fastlio2-urbannav:latest"
CONTAINER_NAME="fastlio2_build_check"
BAG_PATH="${SCRIPT_DIR}/data/UrbanNav-HK_TST-20210517_sensors.bag"
GT_PATH="${SCRIPT_DIR}/data/UrbanNav_TST_GT_raw.txt"
CACHE_FLAG=""

if [[ "${1:-}" == "--no-cache" ]]; then
    CACHE_FLAG="--no-cache"
fi

command -v docker >/dev/null || {
    echo "ERROR: docker is not installed or not in PATH."
    exit 1
}

if [ ! -f "${BAG_PATH}" ]; then
    echo "ERROR: missing dataset bag: ${BAG_PATH}"
    echo "Put UrbanNav-HK_TST-20210517_sensors.bag in ./data."
    exit 1
fi

if [ ! -f "${GT_PATH}" ]; then
    echo "ERROR: missing ground truth file: ${GT_PATH}"
    echo "Put UrbanNav_TST_GT_raw.txt in ./data."
    exit 1
fi

chmod +x "${SCRIPT_DIR}"/scripts/*.sh
mkdir -p "${SCRIPT_DIR}/.catkin_cache/build" "${SCRIPT_DIR}/.catkin_cache/devel" "${SCRIPT_DIR}/.catkin_cache/logs"

echo "[build] algorithm=FAST-LIO2 image=${IMAGE_NAME}"
cd "${SCRIPT_DIR}"
docker build ${CACHE_FLAG} --network host -t "${IMAGE_NAME}" -f Dockerfile .

echo "[build] running workspace checks"
docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true
docker run --rm \
    --name "${CONTAINER_NAME}" \
    --network host \
    -e ROS_MASTER_URI=http://localhost:11311 \
    -e ROS_HOSTNAME=localhost \
    -v "${SCRIPT_DIR}/data":/data \
    -v "${SCRIPT_DIR}":/workspace \
    -v "${SCRIPT_DIR}/.catkin_cache/build":/root/catkin_ws/build \
    -v "${SCRIPT_DIR}/.catkin_cache/devel":/root/catkin_ws/devel \
    -v "${SCRIPT_DIR}/.catkin_cache/logs":/root/catkin_ws/logs \
    -v "${SCRIPT_DIR}/wrappers/fast-lio_urbannav":/root/catkin_ws/src/fast_lio_urbannav \
    -v "${SCRIPT_DIR}/wrappers/custom_localization_msgs":/root/catkin_ws/src/custom_localization_msgs \
    -v "${SCRIPT_DIR}/wrappers/localization_benchmark":/root/catkin_ws/src/localization_benchmark \
    -v "${SCRIPT_DIR}/wrappers/adaptive_w_lvio_urbannav":/root/catkin_ws/src/adaptive_w_lvio_urbannav \
    "${IMAGE_NAME}" \
    /workspace/scripts/container_build_check.sh

echo "[build] complete algorithm=FAST-LIO2"
