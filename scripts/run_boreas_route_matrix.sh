#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEQUENCES=(
  boreas_2025_07_18_15_30_farm
  boreas_2025_07_18_11_53_forest
  boreas_2025_08_06_06_33_urban
)
ALGORITHMS=(fastlio2 fastlivo2 lvisam orbslam3 rtabmap)

if (($#)); then SEQUENCES=("$@"); fi

failures=()
for sequence in "${SEQUENCES[@]}"; do
  for algorithm in "${ALGORITHMS[@]}"; do
    printf '\n[%s] starting %s / %s\n' "$(date --iso-8601=seconds)" "$sequence" "$algorithm"
    extra_args=()
    if [[ "$algorithm" == orbslam3 || ( "$algorithm" == fastlivo2 && "$sequence" == boreas_2025_07_18_15_30_farm ) ]]; then
      pre_roll="$(python3 - "$ROOT/configs/datasets/boreas_rt/$sequence/sequence.yaml" "$algorithm" <<'PY'
import sys, yaml
source = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))["source"]
algorithm = sys.argv[2] if len(sys.argv) > 2 else "orbslam3"
print(source["fastlivo_pre_roll_seconds"] if algorithm == "fastlivo2" else source["orb_pre_roll_seconds"])
PY
)"
      extra_args+=(--pre-roll "$pre_roll")
    fi
    if "$ROOT/run_benchmark.sh" --dataset boreas_rt --sequence "$sequence" \
         --algorithm "$algorithm" --start-offset 40 --duration 60 --phase holdout \
         "${extra_args[@]}"; then
      printf '[%s] accepted %s / %s\n' "$(date --iso-8601=seconds)" "$sequence" "$algorithm"
    else
      failures+=("$sequence/$algorithm")
      printf '[%s] requires investigation %s / %s\n' \
        "$(date --iso-8601=seconds)" "$sequence" "$algorithm" >&2
    fi
  done
done

if ((${#failures[@]})); then
  printf 'Matrix completed with %d pair(s) requiring investigation:\n' "${#failures[@]}" >&2
  printf '  %s\n' "${failures[@]}" >&2
  exit 1
fi
printf 'All %d route/algorithm pairs accepted.\n' \
  "$(( ${#SEQUENCES[@]} * ${#ALGORITHMS[@]} ))"
