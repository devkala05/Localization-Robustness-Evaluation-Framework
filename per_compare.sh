#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/wrappers/localization_benchmark/scripts/trajectory_analysis.py" per_compare "$@"
