#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-fastlivo2-urbannav:latest}"
CACHE_FLAG=""

if [[ "${1:-}" == "--no-cache" ]]; then
    CACHE_FLAG="--no-cache"
fi

for path in \
    "${SCRIPT_DIR}/wrappers/fast_livo2_wrapper" \
    "${SCRIPT_DIR}/wrappers/localization_benchmark" \
    "${SCRIPT_DIR}/wrappers/custom_localization_msgs" \
    "${SCRIPT_DIR}/wrappers/fast-lio_urbannav" \
    "${SCRIPT_DIR}/docker/fastlivo2/Dockerfile"; do
    if [ ! -e "${path}" ]; then
        echo "ERROR: missing required path: ${path}"
        exit 1
    fi
done

chmod +x "${SCRIPT_DIR}"/wrappers/fast_livo2_wrapper/scripts/*.py || true
chmod +x "${SCRIPT_DIR}"/wrappers/localization_benchmark/scripts/*.py || true
chmod +x "${SCRIPT_DIR}"/wrappers/fast-lio_urbannav/scripts/*.py || true

mkdir -p "${SCRIPT_DIR}/data/results/fast_livo2" "${SCRIPT_DIR}/data/output"

echo "[build] algorithm=FAST-LIVO2 image=${IMAGE_NAME}"
docker build ${CACHE_FLAG} --network host \
    -t "${IMAGE_NAME}" \
    -f "${SCRIPT_DIR}/docker/fastlivo2/Dockerfile" \
    "${SCRIPT_DIR}"

echo "[build] complete algorithm=FAST-LIVO2"
