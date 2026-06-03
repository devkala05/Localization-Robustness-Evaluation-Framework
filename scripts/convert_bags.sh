#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${ROOT_DIR}/.venv/bin/python"
if [ ! -x "${PYTHON}" ]; then
  PYTHON="python3"
fi

"${PYTHON}" "${ROOT_DIR}/scripts/kitti_to_ros2bag.py" \
  --kitti_root "${ROOT_DIR}/data/raw/kitti/2011_09_26" \
  --sequence 2011_09_26_drive_0005_sync \
  --output "${ROOT_DIR}/data/sequences/urban_01" \
  --calib "${ROOT_DIR}/data/raw/kitti/2011_09_26"

"${PYTHON}" "${ROOT_DIR}/scripts/kitti_to_ros2bag.py" \
  --kitti_root "${ROOT_DIR}/data/raw/kitti/2011_09_26" \
  --sequence 2011_09_26_drive_0001_sync \
  --output "${ROOT_DIR}/data/sequences/highway_01" \
  --calib "${ROOT_DIR}/data/raw/kitti/2011_09_26"
