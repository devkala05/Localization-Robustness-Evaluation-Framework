#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATASET="e2o"; BAG=""; GT=""; STRICT="false"
usage(){ cat <<'EOF'
Usage: ./inspect_bag.sh [--dataset e2o|urbannav] [--bag /data/...bag] [--gt /data/...txt] [--strict]

Runs a read-only ROS bag preflight in the FAST-LIO2 Docker image. Put E2O's bag at
  data/e2o/raw/one_full_loop.bag
or pass another path under this repository's data/ directory as /data/....
EOF
}
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dataset) DATASET="${2:-}"; shift 2;; --dataset=*) DATASET="${1#*=}"; shift;;
    --bag) BAG="${2:-}"; shift 2;; --bag=*) BAG="${1#*=}"; shift;;
    --gt) GT="${2:-}"; shift 2;; --gt=*) GT="${1#*=}"; shift;;
    --strict) STRICT="true"; shift;; -h|--help) usage; exit 0;;
    *) echo "ERROR: unknown argument: $1"; usage; exit 2;;
  esac
done
CONFIG="$ROOT/wrappers/localization_benchmark/config/datasets.yaml"
eval "$(python3 "$ROOT/scripts/dataset_config.py" --config "$CONFIG" --dataset "$DATASET")"
BAG="${BAG:-$DATASET_DEFAULT_BAG}"; GT="${GT:-$DATASET_DEFAULT_GT}"
IMAGE="fastlio2-urbannav:latest"
docker image inspect "$IMAGE" >/dev/null 2>&1 || {
  echo "ERROR: $IMAGE is not built. Run: ./build.sh fastlio2"; exit 1;
}
ARGS=(--bag "$BAG" --gt "$GT" --lidar-topic "$DATASET_SOURCE_LIDAR_TOPIC" --imu-topic "$DATASET_SOURCE_IMU_TOPIC" --camera-topic "$DATASET_SOURCE_CAMERA_TOPIC" --gps-topic "$DATASET_GPS_TOPIC" --point-time-field "$DATASET_POINT_TIME_FIELD" --point-time-unit "$DATASET_POINT_TIME_UNIT" --scan-lines "$DATASET_SCAN_LINES_ASSUMED")
[ -n "${DATASET_CAMERA_WIDTH:-}" ] && ARGS+=(--camera-width "$DATASET_CAMERA_WIDTH")
[ -n "${DATASET_CAMERA_HEIGHT:-}" ] && ARGS+=(--camera-height "$DATASET_CAMERA_HEIGHT")
[ "$STRICT" = "true" ] && ARGS+=(--strict)
exec docker run --rm --network host \
  -v "$ROOT/data:/data:ro" -v "$ROOT:/workspace:ro" \
  "$IMAGE" bash -lc 'source /opt/ros/noetic/setup.bash; python3 /workspace/scripts/inspect_dataset_bag.py "$@"' _ "${ARGS[@]}"
