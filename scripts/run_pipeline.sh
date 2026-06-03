#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/ros2_ws/src/orchestrator:${ROOT_DIR}/ros2_ws/src/evaluator:${ROOT_DIR}/ros2_ws/src/perturbation_injector:${PYTHONPATH:-}"

python3 "${ROOT_DIR}/ros2_ws/src/orchestrator/orchestrator/orchestrator.py" \
  --config "${ROOT_DIR}/config/pipeline.yaml" \
  "$@"
