#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-orbslam3-urbannav:latest}"
CACHE_FLAG=""

if [[ "${1:-}" == "--no-cache" ]]; then
    CACHE_FLAG="--no-cache"
fi

for path in \
    "${SCRIPT_DIR}/docker/orbslam3/Dockerfile" \
    "${SCRIPT_DIR}/docker/orbslam3/patches/add_orbslam3_pose_publishers.py" \
    "${SCRIPT_DIR}/wrappers/orbslam3_urbannav" \
    "${SCRIPT_DIR}/wrappers/localization_benchmark" \
    "${SCRIPT_DIR}/wrappers/custom_localization_msgs" \
    "${SCRIPT_DIR}/wrappers/fast-lio_urbannav"; do
    if [ ! -e "${path}" ]; then
        echo "ERROR: missing required path: ${path}"
        exit 1
    fi
done

chmod +x "${SCRIPT_DIR}"/wrappers/orbslam3_urbannav/scripts/*.py "${SCRIPT_DIR}"/wrappers/orbslam3_urbannav/scripts/*.sh || true
chmod +x "${SCRIPT_DIR}"/wrappers/localization_benchmark/scripts/*.py || true
chmod +x "${SCRIPT_DIR}"/wrappers/fast-lio_urbannav/scripts/*.py || true

mkdir -p "${SCRIPT_DIR}/data/results/orb_slam3" "${SCRIPT_DIR}/data/output"

echo "[build] algorithm=ORB-SLAM3 image=${IMAGE_NAME}"
echo "NOTE: first ORB-SLAM3 build is heavy because Pangolin + ORB-SLAM3 are compiled."
docker build ${CACHE_FLAG} --network host \
    -t "${IMAGE_NAME}" \
    -f "${SCRIPT_DIR}/docker/orbslam3/Dockerfile" \
    "${SCRIPT_DIR}"

echo "[build] complete algorithm=ORB-SLAM3"
