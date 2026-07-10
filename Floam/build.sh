#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NO_CACHE="${1:-}"

if [[ "$NO_CACHE" != "" && "$NO_CACHE" != "--no-cache" ]]; then
  echo "Usage: ./Floam/build.sh [--no-cache]" >&2
  exit 2
fi

docker build ${NO_CACHE} --network host \
  -f "${ROOT}/Floam/docker/Dockerfile" \
  -t floam-e2o:latest \
  "${ROOT}"
