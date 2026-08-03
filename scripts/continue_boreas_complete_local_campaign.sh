#!/usr/bin/env bash
# Resume a complete-local Boreas campaign after a foreground terminal detaches.
# The optional PID is an already-running run_benchmark.sh child; it is allowed
# to finish before this controller executes the remaining, non-duplicated cells.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACTIVE_PID="${1:-}"
if [[ -n "$ACTIVE_PID" ]]; then
  [[ "$ACTIVE_PID" =~ ^[0-9]+$ ]] || { echo "invalid active PID: $ACTIVE_PID" >&2; exit 2; }
  while kill -0 "$ACTIVE_PID" 2>/dev/null; do
    printf '[%s] waiting for active native run PID %s\n' "$(date --iso-8601=seconds)" "$ACTIVE_PID"
    sleep 30
  done
fi

declare -a JOBS=(
  'boreas_2024_12_04_14_44 orbslam3'
  'boreas_2024_12_04_14_44 rtabmap'
  'boreas_2025_07_18_15_30_farm_complete_local fastlio2'
  'boreas_2025_07_18_15_30_farm_complete_local fastlivo2'
  'boreas_2025_07_18_15_30_farm_complete_local lvisam'
  'boreas_2025_07_18_15_30_farm_complete_local orbslam3'
  'boreas_2025_07_18_15_30_farm_complete_local rtabmap'
  'boreas_2025_07_18_11_53_forest_complete_local fastlio2'
  'boreas_2025_07_18_11_53_forest_complete_local fastlivo2'
  'boreas_2025_07_18_11_53_forest_complete_local lvisam'
  'boreas_2025_07_18_11_53_forest_complete_local orbslam3'
  'boreas_2025_07_18_11_53_forest_complete_local rtabmap'
  'boreas_2025_08_06_06_33_urban_complete_local fastlio2'
  'boreas_2025_08_06_06_33_urban_complete_local fastlivo2'
  'boreas_2025_08_06_06_33_urban_complete_local lvisam'
  'boreas_2025_08_06_06_33_urban_complete_local orbslam3'
  'boreas_2025_08_06_06_33_urban_complete_local rtabmap'
)

failures=()
for job in "${JOBS[@]}"; do
  read -r sequence algorithm <<<"$job"
  printf '[%s] starting complete-local %s / %s\n' \
    "$(date --iso-8601=seconds)" "$sequence" "$algorithm"
  if "$ROOT/run_benchmark.sh" --dataset boreas_rt --sequence "$sequence" \
       --algorithm "$algorithm" --start-offset 0 --duration 0 --phase production; then
    printf '[%s] accepted %s / %s\n' \
      "$(date --iso-8601=seconds)" "$sequence" "$algorithm"
  else
    failures+=("$sequence/$algorithm")
    printf '[%s] requires investigation %s / %s\n' \
      "$(date --iso-8601=seconds)" "$sequence" "$algorithm" >&2
  fi
done

OUT="$ROOT/results/boreas_rt/complete_local_benchmark"
mkdir -p "$OUT"
if ((${#failures[@]})); then
  printf 'Complete-local campaign has %d failed/rejected cell(s):\n' "${#failures[@]}" >&2
  printf '  %s\n' "${failures[@]}" >&2
  printf '%s\n' "${failures[@]}" >"$OUT/requires_investigation.txt"
  exit 1
fi

python3 "$ROOT/tools/generate_boreas_route_report.py"
python3 "$ROOT/tools/generate_repository_implementation_pdf.py"
printf 'Complete-local campaign and both PDFs finished successfully.\n'
