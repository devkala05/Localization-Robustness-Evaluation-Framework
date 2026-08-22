#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="${1:-$ROOT/robustness/results/latest}"
python3 "$ROOT/robustness/scripts/evaluate_robustness.py" \
  --config "${PERTURBATION_CONFIG:-$ROOT/robustness/config/alive_perturbations.yaml}" \
  --results-root "$ROOT/results/alive/one_full_loop" \
  --output "$OUTPUT"
