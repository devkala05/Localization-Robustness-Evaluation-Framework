#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="${PERTURBATION_CONFIG:-$ROOT/robustness/config/alive_perturbations.yaml}"
ORIGINAL="${ALIVE_ORIGINAL_BAG:-}"
GT="${ALIVE_GROUND_TRUTH:-}"
RESULTS="$ROOT/robustness/results"
ALGORITHMS=(fastlivo2 fastlio2 lvisam floam orbslam3 rtabmap)
SCENARIOS=(baseline rain fog sensor_degradation)
ONLY_ALGORITHM=""; ONLY_SCENARIO=""; SKIP_EXISTING=false

usage() {
  cat <<'EOF'
Usage: ./robustness/run_alive_matrix.sh [options]
  --algorithm NAME       Run only one of the six algorithms
  --scenario NAME        baseline|rain|fog|sensor_degradation
  --skip-existing        Keep an existing completed campaign pair

Environment: ALIVE_ORIGINAL_BAG, ALIVE_GROUND_TRUTH, PERTURBATION_CONFIG,
             BAG_RATE, BENCHMARK_ROS_MASTER_PORT
EOF
}

while (($#)); do
  case "$1" in
    --algorithm) ONLY_ALGORITHM="${2:-}"; shift 2 ;;
    --scenario) ONLY_SCENARIO="${2:-}"; shift 2 ;;
    --skip-existing) SKIP_EXISTING=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -n "$ONLY_ALGORITHM" && " ${ALGORITHMS[*]} " != *" $ONLY_ALGORITHM "* ]]; then
  printf 'Unknown algorithm: %s\n' "$ONLY_ALGORITHM" >&2; exit 2
fi
if [[ -n "$ONLY_SCENARIO" && " ${SCENARIOS[*]} " != *" $ONLY_SCENARIO "* ]]; then
  printf 'Unknown scenario: %s\n' "$ONLY_SCENARIO" >&2; exit 2
fi

[[ -f "$CONFIG" ]] || { printf 'Missing perturbation config: %s\n' "$CONFIG" >&2; exit 2; }
mapfile -t configured_paths < <(python3 - "$CONFIG" <<'PY'
import sys, yaml
config = yaml.safe_load(open(sys.argv[1]))
print(config["input_bag"])
print(config["evaluation"]["ground_truth"])
PY
)
ORIGINAL="${ORIGINAL:-${configured_paths[0]}}"
GT="${GT:-${configured_paths[1]}}"
[[ -f "$ORIGINAL" && -f "$GT" ]] || {
  printf 'Missing config, original bag, or reference trajectory.\n' >&2; exit 2;
}
mkdir -p "$RESULTS"
CAMPAIGN_ID="${CAMPAIGN_ID:-$(date +%Y%m%d_%H%M%S)}"
INDEX="$RESULTS/${CAMPAIGN_ID}_runs.tsv"
printf 'scenario\talgorithm\trun_id\tstatus\trun_directory\n' > "$INDEX"
failures=0

for scenario in "${SCENARIOS[@]}"; do
  [[ -z "$ONLY_SCENARIO" || "$scenario" == "$ONLY_SCENARIO" ]] || continue
  bag="$ORIGINAL"
  for algorithm in "${ALGORITHMS[@]}"; do
    [[ -z "$ONLY_ALGORITHM" || "$algorithm" == "$ONLY_ALGORITHM" ]] || continue
    run_id="${CAMPAIGN_ID}_${scenario}_${algorithm}"
    run_dir="$ROOT/results/alive/one_full_loop/$algorithm/$run_id"
    if [[ "$SKIP_EXISTING" == true && -f "$run_dir/execution_status.json" ]]; then
      status=existing
    else
      rate="${BAG_RATE:-}"
      if [[ -z "$rate" ]]; then
        case "$algorithm" in
          fastlivo2) rate=0.5 ;; fastlio2) rate=1.0 ;; lvisam) rate=0.20 ;;
          floam) rate=0.5 ;; orbslam3) rate=0.15 ;; rtabmap) rate=0.15 ;;
        esac
      fi
      printf '[campaign] scenario=%s algorithm=%s rate=%s\n' "$scenario" "$algorithm" "$rate"
      if BENCHMARK_RUN_ID="$run_id" "$ROOT/run_benchmark.sh" \
          --dataset alive --sequence one_full_loop --algorithm "$algorithm" \
          --input-bag "$bag" --ground-truth "$GT" --scenario "$scenario" \
          --rate "$rate" --phase production; then
        status=accepted
      else
        status=requires_review
        failures=$((failures + 1))
      fi
    fi
    printf '%s\t%s\t%s\t%s\t%s\n' "$scenario" "$algorithm" "$run_id" "$status" "$run_dir" >> "$INDEX"
  done
done

printf 'Campaign index: %s\n' "$INDEX"
if ((failures)); then
  printf '%d run(s) completed execution or quality checks unsuccessfully; they remain recorded for failure analysis.\n' "$failures" >&2
fi
exit 0
