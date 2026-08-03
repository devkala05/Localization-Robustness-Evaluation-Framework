#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST_PARENT="${ROOT}/data/datasets/boreas_rt"
AWS_CONFIG="${ROOT}/configs/datasets/aws_s3_download.conf"
# Fixed 60-second scored windows plus continuous sensor initialization. Most
# cells use 40 seconds; Farm retains its declared 120-second FAST-LIVO2 prefix.
# Timestamps are acquisition times, not filesystem mtimes.
ROUTES=(farm forest urban)
declare -A SEQUENCES=(
  [farm]="boreas-2025-07-18-15-30"
  [forest]="boreas-2025-07-18-11-53"
  [urban]="boreas-2025-08-06-06-33"
)
declare -A START_SECONDS=(
  [farm]=1752867070
  [forest]=1752854430
  [urban]=1754476978
)
declare -A END_SECONDS=(
  [farm]=1752867250
  [forest]=1752854530
  [urban]=1754477078
)

requested=("${@:-all}")
if [[ "${requested[0]}" == all ]]; then requested=("${ROUTES[@]}"); fi

docker image inspect amazon/aws-cli:latest >/dev/null 2>&1 || docker pull amazon/aws-cli:latest
mkdir -p "$DEST_PARENT"
exec 9>"${DEST_PARENT}/.route_window_download.lock"
flock -n 9 || { echo "another Boreas route-window downloader is active" >&2; exit 1; }

download_route() {
  local route="$1" sequence="${SEQUENCES[$1]:-}"
  [[ -n "$sequence" ]] || { echo "unknown route: $route" >&2; return 2; }
  local start_s="${START_SECONDS[$route]}"
  local end_s="${END_SECONDS[$route]}"
  local destination="${DEST_PARENT}/${sequence}"
  local includes=(--include 'imu/*' --include 'applanix/*' --include 'calib/*')
  local second
  for ((second=start_s; second<=end_s; second++)); do
    includes+=(--include "camera/${second}*.png" --include "lidar/${second}*.bin")
  done
  mkdir -p "$destination/camera" "$destination/lidar"
  docker run --rm --network host --user "$(id -u):$(id -g)" \
    -e AWS_CONFIG_FILE=/aws-config -e AWS_EC2_METADATA_DISABLED=true \
    -e AWS_MAX_ATTEMPTS=20 -e AWS_RETRY_MODE=adaptive \
    -v "${AWS_CONFIG}:/aws-config:ro" -v "${DEST_PARENT}:/data" \
    amazon/aws-cli s3 sync "s3://boreas/${sequence}" "/data/${sequence}" \
    --no-sign-request --only-show-errors --exclude '*' "${includes[@]}"

  local camera_count lidar_count
  camera_count="$(find "$destination/camera" -maxdepth 1 -type f -name '*.png' | wc -l)"
  lidar_count="$(find "$destination/lidar" -maxdepth 1 -type f -name '*.bin' | wc -l)"
  ((camera_count >= 590 && lidar_count >= 570)) || {
    echo "$route window is incomplete: camera=$camera_count lidar=$lidar_count" >&2
    return 1
  }
  for required in calib/T_applanix_dmu.txt calib/T_applanix_lidar.txt \
                  calib/T_camera_lidar.txt calib/P_camera.txt \
                  imu/dmu_imu_infilled.csv applanix/gps_post_process.csv; do
    [[ -s "$destination/$required" ]] || {
      echo "$route window is missing $required" >&2
      return 1
    }
  done
  printf '%s: sequence=%s start=%s duration=%ss camera=%s lidar=%s\n' \
    "$route" "$sequence" "$start_s" "$((end_s-start_s))" \
    "$camera_count" "$lidar_count"
}

pids=()
for route in "${requested[@]}"; do download_route "$route" & pids+=("$!"); done
failed=0
for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
exit "$failed"
