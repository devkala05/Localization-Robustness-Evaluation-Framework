#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SEQUENCE="boreas-2024-12-04-14-44"
DEST_PARENT="${ROOT}/data/datasets/boreas_rt"
DEST="${DEST_PARENT}/${SEQUENCE}"
EXPECTED_BYTES=13179516822
DOC_REF='ae3b54983349ae87962ce81c60f3ff2c5954c0f6'
AWS_CONFIG="${ROOT}/configs/datasets/aws_s3_download.conf"

mkdir -p "$DEST_PARENT"
exec 9>"${DEST_PARENT}/.download.lock"
flock -n 9 || { echo "another Boreas downloader is already active" >&2; exit 1; }
mkdir -p "$DEST/camera" "$DEST/lidar"
# AWS transfer temp names are randomized and cannot be resumed by a later CLI
# process. Remove only stale sensor temp files; completed .png/.bin files remain.
find "$DEST/camera" -maxdepth 1 -type f -name '*.png.*' -delete
find "$DEST/lidar" -maxdepth 1 -type f -name '*.bin.*' -delete

sync_group() {
  local group="$1"
  shift
  local includes=() pattern
  for pattern in "$@"; do includes+=(--include "$pattern"); done
  local attempt
  for attempt in $(seq 1 30); do
    if (( attempt > 1 )); then
      [[ "$group" == camera ]] && find "$DEST/camera" -maxdepth 1 -type f -name '*.png.*' -delete
      [[ "$group" == lidar ]] && find "$DEST/lidar" -maxdepth 1 -type f -name '*.bin.*' -delete
    fi
    if command -v aws >/dev/null 2>&1; then
      if AWS_CONFIG_FILE="$AWS_CONFIG" AWS_EC2_METADATA_DISABLED=true \
        AWS_MAX_ATTEMPTS=20 AWS_RETRY_MODE=adaptive \
        aws s3 sync "s3://boreas/${SEQUENCE}" "$DEST" \
        --no-sign-request --only-show-errors --exclude '*' "${includes[@]}"; then
        return 0
      fi
    else
      if docker run --rm --name "${SYNC_TAG}_${group}" --network host --user "$(id -u):$(id -g)" \
        -e AWS_CONFIG_FILE=/aws-config -e AWS_EC2_METADATA_DISABLED=true \
        -e AWS_MAX_ATTEMPTS=20 -e AWS_RETRY_MODE=adaptive \
        -v "${AWS_CONFIG}:/aws-config:ro" -v "${DEST_PARENT}:/data" \
        amazon/aws-cli s3 sync "s3://boreas/${SEQUENCE}" "/data/${SEQUENCE}" \
        --no-sign-request --only-show-errors --exclude '*' "${includes[@]}"; then
        return 0
      fi
    fi
    echo "Boreas ${group} sync attempt ${attempt}/30 failed; resuming in 3 seconds" >&2
    sleep 3
  done
  return 1
}

# S3 throughput on this machine is connection-limited. Separate workers keep
# the camera and lidar prefixes progressing concurrently instead of filling the
# transfer queue with every camera object before the first lidar object.
SYNC_TAG="boreas_sync_$$"
pids=()
docker_names=("${SYNC_TAG}_camera" "${SYNC_TAG}_lidar" "${SYNC_TAG}_aux")
sync_group camera 'camera/*' & pids+=("$!")
sync_group lidar 'lidar/*' & pids+=("$!")
sync_group aux 'imu/*' 'applanix/*' 'calib/*' & pids+=("$!")
cancel_syncs() {
  kill "${pids[@]}" 2>/dev/null || true
  if ! command -v aws >/dev/null 2>&1; then
    docker stop -t 1 "${docker_names[@]}" >/dev/null 2>&1 || true
  fi
  wait "${pids[@]}" 2>/dev/null || true
}
trap cancel_syncs INT TERM
sync_failed=0
for pid in "${pids[@]}"; do
  wait "$pid" || sync_failed=1
done
trap - INT TERM
[[ "$sync_failed" -eq 0 ]] || { echo "one or more Boreas S3 sync groups failed" >&2; exit 1; }

# Count only immutable upstream streams. Derived files such as ground_truth.csv
# may already be present when a validation slice is expanded to the full set.
ACTUAL_BYTES="$(find "$DEST/lidar" "$DEST/camera" "$DEST/imu" "$DEST/applanix" "$DEST/calib" \
  -type f -printf '%s\n' | awk '{sum += $1} END {print sum + 0}')"
[[ "$ACTUAL_BYTES" -eq "$EXPECTED_BYTES" ]] || {
  echo "Boreas-RT size mismatch: expected ${EXPECTED_BYTES}, got ${ACTUAL_BYTES}" >&2
  exit 1
}
CAMERA_COUNT="$(find "$DEST/camera" -maxdepth 1 -type f -name '*.png' | wc -l)"
LIDAR_COUNT="$(find "$DEST/lidar" -maxdepth 1 -type f -name '*.bin' | wc -l)"
[[ "$CAMERA_COUNT" -eq 1694 && "$LIDAR_COUNT" -eq 1627 ]] || {
  echo "Boreas-RT count mismatch: camera=${CAMERA_COUNT}/1694 lidar=${LIDAR_COUNT}/1627" >&2
  exit 1
}

DOC_DEST="${DEST_PARENT}/documentation"
mkdir -p "$DOC_DEST"
for document in DATA_RT_REFERENCE.md download.md LICENSE; do
  curl --fail --location --retry 8 --output "${DOC_DEST}/${document}" \
    "https://raw.githubusercontent.com/utiasASRL/pyboreas/${DOC_REF}/${document}"
done

find "$DEST/lidar" "$DEST/camera" "$DEST/imu" "$DEST/applanix" "$DEST/calib" \
  -type f -print0 | sort -z | xargs -0 sha256sum > "${DEST}/SHA256SUMS"
find "$DOC_DEST" -type f -print0 | sort -z | xargs -0 sha256sum > "${DOC_DEST}/SHA256SUMS"
echo "Boreas-RT ${SEQUENCE}: ${DEST}"
