#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-/tmp/e2o_switch_observation_$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$OUT"
if command -v rostopic >/dev/null 2>&1; then
  ROS_ECHO=(rostopic echo)
else
  CONTAINER="$(docker ps --format '{{.Names}}' | grep '_fusion$' | tail -1)"
  [[ -n "$CONTAINER" ]] || { echo "No running fusion container found." >&2; exit 1; }
  ROS_ECHO=(docker exec "$CONTAINER" bash -c
    'source /opt/ros/noetic/setup.bash; source /root/catkin_ws/devel/setup.bash; rostopic echo "$@"'
    _)
fi
"${ROS_ECHO[@]}" /fused_localization/status > "$OUT/status.log" & P1=$!
"${ROS_ECHO[@]}" /fused_localization/events > "$OUT/events.log" & P2=$!
"${ROS_ECHO[@]}" /localization_health/summary > "$OUT/health.log" & P3=$!
trap 'kill $P1 $P2 $P3 2>/dev/null || true' EXIT INT TERM
echo "Recording to $OUT; press Ctrl-C to stop."
wait
