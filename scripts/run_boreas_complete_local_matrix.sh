#!/usr/bin/env bash
# Run every native algorithm over every full camera/LiDAR interval available
# locally.  This deliberately uses no scoring-window offset, duration cap, or
# pre-roll: the full recorded joint interval is both replayed and evaluated.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEQUENCES=(
  boreas_2024_12_04_14_44
  boreas_2025_07_18_15_30_farm_complete_local
  boreas_2025_07_18_11_53_forest_complete_local
  boreas_2025_08_06_06_33_urban_complete_local
)
ALGORITHMS=(fastlio2 fastlivo2 lvisam orbslam3 rtabmap)

if (($#)); then SEQUENCES=("$@"); fi

failures=()
for sequence in "${SEQUENCES[@]}"; do
  for algorithm in "${ALGORITHMS[@]}"; do
    printf '\n[%s] starting complete local interval: %s / %s\n' \
      "$(date --iso-8601=seconds)" "$sequence" "$algorithm"
    if "$ROOT/run_benchmark.sh" --dataset boreas_rt --sequence "$sequence" \
         --algorithm "$algorithm" --start-offset 0 --duration 0 --phase production; then
      printf '[%s] accepted %s / %s\n' "$(date --iso-8601=seconds)" "$sequence" "$algorithm"
    else
      failures+=("$sequence/$algorithm")
      printf '[%s] requires investigation %s / %s\n' \
        "$(date --iso-8601=seconds)" "$sequence" "$algorithm" >&2
    fi
  done
done

if ((${#failures[@]})); then
  printf 'Complete-local matrix finished with %d pair(s) requiring investigation:\n' \
    "${#failures[@]}" >&2
  printf '  %s\n' "${failures[@]}" >&2
  exit 1
fi
printf 'All %d complete-local route/algorithm pairs accepted.\n' \
  "$(( ${#SEQUENCES[@]} * ${#ALGORITHMS[@]} ))"
