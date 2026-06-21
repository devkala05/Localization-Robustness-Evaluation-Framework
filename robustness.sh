#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION="${1:-help}"
shift || true

latest_run() {
  local name
  name="$(find "$ROOT/data/output" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null |
    sort -r | head -1)"
  [[ -n "$name" ]] && printf '%s/%s\n' "$ROOT/data/output" "$name"
}

usage() {
  cat <<'EOF'
Usage:
  ./robustness.sh run [bag]             Start fault-enabled fusion with RViz
  ./robustness.sh status [run_dir]      Show current health/fusion summary
  ./robustness.sh watch [run_dir]       Refresh status every two seconds
  ./robustness.sh record [output_dir]   Record live ROS status/events/health
  ./robustness.sh recover-all           Clear every sensor and pose fault
  ./robustness.sh matrix                Show expected robustness outcomes
  ./robustness.sh SCENARIO [VALUE]      Apply a failure_control.sh scenario

Examples:
  ./robustness.sh fast_freeze
  ./robustness.sh fast_recover
  ./robustness.sh camera_drop
  ./robustness.sh camera_recover
EOF
}

case "$ACTION" in
  run)
    BAG="${1:-$ROOT/data/e2o/raw/one_full_loop.bag}"
    exec env FAULT_INJECTION=true RVIZ="${RVIZ:-true}" "$ROOT/run.sh" fusion e2o "$BAG"
    ;;
  status)
    RUN_DIR="${1:-$(latest_run)}"
    [[ -n "$RUN_DIR" ]] || { echo "No run directory found." >&2; exit 1; }
    exec python3 "$ROOT/tests/robustness_status.py" "$RUN_DIR"
    ;;
  watch)
    RUN_DIR="${1:-$(latest_run)}"
    [[ -n "$RUN_DIR" ]] || { echo "No run directory found." >&2; exit 1; }
    while true; do
      clear
      python3 "$ROOT/tests/robustness_status.py" "$RUN_DIR" || true
      sleep 2
    done
    ;;
  record)
    exec "$ROOT/tests/observe_switching.sh" "${1:-/tmp/e2o_robustness_$(date +%Y%m%d_%H%M%S)}"
    ;;
  recover-all)
    for scenario in camera_recover lidar_recover imu_recover fast_recover orb_recover; do
      "$ROOT/tests/failure_control.sh" "$scenario"
    done
    ;;
  matrix)
    if command -v column >/dev/null 2>&1; then
      column -s, -t "$ROOT/tests/failure_matrix.csv"
    else
      cat "$ROOT/tests/failure_matrix.csv"
    fi
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    exec "$ROOT/tests/failure_control.sh" "$ACTION" "$@"
    ;;
esac
