#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BAG_PATH="${1:-${SCRIPT_DIR}/one_full_loop.bag}"
OUT_CSV="${2:-${SCRIPT_DIR}/gt_one_full_loop_gps_enu.csv}"
IMAGE="${ROS_DOCKER_IMAGE:-osrf/ros:noetic-desktop-full}"

if [[ ! -f "${BAG_PATH}" ]]; then
  echo "Bag not found: ${BAG_PATH}" >&2
  exit 1
fi

mkdir -p "$(dirname "${OUT_CSV}")"

docker run --rm \
  -v "${SCRIPT_DIR}:/ws" \
  -v "$(dirname "${BAG_PATH}"):/bag:ro" \
  -v "$(dirname "${OUT_CSV}"):/out" \
  -w /ws \
  "${IMAGE}" \
  bash -lc "source /opt/ros/noetic/setup.bash && python3 /ws/export_gt_gps_enu.py --bag /bag/$(basename "${BAG_PATH}") --output /out/$(basename "${OUT_CSV}")"

echo "CSV ready: ${OUT_CSV}"
