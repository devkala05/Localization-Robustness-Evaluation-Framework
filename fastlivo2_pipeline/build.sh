#!/bin/bash
# ============================================================
# build.sh  —  Build the FAST-LIVO2 wrapper Docker image
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="fastlivo2-wrapper:latest"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Building: ${IMAGE_NAME}"
echo "╚══════════════════════════════════════════════════════════════╝"

docker build \
    --tag "${IMAGE_NAME}" \
    --file "${SCRIPT_DIR}/Dockerfile" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    "${SCRIPT_DIR}"

echo ""
echo "✓ Build complete: ${IMAGE_NAME}"
echo ""
echo "Next steps:"
echo "  1. Copy your UrbanNav rosbag into ./data/"
echo "  2. ./run_pipeline.sh ./data/UrbanNav-HK-TST-20210517_sensors.bag"
echo "  or"
echo "  2. ./run.sh  (interactive shell)"
