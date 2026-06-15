#!/usr/bin/env bash
set -euo pipefail
ROOT="${E2O_EVAL_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
REQUESTED="${1:-}"

resolve_path() {
  local p="$1"
  if [[ -z "$p" ]]; then return 1; fi
  if [[ -f "$p" ]]; then realpath "$p"; return 0; fi
  if [[ -f "$ROOT/$p" ]]; then realpath "$ROOT/$p"; return 0; fi
  if [[ -f "$ROOT/data/$p" ]]; then realpath "$ROOT/data/$p"; return 0; fi
  if [[ -f "$ROOT/data/raw/$p" ]]; then realpath "$ROOT/data/raw/$p"; return 0; fi
  return 1
}

if [[ -n "$REQUESTED" ]]; then
  resolve_path "$REQUESTED" || { echo "ERROR: bag not found: $REQUESTED" >&2; exit 2; }
  exit 0
fi

mapfile -t bags < <(find "$ROOT/data" -type f -name '*.bag' | sort)
if [[ ${#bags[@]} -eq 0 ]]; then
  echo "ERROR: no .bag file found under $ROOT/data" >&2
  echo "Put your bag anywhere under data/, for example: data/raw/one_loop.bag" >&2
  exit 3
elif [[ ${#bags[@]} -eq 1 ]]; then
  realpath "${bags[0]}"
else
  echo "ERROR: multiple .bag files found. Pass --bag <name-or-path>." >&2
  printf '  %s\n' "${bags[@]}" >&2
  exit 4
fi
