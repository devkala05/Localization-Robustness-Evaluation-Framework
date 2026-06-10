#!/bin/bash
# ============================================================
# run.sh  —  Start FAST-LIVO2 wrapper container (interactive)
# ============================================================
# Usage:
#   ./run.sh                               # drop into bash shell
#   ./run.sh ./run_pipeline.sh /data/x.bag # run pipeline directly
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="fastlivo2-wrapper:latest"
CONTAINER_NAME="fastlivo2_interactive"

# Allow X forwarding
[ -z "${DISPLAY:-}" ] && export DISPLAY=:0
xhost +local:docker 2>/dev/null || true

echo "═══════════════════════════════════════════════════════"
echo "  Image:   ${IMAGE_NAME}"
echo "  Data:    ${SCRIPT_DIR}/data  →  /data"
echo "  Output:  ${SCRIPT_DIR}/data/output  →  /data/output"
echo "═══════════════════════════════════════════════════════"

docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

docker run -it \
    --name "${CONTAINER_NAME}" \
    --network host \
    --privileged \
    -e DISPLAY="${DISPLAY}" \
    -e ROS_MASTER_URI=http://localhost:11311 \
    -e ROS_HOSTNAME=localhost \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "${SCRIPT_DIR}/data":/data \
    -v "${SCRIPT_DIR}/wrappers/fast_livo2_wrapper":/root/catkin_ws/src/fast_livo2_wrapper \
    "${IMAGE_NAME}" \
    "${@:-bash}"
