#!/usr/bin/env bash
set -u

# Convenience wrapper for one run.
# Put folder inside codebase root, then:
#   cd benchmark_matrix_runner
#   ./run_one.sh r3live 0 off
#   ./run_one.sh lvisam 3 on

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALGO="${1:-}"
PER="${2:-0}"
GPS="${3:-off}"
shift $(( $# >= 1 ? 1 : 0 )) || true
shift $(( $# >= 1 ? 1 : 0 )) || true
shift $(( $# >= 1 ? 1 : 0 )) || true

if [[ -z "$ALGO" ]]; then
  echo "Usage: ./run_one.sh <algo> [per] [gps:on|off] [extra run_all options]"
  echo "Example: ./run_one.sh r3live 0 off --timeout-min 30"
  exit 2
fi

"$SCRIPT_DIR/run_all.sh" --algos "$ALGO" --per "$PER" --gps "$GPS" --no-build "$@"
