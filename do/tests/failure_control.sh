#!/usr/bin/env bash
set -euo pipefail
SCENARIO="${1:-}"
VALUE="${2:-}"
usage() {
  cat <<USAGE
Usage: tests/failure_control.sh SCENARIO [VALUE]
Start the stack with FAULT_INJECTION=true for pose-fault scenarios.
Scenarios:
  camera_drop|camera_freeze|camera_delay [seconds]|camera_recover
  lidar_drop|lidar_freeze|lidar_delay [seconds]|lidar_recover
  imu_drop|imu_freeze|imu_delay [seconds]|imu_recover
  fast_freeze|fast_nan|fast_jump [metres]|fast_delay [seconds]|fast_out_of_order|fast_recover
  orb_freeze|orb_nan|orb_jump [metres]|orb_delay [seconds]|orb_out_of_order|orb_recover
  kill_fast|restart_fast|kill_orb|restart_orb
USAGE
}
[[ -n "$SCENARIO" ]] || { usage; exit 2; }
fusion_container() {
  docker ps --format '{{.Names}}' | grep '_fusion$' | tail -1
}
rosparam_set() {
  if command -v rosparam >/dev/null 2>&1; then
    rosparam set "$1" "$2"
    return
  fi
  local container
  container="$(fusion_container)"
  [[ -n "$container" ]] || { echo "No running fusion container found." >&2; exit 1; }
  docker exec "$container" bash -c \
    'source /opt/ros/noetic/setup.bash; source /root/catkin_ws/devel/setup.bash; rosparam "$@"' \
    _ set "$1" "$2"
}
sensor() {
  local name="$1" mode="$2" delay="${3:-1.0}"
  rosparam_set "/e2o_faults/${name}/mode" "$mode"
  if [[ "$mode" == delay ]]; then
    rosparam_set "/e2o_faults/${name}/delay_sec" "$delay"
  fi
}
pose() {
  local name="$1" mode="$2" amount="${3:-}"
  rosparam_set "/${name}_pose_fault/mode" "$mode"
  case "$mode" in
    delay) rosparam_set "/${name}_pose_fault/delay_sec" "${amount:-1.0}" ;;
    jump) rosparam_set "/${name}_pose_fault/jump_m" "${amount:-100.0}" ;;
    out_of_order) rosparam_set "/${name}_pose_fault/stamp_offset_sec" "${amount:-5.0}" ;;
  esac
}
case "$SCENARIO" in
  camera_drop) sensor camera drop;; camera_freeze) sensor camera freeze;; camera_delay) sensor camera delay "${VALUE:-1.0}";; camera_recover) sensor camera pass;;
  lidar_drop) sensor lidar drop;; lidar_freeze) sensor lidar freeze;; lidar_delay) sensor lidar delay "${VALUE:-1.0}";; lidar_recover) sensor lidar pass;;
  imu_drop) sensor imu drop;; imu_freeze) sensor imu freeze;; imu_delay) sensor imu delay "${VALUE:-1.0}";; imu_recover) sensor imu pass;;
  fast_freeze) pose fast_livo2 freeze;; fast_nan) pose fast_livo2 nan;; fast_jump) pose fast_livo2 jump "${VALUE:-100.0}";; fast_delay) pose fast_livo2 delay "${VALUE:-1.0}";; fast_out_of_order) pose fast_livo2 out_of_order "${VALUE:-5.0}";; fast_recover) pose fast_livo2 pass;;
  orb_freeze) pose orbslam3 freeze;; orb_nan) pose orbslam3 nan;; orb_jump) pose orbslam3 jump "${VALUE:-100.0}";; orb_delay) pose orbslam3 delay "${VALUE:-1.0}";; orb_out_of_order) pose orbslam3 out_of_order "${VALUE:-5.0}";; orb_recover) pose orbslam3 pass;;
  kill_fast) name=$(docker ps --format '{{.Names}}' | grep '_fast$' | tail -1); [[ -n "$name" ]] && docker stop "$name";;
  restart_fast) name=$(docker ps -a --format '{{.Names}}' | grep '_fast$' | tail -1); [[ -n "$name" ]] && docker restart "$name";;
  kill_orb) name=$(docker ps --format '{{.Names}}' | grep '_orb$' | tail -1); [[ -n "$name" ]] && docker stop "$name";;
  restart_orb) name=$(docker ps -a --format '{{.Names}}' | grep '_orb$' | tail -1); [[ -n "$name" ]] && docker restart "$name";;
  *) usage; exit 2;;
esac
printf 'Applied scenario: %s\n' "$SCENARIO"
