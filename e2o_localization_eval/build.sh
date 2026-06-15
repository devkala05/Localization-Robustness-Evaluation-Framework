#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker build -t e2o-localization-eval:noetic -f "$ROOT/docker/Dockerfile" "$ROOT"
echo "Built Docker image: e2o-localization-eval:noetic"
