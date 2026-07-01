#!/usr/bin/env bash
set -Eeuo pipefail

# ROS Noetic setup scripts reference unset variables internally, so do not
# keep bash nounset (-u) enabled while sourcing them.
set +u
source /opt/ros/noetic/setup.bash
set -u

cleanup() {
  [[ -n "${PUBLISHER_PID:-}" ]] && kill "${PUBLISHER_PID}" 2>/dev/null || true
  [[ -n "${ROSCORE_PID:-}" ]] && kill "${ROSCORE_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

roscore >/tmp/roscore.log 2>&1 &
ROSCORE_PID=$!

# Wait until roscore really accepts requests.
for _ in $(seq 1 30); do
  if rosparam list >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

if ! rosparam list >/dev/null 2>&1; then
  echo "ERROR: roscore did not start. Log:" >&2
  cat /tmp/roscore.log >&2 || true
  exit 1
fi

python3 /work/compare_csv_trajectories.py "$@" &
PUBLISHER_PID=$!

# Do not open an empty RViz window if CSV parsing/publishing failed.
sleep 1
if ! kill -0 "$PUBLISHER_PID" 2>/dev/null; then
  echo "ERROR: CSV trajectory publisher exited before RViz started." >&2
  wait "$PUBLISHER_PID" || true
  exit 1
fi

rviz -d /opt/csv_compare/csv_compare.rviz
RVIZ_STATUS=$?
exit "$RVIZ_STATUS"
