#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-lvisam-urbannav:latest}"
CACHE_FLAG=""

if [[ "${1:-}" == "--no-cache" ]]; then
    CACHE_FLAG="--no-cache"
fi

for path in \
    "${SCRIPT_DIR}/algorithms/lvi_sam" \
    "${SCRIPT_DIR}/wrappers/localization_benchmark" \
    "${SCRIPT_DIR}/wrappers/custom_localization_msgs" \
    "${SCRIPT_DIR}/wrappers/fast-lio_urbannav" \
    "${SCRIPT_DIR}/wrappers/lvi_sam_urbannav"; do
    if [ ! -d "${path}" ]; then
        echo "ERROR: missing required source directory: ${path}"
        exit 1
    fi
done

echo "Building ${IMAGE_NAME}..."
docker build ${CACHE_FLAG} --network host \
    -t "${IMAGE_NAME}" \
    -f "${SCRIPT_DIR}/docker/lvisam/Dockerfile" \
    "${SCRIPT_DIR}"

echo "LVI-SAM build complete."
echo "Run: ./run_lvisam.sh 0"
