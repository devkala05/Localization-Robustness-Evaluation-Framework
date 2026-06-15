#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="all"; NO_CACHE=""
usage(){ cat <<'EOF'
Usage:
  ./build.sh [all|fastlio2|lvisam|fastlivo2|rtabmap|adaptive_w_lvio|orbslam3|r3live] [--no-cache]

The build is dataset-independent. Bags are required only at run time.
EOF
}
while [ "$#" -gt 0 ]; do
  case "$1" in
    all|fastlio2|lvisam|fastlivo2|rtabmap|adaptive_w_lvio|orbslam3|r3live) TARGET="$1"; shift;;
    --algo) TARGET="${2:-}"; shift 2;; --algo=*) TARGET="${1#*=}"; shift;;
    --no-cache) NO_CACHE="--no-cache"; shift;;
    -h|--help) usage; exit 0;;
    *) echo "ERROR: unknown argument $1"; usage; exit 2;;
  esac
done
command -v docker >/dev/null || { echo "ERROR: docker is not installed or not in PATH"; exit 1; }
build_one(){
  case "$1" in
    fastlio2) "$ROOT/build_fastlio2.sh" $NO_CACHE;;
    lvisam) "$ROOT/build_lvisam.sh" $NO_CACHE;;
    fastlivo2) "$ROOT/build_fastlivo2.sh" $NO_CACHE;;
    rtabmap) "$ROOT/build_rtabmap.sh" $NO_CACHE;;
    adaptive_w_lvio) "$ROOT/build_adaptive_w_lvio.sh" $NO_CACHE;;
    orbslam3) "$ROOT/build_orbslam3.sh" $NO_CACHE;;
    r3live) "$ROOT/build_r3live.sh" $NO_CACHE;;
    *) echo "ERROR: unknown target $1"; exit 2;;
  esac
}
if [ "$TARGET" = "all" ]; then
  for algo in fastlio2 lvisam fastlivo2 rtabmap adaptive_w_lvio orbslam3 r3live; do build_one "$algo"; done
else
  build_one "$TARGET"
fi
