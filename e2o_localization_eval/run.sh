#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${IMAGE:-e2o-localization-eval:noetic}"
MODE="${1:-shell}"
if [[ $# -gt 0 ]]; then shift; fi

mkdir -p "$ROOT/data/raw" "$ROOT/data/ground_truth" "$ROOT/data/outputs"

XSOCK=/tmp/.X11-unix
XAUTH=${XAUTHORITY:-$HOME/.Xauthority}
DOCKER_ARGS=(
  --rm
  --net=host
  -e DISPLAY="${DISPLAY:-}"
  -e QT_X11_NO_MITSHM=1
  -e E2O_EVAL_ROOT=/workspace/e2o_eval
  -v "$ROOT:/workspace/e2o_eval"
)
if [[ -t 0 ]]; then
  DOCKER_ARGS+=( -it )
fi
if [[ -d "$XSOCK" ]]; then
  DOCKER_ARGS+=( -v "$XSOCK:$XSOCK:rw" )
fi
if [[ -f "$XAUTH" ]]; then
  DOCKER_ARGS+=( -e XAUTHORITY=/tmp/.docker.xauth -v "$XAUTH:/tmp/.docker.xauth:ro" )
fi

exec docker run "${DOCKER_ARGS[@]}" "$IMAGE" "$MODE" "$@"
