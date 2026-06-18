#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-rtabmap-urbannav:latest}"
CACHE_FLAG=""

if [[ "${1:-}" == "--no-cache" ]]; then
    CACHE_FLAG="--no-cache"
fi

for path in \
    "${SCRIPT_DIR}/docker/rtabmap/Dockerfile" \
    "${SCRIPT_DIR}/wrappers/rtabmap_urbannav" \
    "${SCRIPT_DIR}/wrappers/localization_benchmark" \
    "${SCRIPT_DIR}/wrappers/custom_localization_msgs" \
    "${SCRIPT_DIR}/wrappers/fast-lio_urbannav"; do
    if [ ! -e "${path}" ]; then
        echo "ERROR: missing required path: ${path}"
        exit 1
    fi
done

chmod +x "${SCRIPT_DIR}"/wrappers/rtabmap_urbannav/scripts/*.py || true
chmod +x "${SCRIPT_DIR}"/wrappers/localization_benchmark/scripts/*.py || true
chmod +x "${SCRIPT_DIR}"/wrappers/fast-lio_urbannav/scripts/*.py || true

mkdir -p "${SCRIPT_DIR}/data/results/rtab_map" "${SCRIPT_DIR}/data/output"

echo "[build] algorithm=RTAB-Map-ICP image=${IMAGE_NAME}"
docker build ${CACHE_FLAG} --network host \
    -t "${IMAGE_NAME}" \
    -f "${SCRIPT_DIR}/docker/rtabmap/Dockerfile" \
    "${SCRIPT_DIR}"

echo "[build] complete algorithm=RTAB-Map"
