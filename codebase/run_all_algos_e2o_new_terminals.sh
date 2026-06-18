#!/usr/bin/env bash
set -euo pipefail

# E2O-only full benchmark launcher.
# This intentionally reuses run_all_algos_new_terminals.sh so build/run order,
# terminal handling, eval mode, GPS modes, perturbations, and overrides stay
# identical to the main launcher. The only forced difference is DATASET_LIST=e2o.
#
# Usage:
#   ./run_all_algos_e2o_new_terminals.sh
#
# Optional environment overrides still work:
#   ALGO_LIST="fastlio2 lvisam" ./run_all_algos_e2o_new_terminals.sh
#   PER_LIST="0 1" GPS_LIST="off" ./run_all_algos_e2o_new_terminals.sh
#   START_ALGO=rtabmap START_PER=3 ./run_all_algos_e2o_new_terminals.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

usage() {
  cat <<'USAGE'
E2O-only run-all benchmark launcher.

Runs the same full matrix as run_all_algos_new_terminals.sh, but only for dataset=e2o:
  7 algorithms x 7 perturbations x GPS off/on, with --eval.

Usage:
  ./run_all_algos_e2o_new_terminals.sh

Optional environment overrides:
  ALGO_LIST="fastlio2 lvisam" ./run_all_algos_e2o_new_terminals.sh
  PER_LIST="0 1 2" ./run_all_algos_e2o_new_terminals.sh
  GPS_LIST="off" ./run_all_algos_e2o_new_terminals.sh
  START_ALGO=rtabmap ./run_all_algos_e2o_new_terminals.sh
  START_PER=3 ./run_all_algos_e2o_new_terminals.sh

Use ./run_all_algos_new_terminals.sh when you want both datasets or custom DATASET_LIST.
USAGE
}

case "${1:-}" in
  -h|--help)
    usage
    exit 0
    ;;
  "")
    ;;
  *)
    echo "ERROR: this launcher uses environment overrides, not positional arguments." >&2
    usage >&2
    exit 2
    ;;
esac

if [ ! -x "${ROOT_DIR}/run_all_algos_new_terminals.sh" ]; then
  chmod +x "${ROOT_DIR}/run_all_algos_new_terminals.sh"
fi

export DATASET_LIST="e2o"
exec "${ROOT_DIR}/run_all_algos_new_terminals.sh"
