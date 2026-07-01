#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${1:?Usage: ./evaluation/evaluate.sh data/output/<run_id> [ground_truth.csv]}"
GT="${2:-${ROOT}/data/e2o/ground_truth/ref.csv}"
python3 "${ROOT}/evaluation/evaluate_e2o.py" --run-dir "${RUN_DIR}" --gt "${GT}"
