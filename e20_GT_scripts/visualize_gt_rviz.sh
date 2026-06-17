#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSV_PATH="${1:-${SCRIPT_DIR}/gt_one_full_loop_gps_enu.csv}"
IMAGE="${ROS_DOCKER_IMAGE:-osrf/ros:noetic-desktop-full}"

if [[ ! -f "${CSV_PATH}" ]]; then
  echo "CSV not found: ${CSV_PATH}" >&2
  echo "Create it first with: ${SCRIPT_DIR}/make_gt_csv.sh" >&2
  exit 1
fi

if [[ -z "${DISPLAY:-}" ]]; then
  echo "DISPLAY is not set. Run from a graphical Linux session with X11 forwarding enabled." >&2
  exit 1
fi

xhost +local:docker >/dev/null

FRAME_ID="$(python3 - "${CSV_PATH}" <<'PY'
import csv
import sys
with open(sys.argv[1], newline="") as handle:
    row = next(csv.DictReader(handle), {})
print(row.get("frame_id") or "map")
PY
)"
TMP_RVIZ="$(mktemp /tmp/gt_path_XXXXXX.rviz)"
sed "s/Fixed Frame: .*/Fixed Frame: ${FRAME_ID}/; s/Reference Frame: .*/Reference Frame: ${FRAME_ID}/; s/Target Frame: .*/Target Frame: ${FRAME_ID}/" \
  "${SCRIPT_DIR}/gt_path.rviz" > "${TMP_RVIZ}"

docker run --rm -it \
  --net=host \
  -e DISPLAY="${DISPLAY}" \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v "${SCRIPT_DIR}:/ws" \
  -v "$(dirname "${CSV_PATH}"):/gt:ro" \
  -v "${TMP_RVIZ}:/tmp/gt_path.rviz:ro" \
  -w /ws \
  "${IMAGE}" \
  bash -lc "source /opt/ros/noetic/setup.bash && roscore >/tmp/gt_roscore.log 2>&1 & sleep 2 && python3 /ws/publish_gt_path.py --csv /gt/$(basename "${CSV_PATH}") --stride 10 --frame-id ${FRAME_ID} >/tmp/gt_path.log 2>&1 & rviz -d /tmp/gt_path.rviz"
