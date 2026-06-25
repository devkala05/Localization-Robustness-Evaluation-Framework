#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION="${1:-help}"
ALGORITHM="${2:-}"

usage() {
  cat <<'EOF'
Usage:
  ./test_estimators.sh run fast [bag]       Run FAST-LIVO2 alone with RViz
  ./test_estimators.sh run orb [bag]        Run ORB-SLAM3 alone with RViz
  ./test_estimators.sh verify fast RUN_DIR  Validate FAST-LIVO2 output
  ./test_estimators.sh verify orb RUN_DIR   Validate ORB-SLAM3 output
EOF
}

case "$ACTION:$ALGORITHM" in
  run:fast|run:orb)
    BAG="${3:-$ROOT/data/e2o/raw/one_full_loop.bag}"
    MODE="fast_livo2"
    [[ "$ALGORITHM" == "orb" ]] && MODE="orbslam3"
    exec env RVIZ="${RVIZ:-true}" "$ROOT/run.sh" "$MODE" e2o "$BAG"
    ;;
  verify:fast|verify:orb)
    RUN_DIR="${3:-}"
    [[ -n "$RUN_DIR" ]] || { usage; exit 2; }
    NAME="fast_livo2"
    [[ "$ALGORITHM" == "orb" ]] && NAME="orbslam3"
    exec python3 "$ROOT/tests/verify_estimator_run.py" "$NAME" "$RUN_DIR"
    ;;
  *)
    usage
    [[ "$ACTION" == "help" || "$ACTION" == "-h" || "$ACTION" == "--help" ]]
    ;;
esac
