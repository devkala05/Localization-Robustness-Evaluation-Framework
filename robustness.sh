#!/usr/bin/env bash
# robustness.sh — single entry point for all E2O fault testing and monitoring.
#
# Covers: starting fault-enabled runs, live status, gate-level sensor faults,
# estimator pose faults, process kill/restart, and recording.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION="${1:-help}"
shift || true

# ── color codes ───────────────────────────────────────────────────────────────
RED=$'\033[0;31m'; GRN=$'\033[0;32m'; YEL=$'\033[0;33m'
CYN=$'\033[0;36m'; BOLD=$'\033[1m'; DIM=$'\033[2m'; RST=$'\033[0m'

# ── helpers ───────────────────────────────────────────────────────────────────
latest_run() {
  local name
  name="$(find "$ROOT/data/output" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null \
    | sort -r | head -1)"
  [[ -n "$name" ]] && printf '%s/%s\n' "$ROOT/data/output" "$name"
}

fusion_container() {
  docker ps --format '{{.Names}}' 2>/dev/null | grep '_fusion$' | tail -1 || true
}

_rosparam() {
  local op="$1"; shift
  if command -v rosparam >/dev/null 2>&1; then
    rosparam "$op" "$@"
    return
  fi
  local c; c="$(fusion_container)"
  [[ -n "$c" ]] || { printf '%sNo running fusion container and rosparam not found.%s\n' "$RED" "$RST" >&2; exit 1; }
  docker exec "$c" bash -lc "source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash && rosparam $op $(printf '%q ' "$@")"
}

sensor() {
  local name="$1" mode="$2" delay="${3:-1.0}"
  _rosparam set "/e2o_faults/${name}/mode" "$mode"
  [[ "$mode" == "delay" ]] && _rosparam set "/e2o_faults/${name}/delay_sec" "$delay"
}

pose() {
  local name="$1" mode="$2" amount="${3:-}"
  _rosparam set "/${name}_pose_fault/mode" "$mode"
  case "$mode" in
    delay)        _rosparam set "/${name}_pose_fault/delay_sec"       "${amount:-1.0}"   ;;
    jump)         _rosparam set "/${name}_pose_fault/jump_m"          "${amount:-100.0}" ;;
    out_of_order) _rosparam set "/${name}_pose_fault/stamp_offset_sec" "${amount:-5.0}" ;;
  esac
}

find_container() {
  docker ps -a --format '{{.Names}}' 2>/dev/null | grep "_${1}$" | tail -1 || true
}

kill_container() {
  local n; n="$(docker ps --format '{{.Names}}' 2>/dev/null | grep "_${1}$" | tail -1 || true)"
  [[ -n "$n" ]] && docker stop "$n" >/dev/null
}

restart_container() {
  local n; n="$(find_container "$1")"
  [[ -n "$n" ]] && docker restart "$n" >/dev/null
}

gate_mode() {
  local value
  value="$(_rosparam get "/e2o_faults/${1}/mode" 2>/dev/null || true)"
  value="$(printf '%s' "$value" | tr -d '"' | tr '[:upper:]' '[:lower:]')"
  [[ -z "$value" || "$value" == "not set" ]] && value="pass"
  printf '%s\n' "$value"
}

gate_pass() {
  [[ "$(gate_mode "$1")" == "pass" ]]
}

restart_ready_estimators() {
  # The adapter refreshes fault gate params at 5 Hz. Give it time to observe
  # pass mode and publish fresh sensor messages before native estimator init.
  sleep "${RECOVERY_RESTART_DELAY_SEC:-0.75}"
  local restarted=()
  if gate_pass lidar && gate_pass imu && gate_pass camera; then
    restart_container fast
    restarted+=("fast")
  fi
  if gate_pass lidar && gate_pass imu; then
    restart_container lvisam
    restarted+=("lvisam")
  fi
  if gate_pass camera && gate_pass depth; then
    restart_container orb
    restarted+=("orb")
  fi
  if ((${#restarted[@]})); then
    printf '%sRestarted ready estimators: %s%s\n' "$GRN" "${restarted[*]}" "$RST"
  else
    printf '%sNo estimator has all required sensor gates in pass mode yet.%s\n' "$YEL" "$RST"
  fi
}

gate_val() {
  _rosparam get "$1" 2>/dev/null || echo "(not set)"
}

gate_colored() {
  local v; v="$(_rosparam get "$1" 2>/dev/null || echo "not set")"
  case "$v" in
    pass)         printf '%s%-10s%s' "$GRN"  "pass"   "$RST" ;;
    drop)         printf '%s%-10s%s' "$RED"  "drop"   "$RST" ;;
    freeze|delay) printf '%s%-10s%s' "$YEL"  "$v"     "$RST" ;;
    *)            printf '%s%-10s%s' "$DIM"  "$v"     "$RST" ;;
  esac
}

# ── usage ─────────────────────────────────────────────────────────────────────
usage() {
  printf '%sUsage:%s\n' "$BOLD" "$RST"
  cat <<'EOF'
  ./robustness.sh run [bag]              Start fault-enabled fusion (FAULT_INJECTION=true)
  ./robustness.sh status [run_dir]       Print health/fusion summary once
  ./robustness.sh watch  [run_dir]       Live colorful status, refreshes every 1 s
  ./robustness.sh gate-status            Live sensor gate modes display, refreshes every 1 s
  ./robustness.sh record [output_dir]    Record live ROS topics (status/events/health) to files
  ./robustness.sh recover-all            Clear every active sensor and pose fault
  ./robustness.sh matrix                 Show expected failure outcome table

EOF
  printf '%sSensor faults  (stream gate — no FAULT_INJECTION required):%s\n' "$BOLD" "$RST"
  cat <<'EOF'
  camera_drop  camera_freeze  camera_delay [s]  camera_recover
  lidar_drop   lidar_freeze   lidar_delay  [s]  lidar_recover
  imu_drop     imu_freeze     imu_delay    [s]  imu_recover

EOF
  printf '%sPose faults  (estimator output — requires FAULT_INJECTION=true):%s\n' "$BOLD" "$RST"
  cat <<'EOF'
  fast_freeze   fast_nan   fast_jump [m]   fast_delay [s]   fast_out_of_order   fast_recover
  lvisam_freeze lvisam_nan lvisam_jump [m] lvisam_delay [s] lvisam_out_of_order lvisam_recover
  orb_freeze    orb_nan    orb_jump  [m]   orb_delay  [s]   orb_out_of_order    orb_recover

EOF
  printf '%sProcess control:%s\n' "$BOLD" "$RST"
  cat <<'EOF'
  kill_fast    restart_fast
  kill_lvisam  restart_lvisam
  kill_orb     restart_orb
EOF
}

# ── main ──────────────────────────────────────────────────────────────────────
case "$ACTION" in

  run)
    BAG="${1:-$ROOT/data/e2o/raw/one_full_loop.bag}"
    exec env FAULT_INJECTION=true RVIZ="${RVIZ:-true}" "$ROOT/run.sh" fusion e2o "$BAG"
    ;;

  status)
    RUN_DIR="${1:-$(latest_run)}"
    [[ -n "$RUN_DIR" ]] || { printf '%sNo run directory found.%s\n' "$RED" "$RST" >&2; exit 1; }
    exec python3 "$ROOT/tests/robustness_status.py" "$RUN_DIR"
    ;;

  watch)
    RUN_DIR="${1:-$(latest_run)}"
    [[ -n "$RUN_DIR" ]] || { printf '%sNo run directory found.%s\n' "$RED" "$RST" >&2; exit 1; }
    while true; do
      clear
      printf '%s[watch] %s  (Ctrl-C to stop)%s\n\n' "$DIM" "$RUN_DIR" "$RST"
      python3 "$ROOT/tests/robustness_status.py" "$RUN_DIR" || true
      sleep 1
    done
    ;;

  gate-status)
    while true; do
      clear
      printf '%s━━  Sensor gate status  ━━%s  %s(Ctrl-C to stop)%s\n\n' "$BOLD" "$RST" "$DIM" "$RST"
      printf '%-20s %s\n' "Gate" "Mode"
      printf '%s\n' "────────────────────────────────"
      for gate in lidar camera depth imu; do
        printf '%-20s ' "/e2o_faults/${gate}/mode"
        gate_colored "/e2o_faults/${gate}/mode"
        printf '\n'
      done
      printf '\n%s%s%s\n' "$DIM" "$(date '+%H:%M:%S')" "$RST"
      sleep 1
    done
    ;;

  record)
    OUT="${1:-/tmp/e2o_robustness_$(date +%Y%m%d_%H%M%S)}"
    mkdir -p "$OUT"
    if command -v rostopic >/dev/null 2>&1; then
      ROS_ECHO=(rostopic echo)
    else
      C="$(fusion_container)"
      [[ -n "$C" ]] || { printf '%sNo running fusion container found.%s\n' "$RED" "$RST" >&2; exit 1; }
      ROS_ECHO=(docker exec "$C" bash -lc 'rostopic echo "$@"' _)
    fi
    "${ROS_ECHO[@]}" /fused_localization/status  > "$OUT/status.log"  & P1=$!
    "${ROS_ECHO[@]}" /fused_localization/events  > "$OUT/events.log"  & P2=$!
    "${ROS_ECHO[@]}" /localization_health/summary > "$OUT/health.log" & P3=$!
    trap 'kill $P1 $P2 $P3 2>/dev/null || true' EXIT INT TERM
    printf '%sRecording to %s — Ctrl-C to stop.%s\n' "$GRN" "$OUT" "$RST"
    wait
    ;;

  recover-all)
    for s in camera depth lidar imu; do sensor "$s" pass; done
    for e in fast_livo2 lvisam orbslam3; do pose "$e" pass; done
    restart_ready_estimators
    printf '%sAll sensor and pose faults cleared.%s\n' "$GRN" "$RST"
    ;;

  matrix)
    if command -v column >/dev/null 2>&1; then
      column -s, -t "$ROOT/tests/failure_matrix.csv"
    else
      cat "$ROOT/tests/failure_matrix.csv"
    fi
    ;;

  # ── sensor stream faults ──────────────────────────────────────────────────
  camera_drop)    sensor camera drop; sensor depth drop ;;
  camera_freeze)  sensor camera freeze; sensor depth freeze ;;
  camera_delay)   sensor camera delay "${1:-1.0}"; sensor depth delay "${1:-1.0}" ;;
  camera_recover) sensor camera pass; sensor depth pass; restart_ready_estimators ;;
  lidar_drop)     sensor lidar drop ;;
  lidar_freeze)   sensor lidar freeze ;;
  lidar_delay)    sensor lidar delay "${1:-1.0}" ;;
  lidar_recover)  sensor lidar pass; restart_ready_estimators ;;
  imu_drop)       sensor imu drop ;;
  imu_freeze)     sensor imu freeze ;;
  imu_delay)      sensor imu delay "${1:-1.0}" ;;
  imu_recover)    sensor imu pass; restart_ready_estimators ;;

  # ── estimator pose faults ─────────────────────────────────────────────────
  fast_freeze)       pose fast_livo2 freeze ;;
  fast_nan)          pose fast_livo2 nan ;;
  fast_jump)         pose fast_livo2 jump "${1:-100.0}" ;;
  fast_delay)        pose fast_livo2 delay "${1:-1.0}" ;;
  fast_out_of_order) pose fast_livo2 out_of_order "${1:-5.0}" ;;
  fast_recover)      pose fast_livo2 pass ;;

  lvisam_freeze)       pose lvisam freeze ;;
  lvisam_nan)          pose lvisam nan ;;
  lvisam_jump)         pose lvisam jump "${1:-100.0}" ;;
  lvisam_delay)        pose lvisam delay "${1:-1.0}" ;;
  lvisam_out_of_order) pose lvisam out_of_order "${1:-5.0}" ;;
  lvisam_recover)      pose lvisam pass ;;

  orb_freeze)       pose orbslam3 freeze ;;
  orb_nan)          pose orbslam3 nan ;;
  orb_jump)         pose orbslam3 jump "${1:-100.0}" ;;
  orb_delay)        pose orbslam3 delay "${1:-1.0}" ;;
  orb_out_of_order) pose orbslam3 out_of_order "${1:-5.0}" ;;
  orb_recover)      pose orbslam3 pass ;;

  # ── process control ───────────────────────────────────────────────────────
  kill_fast)      kill_container fast ;;
  restart_fast)   restart_container fast ;;
  kill_lvisam)    kill_container lvisam ;;
  restart_lvisam) restart_container lvisam ;;
  kill_orb)       kill_container orb ;;
  restart_orb)    restart_container orb ;;

  help|-h|--help) usage ;;
  *) printf '%sUnknown action: %s%s\n' "$RED" "$ACTION" "$RST" >&2; usage >&2; exit 2 ;;
esac

[[ "$ACTION" =~ ^(run|status|watch|gate-status|record|recover-all|matrix|help|-h|--help)$ ]] \
  || printf '%sApplied: %s%s\n' "$GRN" "$ACTION${1+ $1}" "$RST"
