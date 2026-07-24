#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AVAILABLE_KIB="$(df --output=avail -k "$ROOT" | tail -1 | tr -d ' ')"
REQUIRED_KIB=$((32 * 1024 * 1024))
if (( AVAILABLE_KIB < REQUIRED_KIB )); then
  echo "At least 32 GiB free is required before downloading; available KiB=${AVAILABLE_KIB}" >&2
  exit 1
fi
"${ROOT}/scripts/datasets/download_urbanloco.sh"
"${ROOT}/scripts/datasets/download_boreas_rt.sh"

