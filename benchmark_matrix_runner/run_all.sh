#!/usr/bin/env bash
set -u

# Benchmark matrix runner folder-only version.
# Put this whole folder inside your codebase root, then run:
#   cd benchmark_matrix_runner
#   ./run_all.sh --algos fastlio2,lvisam --per 0-6 --gps both --timeout-min 30
# It does not modify your codebase.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEBASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

ALGOS="fastlio2,lvisam,fastlivo2,rtabmap,adaptive_w_lvio,orbslam3,r3live"
PERTURBATIONS="0-6"
GPS_MODES="both"
TIMEOUT_MIN=30
MIN_RUNTIME_MIN=20
EVAL=1
BUILD=1
R3LIVE_VIO=1
EXTRA_ARGS=""
LOG_ROOT="$SCRIPT_DIR/logs/$(date +%Y%m%d_%H%M%S)"

usage() {
  cat <<USAGE
Usage:
  ./run_all.sh [options]

Options:
  --codebase PATH          Codebase root. Default: parent folder of this runner.
  --algos LIST            Comma list. Default: $ALGOS
                           Example: fastlio2,lvisam,rtabmap,r3live
  --per LIST              Perturbations. Default: 0-6
                           Examples: 0-6   0,1,2,3   0,2,6
  --gps MODE              both | on | off. Default: both
  --timeout-min N         Max time per run before killing container. Default: $TIMEOUT_MIN
  --min-runtime-min N     Do not move on until this much time has passed. Default: $MIN_RUNTIME_MIN
  --no-build              Do not build algos first
  --no-eval               Do not pass --eval
  --no-r3live-vio         Do not pass --r3live-vio true for r3live
  --extra "ARGS"          Extra args appended to every run command
  -h, --help              Show help

Examples:
  ./run_all.sh
  ./run_all.sh --algos fastlio2,lvisam,rtabmap --per 0-6 --gps both
  ./run_all.sh --algos r3live --per 0 --gps off --timeout-min 35
  ./run_all.sh --no-build --algos adaptive_w_lvio --per 0,1 --gps both
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --codebase) CODEBASE_DIR="$(cd "$2" && pwd)"; shift 2 ;;
    --algos) ALGOS="$2"; shift 2 ;;
    --per) PERTURBATIONS="$2"; shift 2 ;;
    --gps) GPS_MODES="$2"; shift 2 ;;
    --timeout-min) TIMEOUT_MIN="$2"; shift 2 ;;
    --min-runtime-min) MIN_RUNTIME_MIN="$2"; shift 2 ;;
    --no-build) BUILD=0; shift ;;
    --no-eval) EVAL=0; shift ;;
    --no-r3live-vio) R3LIVE_VIO=0; shift ;;
    --extra) EXTRA_ARGS="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 2 ;;
  esac
done

mkdir -p "$LOG_ROOT"
SUMMARY="$LOG_ROOT/summary.tsv"
echo -e "timestamp\talgo\tper\tgps\tstatus\tduration_sec\tlog" > "$SUMMARY"

split_csv() {
  local s="$1"
  s="${s// /}"
  IFS=',' read -ra _items <<< "$s"
  printf '%s\n' "${_items[@]}" | sed '/^$/d'
}

expand_range_list() {
  local s="$1"
  s="${s// /}"
  local part a b i
  IFS=',' read -ra parts <<< "$s"
  for part in "${parts[@]}"; do
    if [[ "$part" =~ ^[0-9]+-[0-9]+$ ]]; then
      a="${part%-*}"; b="${part#*-}"
      if (( a <= b )); then
        for ((i=a;i<=b;i++)); do echo "$i"; done
      else
        for ((i=a;i>=b;i--)); do echo "$i"; done
      fi
    elif [[ "$part" =~ ^[0-9]+$ ]]; then
      echo "$part"
    else
      echo "Invalid --per item: $part" >&2
      exit 2
    fi
  done
}

expand_gps_modes() {
  case "$GPS_MODES" in
    both) printf 'off\non\n' ;;
    on|off) echo "$GPS_MODES" ;;
    *) echo "Invalid --gps: $GPS_MODES. Use both/on/off." >&2; exit 2 ;;
  esac
}

runner_binary() {
  if [[ -x "$CODEBASE_DIR/run" ]]; then
    echo "$CODEBASE_DIR/run"
  elif [[ -x "$CODEBASE_DIR/run.sh" ]]; then
    echo "$CODEBASE_DIR/run.sh"
  else
    echo ""
  fi
}

build_script_for_algo() {
  case "$1" in
    fastlio2|fast-lio2|fast_lio2) echo "build.sh" ;;
    lvisam|lvi_sam|lvi-sam) echo "build_lvisam.sh" ;;
    fastlivo2|fast_livo2|fast-livo2) echo "build_fastlivo2.sh" ;;
    rtabmap|rtab_map|rtab-map) echo "build_rtabmap.sh" ;;
    adaptive_w_lvio|adaptive-w-lvio|adaptive_w) echo "build_adaptive_w_lvio.sh" ;;
    orbslam3|orb_slam3|orb-slam3) echo "build_orbslam3.sh" ;;
    r3live|r3_live|r3-live) echo "build_r3live.sh" ;;
    *) echo "build_${1}.sh" ;;
  esac
}

container_patterns_for_algo() {
  local algo="$1" per="$2"
  case "$algo" in
    fastlio2|fast-lio2|fast_lio2) echo "fastlio2_run_${per}|fast_lio2_run_${per}|fast-lio2_run_${per}" ;;
    lvisam|lvi_sam|lvi-sam) echo "lvisam_run_${per}|lvi_sam_run_${per}" ;;
    fastlivo2|fast_livo2|fast-livo2) echo "fastlivo2_run_${per}|fast_livo2_run_${per}" ;;
    rtabmap|rtab_map|rtab-map) echo "rtabmap_run_${per}|rtab_map_run_${per}" ;;
    adaptive_w_lvio|adaptive-w-lvio|adaptive_w) echo "adaptive_w_lvio_run_${per}|adaptive.*${per}" ;;
    orbslam3|orb_slam3|orb-slam3) echo "orbslam3_run_${per}|orb_slam3_run_${per}" ;;
    r3live|r3_live|r3-live) echo "r3live_run_${per}|r3_live_run_${per}" ;;
    *) echo "${algo}.*${per}" ;;
  esac
}

kill_algo_containers() {
  local algo="$1" per="$2"
  local pat names
  pat="$(container_patterns_for_algo "$algo" "$per")"
  names="$(docker ps -a --format '{{.Names}}' 2>/dev/null | grep -E "$pat" || true)"
  if [[ -n "$names" ]]; then
    echo "$names" | xargs -r docker rm -f >/dev/null 2>&1 || true
  fi
}

build_algos() {
  echo "[matrix] Building selected algos once..."
  while read -r algo; do
    [[ -z "$algo" ]] && continue
    local bs="$CODEBASE_DIR/$(build_script_for_algo "$algo")"
    if [[ -x "$bs" ]]; then
      echo "[matrix] build $algo using $(basename "$bs")"
      (cd "$CODEBASE_DIR" && "$bs") 2>&1 | tee "$LOG_ROOT/build_${algo}.log"
      local code=${PIPESTATUS[0]}
      if [[ $code -ne 0 ]]; then
        echo "[matrix] WARNING: build failed for $algo with code $code. Continuing. See $LOG_ROOT/build_${algo}.log"
      fi
    else
      echo "[matrix] build script not found/executable for $algo: $bs ; skipping build"
    fi
  done < <(split_csv "$ALGOS")
}

make_run_cmd() {
  local algo="$1" per="$2" gps="$3"
  local runner
  runner="$(runner_binary)"
  if [[ -z "$runner" ]]; then
    echo ""
    return
  fi

  local cmd=("$runner" --algo "$algo" --per "$per")

  if [[ "$gps" == "on" ]]; then
    cmd+=(--gps on)
  else
    cmd+=(--gps off)
  fi

  if [[ "$EVAL" -eq 1 ]]; then
    cmd+=(--eval)
  fi

  if [[ "$algo" =~ ^r3live|r3_live|r3-live$ && "$R3LIVE_VIO" -eq 1 ]]; then
    cmd+=(--r3live-vio true)
  fi

  if [[ -n "$EXTRA_ARGS" ]]; then
    # shellcheck disable=SC2206
    local extra=( $EXTRA_ARGS )
    cmd+=("${extra[@]}")
  fi

  printf '%q ' "${cmd[@]}"
}

run_one() {
  local algo="$1" per="$2" gps="$3"
  local start now elapsed status log cmd timeout_sec min_sec pid code
  timeout_sec=$(( TIMEOUT_MIN * 60 ))
  min_sec=$(( MIN_RUNTIME_MIN * 60 ))
  log="$LOG_ROOT/${algo}_per${per}_gps-${gps}.log"
  cmd="$(make_run_cmd "$algo" "$per" "$gps")"
  if [[ -z "$cmd" ]]; then
    echo "[matrix] ERROR: no ./run or ./run.sh found in $CODEBASE_DIR"
    exit 2
  fi

  echo
  echo "[matrix] START algo=$algo per=$per gps=$gps"
  echo "[matrix] CMD: $cmd"
  echo "[matrix] LOG: $log"
  echo "========== START $(date -Is) algo=$algo per=$per gps=$gps ==========" > "$log"
  echo "CMD: $cmd" >> "$log"

  start=$(date +%s)
  (
    cd "$CODEBASE_DIR" || exit 1
    # Use bash -lc so the quoted command generated above is respected.
    bash -lc "$cmd"
  ) >> "$log" 2>&1 &
  pid=$!

  code=""
  while true; do
    now=$(date +%s)
    elapsed=$(( now - start ))

    if ! kill -0 "$pid" 2>/dev/null; then
      wait "$pid"; code=$?
      # If it finished too early, hold before continuing so Docker cleanup/log flushing can settle.
      if (( elapsed < min_sec )); then
        echo "[matrix] process ended before min-runtime; waiting $((min_sec-elapsed)) sec before next run" | tee -a "$log"
        sleep $(( min_sec - elapsed ))
        now=$(date +%s); elapsed=$(( now - start ))
      fi
      if [[ "$code" -eq 0 ]]; then status="OK"; else status="FAILED_$code"; fi
      break
    fi

    if (( elapsed >= timeout_sec )); then
      status="TIMEOUT"
      echo "[matrix] TIMEOUT after ${elapsed}s. Killing process/container for $algo per=$per" | tee -a "$log"
      kill "$pid" 2>/dev/null || true
      sleep 5
      kill -9 "$pid" 2>/dev/null || true
      kill_algo_containers "$algo" "$per"
      wait "$pid" 2>/dev/null || true
      break
    fi

    sleep 30
  done

  kill_algo_containers "$algo" "$per"
  echo "========== END $(date -Is) status=$status elapsed=${elapsed}s ==========" >> "$log"
  echo -e "$(date -Is)\t$algo\t$per\t$gps\t$status\t$elapsed\t$log" >> "$SUMMARY"
  echo "[matrix] END algo=$algo per=$per gps=$gps status=$status elapsed=${elapsed}s"
}

cat <<INFO
[matrix] codebase     : $CODEBASE_DIR
[matrix] algos        : $ALGOS
[matrix] perturbations: $PERTURBATIONS
[matrix] gps          : $GPS_MODES
[matrix] min runtime  : ${MIN_RUNTIME_MIN} min
[matrix] timeout      : ${TIMEOUT_MIN} min
[matrix] eval         : $EVAL
[matrix] build first  : $BUILD
[matrix] logs         : $LOG_ROOT
INFO

if [[ "$BUILD" -eq 1 ]]; then
  build_algos
fi

while read -r algo; do
  [[ -z "$algo" ]] && continue
  while read -r per; do
    [[ -z "$per" ]] && continue
    while read -r gps; do
      [[ -z "$gps" ]] && continue
      run_one "$algo" "$per" "$gps"
    done < <(expand_gps_modes)
  done < <(expand_range_list "$PERTURBATIONS")
done < <(split_csv "$ALGOS")

echo
echo "[matrix] DONE. Summary: $SUMMARY"
column -t -s $'\t' "$SUMMARY" 2>/dev/null || cat "$SUMMARY"
