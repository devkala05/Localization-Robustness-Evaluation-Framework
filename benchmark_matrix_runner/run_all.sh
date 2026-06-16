#!/usr/bin/env bash
set -u
set -o pipefail

# Put this folder inside your codebase root, then run from this folder.
# Builds once per algorithm, then runs all perturbation/GPS combos for that algo.
# No build timeout and no run timeout by default.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEBASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

DEFAULT_ALGOS="fastlio2,lvisam,fastlivo2,rtabmap,adaptive_w_lvio,orbslam3,r3live"
ALGOS="${ALGOS:-$DEFAULT_ALGOS}"
PERS="${PERS:-0-6}"
GPS_MODES="${GPS_MODES:-both}"
DO_BUILD=1
DO_EVAL=1
DRY_RUN=0
MIN_RUN_MIN="${MIN_RUN_MIN:-20}"
MAX_RUN_MIN="${MAX_RUN_MIN:-0}"   # 0 = disabled, never kill due to timeout
BUILD_NO_CACHE=0
EXTRA_RUN_ARGS="${EXTRA_RUN_ARGS:-}"
RUNNER_OVERRIDE="${RUNNER_OVERRIDE:-}"

usage() {
  cat <<'USAGE'
Usage:
  ./run_all.sh [options]

Options:
  --algos a,b,c          Algorithms to run.
                         Default: fastlio2,lvisam,fastlivo2,rtabmap,adaptive_w_lvio,orbslam3,r3live
  --per 0-6              Perturbations. Supports "0-6" or "0,1,2,3".
  --gps both|on|off      GPS modes. Default: both.
  --no-build             Skip builds completely.
  --build-no-cache       Pass --no-cache to each algo build script.
  --no-eval              Do not pass --eval.
  --min-run-min N        Minimum minutes before container-stop check. Default: 20.
  --max-run-min N        Optional hard max minutes per run. Default: 0 = disabled.
                         Use only if you want stuck runs killed. By default nothing is killed.
  --extra-run-args "..." Extra args appended to every run command, e.g. "--headless".
  --dry-run              Print commands only.

Examples:
  ./run_all.sh
  ./run_all.sh --algos fastlio2,lvisam,rtabmap,r3live --per 0-6 --gps both
  ./run_all.sh --no-build --algos r3live --per 0 --gps off
  ./run_all.sh --algos r3live --per 0-6 --gps both --min-run-min 20
USAGE
}

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

parse_range_or_csv() {
  local spec="$1"; local out=()
  if [[ "$spec" =~ ^[0-9]+-[0-9]+$ ]]; then
    local a="${spec%-*}"; local b="${spec#*-}"
    if (( a <= b )); then for ((i=a; i<=b; i++)); do out+=("$i"); done
    else for ((i=a; i>=b; i--)); do out+=("$i"); done; fi
  else
    IFS=',' read -r -a out <<< "$spec"
  fi
  printf '%s\n' "${out[@]}"
}

csv_to_lines() { local spec="$1"; IFS=',' read -r -a arr <<< "$spec"; printf '%s\n' "${arr[@]}"; }

gps_list() {
  case "$GPS_MODES" in
    both) printf '%s\n' off on ;;
    on) printf '%s\n' on ;;
    off) printf '%s\n' off ;;
    *) die "--gps must be both, on, or off" ;;
  esac
}

canon_algo() {
  case "$1" in
    fast_lio2|fast-lio2) echo "fastlio2" ;;
    lvi_sam|lvi-sam) echo "lvisam" ;;
    fast_livo2|fast-livo2) echo "fastlivo2" ;;
    adaptive_w|adaptive-w|adaptive_w_lvio|adaptive-w-lvio) echo "adaptive_w_lvio" ;;
    rtab_map|rtab-map) echo "rtabmap" ;;
    orb_slam3|orb-slam3) echo "orbslam3" ;;
    *) echo "$1" ;;
  esac
}

build_command_for_algo() {
  local algo; algo="$(canon_algo "$1")"
  local no_cache_arg=""; [[ "$BUILD_NO_CACHE" -eq 1 ]] && no_cache_arg=" --no-cache"

  case "$algo" in
    fastlio2)
      if [[ -x "$CODEBASE_DIR/build_fastlio2.sh" ]]; then echo "./build_fastlio2.sh${no_cache_arg}"
      elif [[ -x "$CODEBASE_DIR/build.sh" ]]; then echo "./build.sh${no_cache_arg}"
      else echo ""; fi ;;
    lvisam) [[ -x "$CODEBASE_DIR/build_lvisam.sh" ]] && echo "./build_lvisam.sh${no_cache_arg}" || echo "" ;;
    fastlivo2) [[ -x "$CODEBASE_DIR/build_fastlivo2.sh" ]] && echo "./build_fastlivo2.sh${no_cache_arg}" || echo "" ;;
    rtabmap) [[ -x "$CODEBASE_DIR/build_rtabmap.sh" ]] && echo "./build_rtabmap.sh${no_cache_arg}" || echo "" ;;
    adaptive_w_lvio) [[ -x "$CODEBASE_DIR/build_adaptive_w_lvio.sh" ]] && echo "./build_adaptive_w_lvio.sh${no_cache_arg}" || echo "" ;;
    r3live) [[ -x "$CODEBASE_DIR/build_r3live.sh" ]] && echo "./build_r3live.sh${no_cache_arg}" || echo "" ;;
    orbslam3)
      if [[ -x "$CODEBASE_DIR/build_orbslam3.sh" ]]; then echo "./build_orbslam3.sh${no_cache_arg}"
      elif [[ -x "$CODEBASE_DIR/build_orb_slam3.sh" ]]; then echo "./build_orb_slam3.sh${no_cache_arg}"
      else echo ""; fi ;;
    *) [[ -x "$CODEBASE_DIR/build_${algo}.sh" ]] && echo "./build_${algo}.sh${no_cache_arg}" || echo "" ;;
  esac
}

runner_path() {
  if [[ -n "$RUNNER_OVERRIDE" ]]; then echo "$RUNNER_OVERRIDE"
  elif [[ -x "$CODEBASE_DIR/run" ]]; then echo "./run"
  elif [[ -x "$CODEBASE_DIR/run.sh" ]]; then echo "./run.sh"
  else echo ""; fi
}

run_command_for_algo() {
  local algo="$1"; local per="$2"; local gps="$3"; local runner
  runner="$(runner_path)"; [[ -z "$runner" ]] && die "No ./run or ./run.sh found in codebase root: $CODEBASE_DIR"
  local eval_arg=""; [[ "$DO_EVAL" -eq 1 ]] && eval_arg=" --eval"
  local vio_arg=""; [[ "$(canon_algo "$algo")" == "r3live" ]] && vio_arg=" --r3live-vio true"
  echo "$runner --algo $(canon_algo "$algo") --per $per --gps $gps${vio_arg}${eval_arg}${EXTRA_RUN_ARGS:+ $EXTRA_RUN_ARGS}"
}

container_name_candidates() {
  local algo="$1"; local per="$2"; local a; a="$(canon_algo "$algo")"
  case "$a" in
    fastlio2) printf '%s\n' "fastlio2_run_${per}" "fast_lio2_run_${per}" ;;
    lvisam) printf '%s\n' "lvisam_run_${per}" "lvi_sam_run_${per}" ;;
    fastlivo2) printf '%s\n' "fastlivo2_run_${per}" "fast_livo2_run_${per}" ;;
    rtabmap) printf '%s\n' "rtabmap_run_${per}" "rtab_map_run_${per}" ;;
    adaptive_w_lvio) printf '%s\n' "adaptive_w_lvio_run_${per}" "adaptive_w_run_${per}" ;;
    r3live) printf '%s\n' "r3live_run_${per}" ;;
    orbslam3) printf '%s\n' "orbslam3_run_${per}" "orb_slam3_run_${per}" ;;
    *) printf '%s\n' "${a}_run_${per}" ;;
  esac
}

running_containers_for() {
  local algo="$1"; local per="$2"; local names=()
  while IFS= read -r candidate; do
    [[ -z "$candidate" ]] && continue
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -Fxq "$candidate"; then names+=("$candidate"); fi
  done < <(container_name_candidates "$algo" "$per")
  local a; a="$(canon_algo "$algo")"
  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    if [[ "$name" == *"$a"* && "$name" == *"run"* && "$name" == *"$per"* ]]; then names+=("$name"); fi
  done < <(docker ps --format '{{.Names}}' 2>/dev/null || true)
  printf '%s\n' "${names[@]}" | awk 'NF && !seen[$0]++'
}

wait_for_run_to_finish() {
  local algo="$1"; local per="$2"; local start_epoch="$3"
  local min_sec=$(( MIN_RUN_MIN * 60 )); local max_sec=$(( MAX_RUN_MIN * 60 ))
  while true; do
    local now elapsed; now="$(date +%s)"; elapsed=$(( now - start_epoch ))
    mapfile -t running < <(running_containers_for "$algo" "$per")
    if (( ${#running[@]} == 0 )); then
      if (( elapsed < min_sec )); then log "No matching Docker container is running for $algo per=$per after ${elapsed}s. Continuing because run command already returned."; fi
      return 0
    fi
    log "Still running: ${running[*]} elapsed=$((elapsed/60))min. Waiting; no timeout is enforced by default."
    if (( max_sec > 0 && elapsed >= max_sec )); then
      log "Max runtime reached (${MAX_RUN_MIN}min). Killing containers: ${running[*]}"
      docker rm -f "${running[@]}" >/dev/null 2>&1 || true
      return 124
    fi
    sleep 60
  done
}

run_logged() {
  local label="$1"; local cmd="$2"; local log_file="$3"
  log "START $label"; log "CMD: $cmd"; mkdir -p "$(dirname "$log_file")"
  if [[ "$DRY_RUN" -eq 1 ]]; then echo "[DRY-RUN] $cmd" | tee -a "$log_file"; return 0; fi
  ( cd "$CODEBASE_DIR" || exit 1; stdbuf -oL -eL bash -lc "$cmd" ) 2>&1 | tee "$log_file"
  local status=${PIPESTATUS[0]}
  log "END $label status=$status"
  return "$status"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --algos) ALGOS="$2"; shift 2 ;;
    --per) PERS="$2"; shift 2 ;;
    --gps) GPS_MODES="$2"; shift 2 ;;
    --no-build) DO_BUILD=0; shift ;;
    --build-no-cache) BUILD_NO_CACHE=1; shift ;;
    --no-eval) DO_EVAL=0; shift ;;
    --min-run-min) MIN_RUN_MIN="$2"; shift 2 ;;
    --max-run-min) MAX_RUN_MIN="$2"; shift 2 ;;
    --extra-run-args) EXTRA_RUN_ARGS="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
done

[[ -d "$CODEBASE_DIR" ]] || die "Codebase root not found: $CODEBASE_DIR"
[[ "$MIN_RUN_MIN" =~ ^[0-9]+$ ]] || die "--min-run-min must be integer minutes"
[[ "$MAX_RUN_MIN" =~ ^[0-9]+$ ]] || die "--max-run-min must be integer minutes"

RUN_ID="$(date '+%Y%m%d_%H%M%S')"
OUT_DIR="$CODEBASE_DIR/data/batch_runs/$RUN_ID"
LOG_DIR="$OUT_DIR/logs"
SUMMARY="$OUT_DIR/summary.tsv"
mkdir -p "$LOG_DIR"
printf 'timestamp\talgo\tper\tgps\tphase\tstatus\tlog\n' > "$SUMMARY"

log "Codebase: $CODEBASE_DIR"
log "Run ID:   $RUN_ID"
log "Algos:    $ALGOS"
log "Pers:     $PERS"
log "GPS:      $GPS_MODES"
log "Build:    $DO_BUILD (once per algo)"
log "Eval:     $DO_EVAL"
log "Min run:  ${MIN_RUN_MIN}min"
if (( MAX_RUN_MIN == 0 )); then log "Max run:  disabled"; else log "Max run:  ${MAX_RUN_MIN}min"; fi
log "Logs:     $LOG_DIR"

mapfile -t ALGO_LIST < <(csv_to_lines "$ALGOS")
mapfile -t PER_LIST < <(parse_range_or_csv "$PERS")
mapfile -t GPS_LIST < <(gps_list)
overall_status=0

for raw_algo in "${ALGO_LIST[@]}"; do
  algo="$(canon_algo "$raw_algo")"; [[ -z "$algo" ]] && continue
  log "========== ALGO START: $algo =========="
  if [[ "$DO_BUILD" -eq 1 ]]; then
    build_cmd="$(build_command_for_algo "$algo")"
    if [[ -z "$build_cmd" ]]; then
      log "No build script found for $algo. Skipping build, continuing to runs."
      printf '%s\t%s\t-\t-\tbuild\tskipped\t-\n' "$(date '+%F %T')" "$algo" >> "$SUMMARY"
    else
      build_log="$LOG_DIR/${algo}__build.log"
      if run_logged "BUILD $algo" "$build_cmd" "$build_log"; then
        printf '%s\t%s\t-\t-\tbuild\t0\t%s\n' "$(date '+%F %T')" "$algo" "$build_log" >> "$SUMMARY"
      else
        status=$?
        printf '%s\t%s\t-\t-\tbuild\t%s\t%s\n' "$(date '+%F %T')" "$algo" "$status" "$build_log" >> "$SUMMARY"
        log "Build failed for $algo. Skipping all runs for this algo."
        overall_status=1
        continue
      fi
    fi
  fi

  # Runs are grouped under the same algorithm, so no rebuild happens when only per/gps changes.
  for per in "${PER_LIST[@]}"; do
    [[ -z "$per" ]] && continue
    for gps in "${GPS_LIST[@]}"; do
      run_cmd="$(run_command_for_algo "$algo" "$per" "$gps")"
      run_log="$LOG_DIR/${algo}__per_${per}__gps_${gps}.log"
      start_epoch="$(date +%s)"
      if run_logged "RUN $algo per=$per gps=$gps" "$run_cmd" "$run_log"; then run_status=0; else run_status=$?; overall_status=1; fi
      wait_for_run_to_finish "$algo" "$per" "$start_epoch" || true
      printf '%s\t%s\t%s\t%s\trun\t%s\t%s\n' "$(date '+%F %T')" "$algo" "$per" "$gps" "$run_status" "$run_log" >> "$SUMMARY"
      log "Finished combo: algo=$algo per=$per gps=$gps status=$run_status"
    done
  done
  log "========== ALGO END: $algo =========="
done

log "All requested jobs completed. Summary: $SUMMARY"
exit "$overall_status"
