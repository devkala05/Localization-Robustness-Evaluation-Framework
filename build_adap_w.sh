#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-adap-w-lvio-urbannav:latest}"
CACHE_FLAG=""

if [[ "${1:-}" == "--no-cache" ]]; then
    CACHE_FLAG="--no-cache"
fi

for path in \
    "${SCRIPT_DIR}/docker/adap_w/Dockerfile" \
    "${SCRIPT_DIR}/wrappers/adaptive_w_lvio_urbannav" \
    "${SCRIPT_DIR}/wrappers/localization_benchmark" \
    "${SCRIPT_DIR}/wrappers/custom_localization_msgs" \
    "${SCRIPT_DIR}/wrappers/fast-lio_urbannav"; do
    if [ ! -e "${path}" ]; then
        echo "ERROR: missing required path: ${path}"
        exit 1
    fi
done

chmod +x "${SCRIPT_DIR}"/wrappers/adaptive_w_lvio_urbannav/scripts/*.py || true
chmod +x "${SCRIPT_DIR}"/wrappers/localization_benchmark/scripts/*.py || true
chmod +x "${SCRIPT_DIR}"/wrappers/fast-lio_urbannav/scripts/*.py || true

mkdir -p "${SCRIPT_DIR}/data/results/adaptive_w_lvio" "${SCRIPT_DIR}/data/output"

echo "Building ${IMAGE_NAME}..."
docker build ${CACHE_FLAG} --network host \
    -t "${IMAGE_NAME}" \
    -f "${SCRIPT_DIR}/docker/adap_w/Dockerfile" \
    "${SCRIPT_DIR}"

echo "Adaptive-W LVIO build complete."
echo "Run examples:"
echo "  ./run_adap_w.sh --per 0"
echo "  ./run_adap_w.sh --per 0 --eval"
