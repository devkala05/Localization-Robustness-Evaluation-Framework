#!/usr/bin/env bash
set -euo pipefail

# Runs the full UrbanNav benchmark matrix sequentially:
#   perturbations 0..6 × GPS off/on × selected algorithms
#
# Examples:
#   ./run_benchmark_matrix.sh
#   ./run_benchmark_matrix.sh --algos fastlio2,lvisam,rtabmap,r3live
#   ALGOS="fastlio2 lvisam" GPS_MODES="off on" PERS="0 1 2" ./run_benchmark_matrix.sh
#   ./run_benchmark_matrix.sh --algos r3live --per 0-6 --gps both --timeout-min 25
#
# Defaults are safe for unattended overnight runs:
#   - builds each selected algorithm once before running it
#   - runs without RViz windows
#   - uses --eval
#   - continues after failed runs and records status in data/batch_runs/<timestamp>/summary.tsv

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

DEFAULT_ALGOS="fastlio2 lvisam fastlivo2 rtabmap adaptive_w_lvio orbslam3 r3live"
ALGOS="${ALGOS:-${DEFAULT_ALGOS}}"
PERS="${PERS:-0 1 2 3 4 5 6}"
GPS_MODES="${GPS_MODES:-off on}"
BUILD_FIRST="${BUILD_FIRST:-true}"
RUN_EVAL="${RUN_EVAL:-true}"
CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-true}"
LAUNCH_RVIZ="${LAUNCH_RVIZ:-false}"
RUN_TIMEOUT_MIN="${RUN_TIMEOUT_MIN:-25}"
BAG_RATE="${BAG_RATE:-0.35}"
GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG:-0.0}"
R3LIVE_VIO="${R3LIVE_VIO:-true}"
EXTRA_RUN_ARGS="${EXTRA_RUN_ARGS:-}"
BATCH_TAG="${BATCH_TAG:-$(date +%Y%m%d_%H%M%S)}"
LOG_ROOT="${LOG_ROOT:-${SCRIPT_DIR}/data/batch_runs/${BATCH_TAG}}"
SUMMARY_FILE="${LOG_ROOT}/summary.tsv"

usage() {
  cat <<'USAGE'
UrbanNav full benchmark matrix runner

Usage:
  ./run_benchmark_matrix.sh [options]

Options:
  --algos LIST          Algorithms to run. Comma or space separated.
                        Default: fastlio2,lvisam,fastlivo2,rtabmap,adaptive_w_lvio,orbslam3,r3live
  --per LIST            Perturbations. Examples: 0-6, 0,1,2, "0 3 6". Default: 0-6
  --gps off|on|both     GPS modes. Default: both
  --timeout-min N       Max wall-clock minutes per run before killing container. Default: 25
  --no-build            Do not run build_<algo>.sh before matrix
  --build              Build selected algorithms once before running them. Default
  --no-eval             Run without --eval
  --with-rviz           Show RViz during batch runs. Default is headless/no RViz
  --stop-on-error       Stop entire batch on first failed run
  --bag-rate R          rosbag playback rate. Default: 0.35
  --extra-args "..."    Extra args appended to every ./run command
  -h, --help            Show this help

Environment overrides:
  ALGOS="fastlio2 lvisam" PERS="0 1 2" GPS_MODES="off on" ./run_benchmark_matrix.sh
  BUILD_FIRST=false RUN_TIMEOUT_MIN=30 LAUNCH_RVIZ=false ./run_benchmark_matrix.sh

Outputs:
  data/batch_runs/<timestamp>/summary.tsv
  data/batch_runs/<timestamp>/logs/*.log
USAGE
}

normalize_list() {
  # Converts comma-separated list to space-separated list.
  echo "$1" | tr ',' ' ' | xargs
}

expand_pers() {
  local input="$(normalize_list "$1")"
  local out=()
  local item start end i
  for item in ${input}; do
    if [[ "${item}" =~ ^([0-6])-([0-6])$ ]]; then
      start="${BASH_REMATCH[1]}"; end="${BASH_REMATCH[2]}"
      if (( start <= end )); then
        for ((i=start; i<=end; i++)); do out+=("$i"); done
      else
        for ((i=start; i>=end; i--)); do out+=("$i"); done
      fi
    elif [[ "${item}" =~ ^[0-6]$ ]]; then
      out+=("${item}")
    else
      echo "ERROR: invalid --per item '${item}'. Use 0..6 or range like 0-6." >&2
      exit 2
    fi
  done
  printf '%s ' "${out[@]}"
}

canonical_algo() {
  case "$1" in
    fastlio2|fast_lio2|fast-lio2) echo "fastlio2" ;;
    lvisam|lvi_sam|lvi-sam) echo "lvisam" ;;
    fastlivo2|fast_livo2|fast-livo2) echo "fastlivo2" ;;
    rtabmap|rtab_map|rtab-map) echo "rtabmap" ;;
    adaptive_w_lvio|adaptive|adaptive-w|adaptive_w) echo "adaptive_w_lvio" ;;
    orbslam3|orb_slam3|orb-slam3) echo "orbslam3" ;;
    r3live|r3_live|r3-live) echo "r3live" ;;
    *) echo "" ;;
  esac
}

build_script_for_algo() {
  case "$1" in
    fastlio2) echo "./build_fastlio2.sh" ;;
    lvisam) echo "./build_lvisam.sh" ;;
    fastlivo2) echo "./build_fastlivo2.sh" ;;
    rtabmap) echo "./build_rtabmap.sh" ;;
    adaptive_w_lvio) echo "./build_adaptive_w_lvio.sh" ;;
    orbslam3) echo "./build_orbslam3.sh" ;;
    r3live) echo "./build_r3live.sh" ;;
  esac
}

result_id_for_algo() {
  case "$1" in
    fastlio2) echo "fast_lio2" ;;
    lvisam) echo "lvi_sam" ;;
    fastlivo2) echo "fast_livo2" ;;
    rtabmap) echo "rtab_map" ;;
    adaptive_w_lvio) echo "adaptive_w_lvio" ;;
    orbslam3) echo "orb_slam3" ;;
    r3live) echo "r3live" ;;
  esac
}

container_for_algo_per() {
  echo "$1_run_$2"
}

kill_container_if_running() {
  local container="$1"
  if docker ps --format '{{.Names}}' | grep -qx "${container}"; then
    echo "[matrix] container still running after timeout/error; killing ${container}"
    docker rm -f "${container}" >/dev/null 2>&1 || true
  fi
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --algos) ALGOS="$(normalize_list "${2:-}")"; shift 2 ;;
    --algos=*) ALGOS="$(normalize_list "${1#*=}")"; shift ;;
    --per|--pers|--perturbations) PERS="$(expand_pers "${2:-}")"; shift 2 ;;
    --per=*|--pers=*|--perturbations=*) PERS="$(expand_pers "${1#*=}")"; shift ;;
    --gps) case "${2:-}" in both) GPS_MODES="off on" ;; off|on) GPS_MODES="${2}" ;; *) echo "ERROR: --gps must be off/on/both" >&2; exit 2 ;; esac; shift 2 ;;
    --gps=*) v="${1#*=}"; case "${v}" in both) GPS_MODES="off on" ;; off|on) GPS_MODES="${v}" ;; *) echo "ERROR: --gps must be off/on/both" >&2; exit 2 ;; esac; shift ;;
    --timeout-min) RUN_TIMEOUT_MIN="${2:-}"; shift 2 ;;
    --timeout-min=*) RUN_TIMEOUT_MIN="${1#*=}"; shift ;;
    --no-build) BUILD_FIRST="false"; shift ;;
    --build) BUILD_FIRST="true"; shift ;;
    --no-eval) RUN_EVAL="false"; shift ;;
    --with-rviz) LAUNCH_RVIZ="true"; shift ;;
    --headless|--no-rviz) LAUNCH_RVIZ="false"; shift ;;
    --stop-on-error) CONTINUE_ON_ERROR="false"; shift ;;
    --continue-on-error) CONTINUE_ON_ERROR="true"; shift ;;
    --bag-rate) BAG_RATE="${2:-}"; shift 2 ;;
    --bag-rate=*) BAG_RATE="${1#*=}"; shift ;;
    --extra-args) EXTRA_RUN_ARGS="${2:-}"; shift 2 ;;
    --extra-args=*) EXTRA_RUN_ARGS="${1#*=}"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "ERROR: unknown argument $1" >&2; usage; exit 2 ;;
  esac
done

if ! [[ "${RUN_TIMEOUT_MIN}" =~ ^[0-9]+$ ]] || [ "${RUN_TIMEOUT_MIN}" -lt 1 ]; then
  echo "ERROR: --timeout-min must be a positive integer" >&2
  exit 2
fi

# Canonicalize algorithms and remove duplicates while preserving order.
CANON_ALGOS=()
for raw in $(normalize_list "${ALGOS}"); do
  canon="$(canonical_algo "${raw}")"
  if [ -z "${canon}" ]; then
    echo "ERROR: unknown algorithm '${raw}'" >&2
    echo "Allowed: ${DEFAULT_ALGOS}" >&2
    exit 2
  fi
  seen=false
  for a in "${CANON_ALGOS[@]:-}"; do [ "$a" = "$canon" ] && seen=true; done
  [ "$seen" = false ] && CANON_ALGOS+=("${canon}")
done

PERS="$(expand_pers "${PERS}")"
GPS_MODES="$(normalize_list "${GPS_MODES}")"

mkdir -p "${LOG_ROOT}/logs"
printf "timestamp\talgo\tper\tgps\tstatus\texit_code\tduration_sec\tlog\tresult_latest\n" > "${SUMMARY_FILE}"

TOTAL=$(( ${#CANON_ALGOS[@]} * $(wc -w <<<"${PERS}") * $(wc -w <<<"${GPS_MODES}") ))
COUNT=0

echo "[matrix] algorithms: ${CANON_ALGOS[*]}"
echo "[matrix] perturbations: ${PERS}"
echo "[matrix] gps modes: ${GPS_MODES}"
echo "[matrix] build_first=${BUILD_FIRST} eval=${RUN_EVAL} rviz=${LAUNCH_RVIZ} timeout=${RUN_TIMEOUT_MIN}m bag_rate=${BAG_RATE}"
echo "[matrix] logs=${LOG_ROOT}"
echo "[matrix] total_runs=${TOTAL}"

# Export once for all runs. run_algorithm_container.sh forwards these into Docker.
export BAG_RATE GT_YAW_OFFSET_DEG LAUNCH_RVIZ

for algo in "${CANON_ALGOS[@]}"; do
  if [ "${BUILD_FIRST}" = "true" ]; then
    build_script="$(build_script_for_algo "${algo}")"
    build_log="${LOG_ROOT}/logs/build_${algo}.log"
    echo "[matrix] building ${algo} using ${build_script}"
    if ! bash -lc "${build_script}" > >(tee "${build_log}") 2>&1; then
      echo "[matrix] BUILD_FAILED algo=${algo} log=${build_log}"
      if [ "${CONTINUE_ON_ERROR}" = "true" ]; then
        continue
      else
        exit 1
      fi
    fi
  fi

  for gps in ${GPS_MODES}; do
    for per in ${PERS}; do
      COUNT=$((COUNT + 1))
      result_id="$(result_id_for_algo "${algo}")"
      container="$(container_for_algo_per "${algo}" "${per}")"
      stamp="$(date +%Y%m%d_%H%M%S)"
      log_file="${LOG_ROOT}/logs/${stamp}_${COUNT}_${algo}_per${per}_gps-${gps}.log"
      latest="${SCRIPT_DIR}/data/results/${result_id}/per_${per}/trajectory.csv"
      eval_arg=()
      [ "${RUN_EVAL}" = "true" ] && eval_arg=(--eval)
      r3live_arg=()
      [ "${algo}" = "r3live" ] && r3live_arg=(--r3live-vio "${R3LIVE_VIO}")

      cmd=(./run --algo "${algo}" --per "${per}" --gps "${gps}" "${eval_arg[@]}" "${r3live_arg[@]}")
      if [ -n "${EXTRA_RUN_ARGS}" ]; then
        # shellcheck disable=SC2206
        extra=( ${EXTRA_RUN_ARGS} )
        cmd+=("${extra[@]}")
      fi

      echo ""
      echo "[matrix] [$COUNT/$TOTAL] START algo=${algo} per=${per} gps=${gps}"
      echo "[matrix] command: ${cmd[*]}"
      start_epoch="$(date +%s)"
      status="OK"
      exit_code=0

      set +e
      timeout --foreground "${RUN_TIMEOUT_MIN}m" "${cmd[@]}" > >(tee "${log_file}") 2>&1
      exit_code=$?
      set -e

      end_epoch="$(date +%s)"
      duration=$((end_epoch - start_epoch))

      if [ "${exit_code}" -eq 124 ]; then
        status="TIMEOUT"
        kill_container_if_running "${container}"
      elif [ "${exit_code}" -ne 0 ]; then
        status="FAILED"
        kill_container_if_running "${container}"
      else
        status="OK"
        # If the command returned cleanly but Docker somehow remained, clean it before next run.
        kill_container_if_running "${container}"
      fi

      printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
        "$(date +%Y-%m-%dT%H:%M:%S)" "${algo}" "${per}" "${gps}" "${status}" "${exit_code}" "${duration}" "${log_file}" "${latest}" \
        >> "${SUMMARY_FILE}"

      echo "[matrix] END algo=${algo} per=${per} gps=${gps} status=${status} exit=${exit_code} duration=${duration}s"
      echo "[matrix] log=${log_file}"

      if [ "${status}" != "OK" ] && [ "${CONTINUE_ON_ERROR}" != "true" ]; then
        echo "[matrix] stopping on first error. Summary: ${SUMMARY_FILE}"
        exit "${exit_code}"
      fi

      sleep 5
    done
  done
done

echo ""
echo "[matrix] complete"
echo "[matrix] summary=${SUMMARY_FILE}"
column -t -s $'\t' "${SUMMARY_FILE}" || cat "${SUMMARY_FILE}"
