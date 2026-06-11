#!/bin/bash
# ============================================================
# build.sh  —  Build the ORB-SLAM3 UrbanNav Docker image
# ============================================================
# Usage:
#   ./build.sh
#   ./build.sh --no-cache
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="orbslam3-urbannav"
IMAGE_TAG="latest"

echo "═══════════════════════════════════════════════════════"
echo "  Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "  Context: ${SCRIPT_DIR}"
echo "  NOTE: ORB-SLAM3 build takes ~15 min on first run"
echo "═══════════════════════════════════════════════════════"

cd "${SCRIPT_DIR}"

CACHE_FLAG=""
if [[ "${1:-}" == "--no-cache" ]]; then
    CACHE_FLAG="--no-cache"
    echo "  [NOTE] Cache disabled — full rebuild"
fi

docker build \
    ${CACHE_FLAG} \
    --network host \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    -f Dockerfile \
    .

echo ""
echo "✓  Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "Next steps:"
echo "  1. Copy rosbag to ./data/"
echo "  2. Run:  ./run.sh"
