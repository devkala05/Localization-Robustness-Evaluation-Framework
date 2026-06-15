#!/usr/bin/env bash
set -euo pipefail
export E2O_EVAL_ROOT="${E2O_EVAL_ROOT:-/workspace/e2o_eval}"
cd "$E2O_EVAL_ROOT"

source /opt/ros/noetic/setup.bash
if [[ ! -f catkin_ws/devel/setup.bash ]]; then
  echo "[entrypoint] Building catkin workspace..."
  (cd catkin_ws && catkin_make)
fi
source catkin_ws/devel/setup.bash

MODE="${1:-shell}"
shift || true

find_bag_in_container() {
  local requested="${1:-}"
  if [[ -n "$requested" ]]; then
    if [[ -f "$requested" ]]; then realpath "$requested"; return 0; fi
    if [[ -f "$E2O_EVAL_ROOT/$requested" ]]; then realpath "$E2O_EVAL_ROOT/$requested"; return 0; fi
    if [[ -f "$E2O_EVAL_ROOT/data/$requested" ]]; then realpath "$E2O_EVAL_ROOT/data/$requested"; return 0; fi
    if [[ -f "$E2O_EVAL_ROOT/data/raw/$requested" ]]; then realpath "$E2O_EVAL_ROOT/data/raw/$requested"; return 0; fi
    echo "ERROR: bag not found inside container: $requested" >&2
    exit 2
  fi
  mapfile -t bags < <(find "$E2O_EVAL_ROOT/data" -type f -name '*.bag' | sort)
  if [[ ${#bags[@]} -eq 0 ]]; then
    echo "ERROR: no .bag under data/. Copy it to data/raw/<any_name>.bag" >&2
    exit 3
  elif [[ ${#bags[@]} -gt 1 ]]; then
    echo "ERROR: multiple .bag files found. Use --bag <name-or-path>." >&2
    printf '  %s\n' "${bags[@]}" >&2
    exit 4
  fi
  realpath "${bags[0]}"
}

resolve_file_in_container() {
  local requested="$1"
  local label="${2:-file}"
  if [[ -f "$requested" ]]; then realpath "$requested"; return 0; fi
  if [[ -f "$E2O_EVAL_ROOT/$requested" ]]; then realpath "$E2O_EVAL_ROOT/$requested"; return 0; fi
  echo "ERROR: $label not found inside container: $requested" >&2
  exit 2
}

BAG_ARG=""
GT_TOPIC="auto"
GT_TUM=""
EST_TUM=""
RATE="1.0"
RVIZ="true"
EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --bag) BAG_ARG="$2"; shift 2 ;;
    --gt-topic) GT_TOPIC="$2"; shift 2 ;;
    --gt) GT_TUM="$2"; shift 2 ;;
    --est) EST_TUM="$2"; shift 2 ;;
    --rate) RATE="$2"; shift 2 ;;
    --no-rviz) RVIZ="false"; shift ;;
    *) EXTRA+=("$1"); shift ;;
  esac
done

case "$MODE" in
  shell)
    exec bash
    ;;
  build)
    (cd catkin_ws && catkin_make)
    ;;
  inspect)
    BAG="$(find_bag_in_container "$BAG_ARG")"
    python3 scripts/inspect_bag.py --bag "$BAG"
    ;;
  gt|fetch-gt|extract-gt)
    BAG="$(find_bag_in_container "$BAG_ARG")"
    BAG_BASE="$(basename "$BAG" .bag)"
    OUT="${GT_TUM:-$E2O_EVAL_ROOT/data/ground_truth/${BAG_BASE}_gt.tum}"
    python3 scripts/extract_ground_truth.py --bag "$BAG" --gt-topic "$GT_TOPIC" --output "$OUT" "${EXTRA[@]}"
    ;;
  play)
    BAG="$(find_bag_in_container "$BAG_ARG")"
    roslaunch e2o_benchmark_tools e2o_dataset.launch bag:="$BAG" rate:="$RATE" use_rviz:="$RVIZ" publish_gt:="false"
    ;;
  play-gt)
    BAG="$(find_bag_in_container "$BAG_ARG")"
    if [[ -z "$GT_TUM" ]]; then
      BAG_BASE="$(basename "$BAG" .bag)"
      GT_TUM="$E2O_EVAL_ROOT/data/ground_truth/${BAG_BASE}_gt.tum"
    fi
    GT_TUM="$(resolve_file_in_container "$GT_TUM" "ground-truth TUM file")"
    roslaunch e2o_benchmark_tools e2o_dataset.launch bag:="$BAG" rate:="$RATE" use_rviz:="$RVIZ" publish_gt:="true" gt_tum:="$GT_TUM"
    ;;
  publish-gt)
    if [[ -z "$GT_TUM" ]]; then echo "ERROR: publish-gt needs --gt data/ground_truth/file.tum" >&2; exit 5; fi
    GT_TUM="$(resolve_file_in_container "$GT_TUM" "ground-truth TUM file")"
    roslaunch e2o_benchmark_tools publish_ground_truth.launch gt_tum:="$GT_TUM"
    ;;
  record)
    OUT="${EST_TUM:-$E2O_EVAL_ROOT/data/outputs/algorithm_trajectory.tum}"
    TOPIC="${EXTRA[0]:-/localization/odometry}"
    roslaunch e2o_benchmark_tools record_algorithm_tum.launch topic:="$TOPIC" output:="$OUT"
    ;;
  eval)
    if [[ -z "$GT_TUM" || -z "$EST_TUM" ]]; then
      echo "ERROR: eval needs --gt <gt.tum> --est <estimate.tum>" >&2
      exit 6
    fi
    GT_TUM="$(resolve_file_in_container "$GT_TUM" "ground-truth TUM file")"
    EST_TUM="$(resolve_file_in_container "$EST_TUM" "estimate TUM file")"
    python3 scripts/evaluate_tum.py --gt "$GT_TUM" --est "$EST_TUM" --out "$E2O_EVAL_ROOT/data/outputs/evaluation" "${EXTRA[@]}"
    ;;
  orb-slam3)
    BAG="$(find_bag_in_container "$BAG_ARG")"
    exec algorithms/orb_slam3/run_orb_slam3.sh --bag "$BAG" --rate "$RATE" "${EXTRA[@]}"
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    echo "Modes: shell | build | inspect | gt | play | play-gt | publish-gt | record | eval | orb-slam3" >&2
    exit 1
    ;;
esac
