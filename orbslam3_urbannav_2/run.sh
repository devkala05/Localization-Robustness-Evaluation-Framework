#!/bin/bash
# ============================================================
# run.sh  —  Start the ORB-SLAM3 UrbanNav container
# ============================================================
# Usage:
#   ./run.sh                    # interactive shell
#   ./run.sh bash run_pipeline.sh /data/bag.bag
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="orbslam3-urbannav:latest"
CONTAINER_NAME="orbslam3_urbannav_run"

if [ -z "${DISPLAY:-}" ] && [ -S /tmp/.X11-unix/X1 ]; then
    export DISPLAY=:1
fi

xhost +local:docker 2>/dev/null || true

echo "═══════════════════════════════════════════════════════"
echo "  Starting container: ${CONTAINER_NAME}"
echo "  Image:  ${IMAGE_NAME}"
echo "  Data:   ${SCRIPT_DIR}/data → /data"
echo "═══════════════════════════════════════════════════════"

docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

docker run -it \
    --name "${CONTAINER_NAME}" \
    --network host \
    --privileged \
    -e DISPLAY="${DISPLAY:-:0}" \
    -e ROS_MASTER_URI=http://localhost:11311 \
    -e ROS_HOSTNAME=localhost \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "${SCRIPT_DIR}/data":/data \
    -v "${SCRIPT_DIR}/run_pipeline.sh":/root/run_pipeline.sh:ro \
    -v "${SCRIPT_DIR}/wrappers/orbslam3_urbannav":/root/catkin_ws/src/orbslam3_urbannav \
    "${IMAGE_NAME}" \
    "${@:-bash}"
