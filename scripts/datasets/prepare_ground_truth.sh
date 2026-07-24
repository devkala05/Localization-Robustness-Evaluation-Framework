#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATASET="${1:-all}"

convert_urban() {
  local sequence="$ROOT/data/datasets/urbanloco/ca_20190828184706"
  local bag="$sequence/CA-20190828184706_blur_align-002.bag"
  local calibration="$sequence/calibration/calibration_CA.txt"
  [[ -f "$bag" && -f "$calibration" ]] || { printf 'UrbanLoco inputs are incomplete\n' >&2; return 1; }
  docker image inspect e2o-localization-fusion:latest >/dev/null
  docker run --rm -v "$ROOT:/workspace" e2o-localization-fusion:latest \
    python3 /workspace/tools/convert_public_ground_truth.py --dataset urbanloco \
      --input "/workspace/${bag#"$ROOT/"}" \
      --calibration "/workspace/${calibration#"$ROOT/"}" \
      --output "/workspace/${sequence#"$ROOT/"}/ground_truth.csv"
}

convert_boreas() {
  local sequence="$ROOT/data/datasets/boreas_rt/boreas-2024-12-04-14-44"
  [[ -f "$sequence/applanix/gps_post_process.csv" && -f "$sequence/calib/T_applanix_dmu.txt" ]] || {
    printf 'Boreas-RT inputs are incomplete\n' >&2; return 1;
  }
  python3 "$ROOT/tools/convert_public_ground_truth.py" --dataset boreas_rt \
    --input "$sequence" --output "$sequence/ground_truth.csv"
}

case "$DATASET" in
  urbanloco) convert_urban ;;
  boreas|boreas_rt) convert_boreas ;;
  all) convert_urban; convert_boreas ;;
  *) printf 'Usage: %s [urbanloco|boreas_rt|all]\n' "$0" >&2; exit 2 ;;
esac
