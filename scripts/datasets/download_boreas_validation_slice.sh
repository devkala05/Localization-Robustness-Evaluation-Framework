#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SEQUENCE="boreas-2024-12-04-14-44"
DEST_PARENT="${ROOT}/data/datasets/boreas_rt"
DEST="${DEST_PARENT}/${SEQUENCE}"
FRAME_COUNT="${BOREAS_VALIDATION_FRAMES:-120}"
AWS_CONFIG="${ROOT}/configs/datasets/aws_s3_download.conf"

[[ "$FRAME_COUNT" =~ ^[1-9][0-9]*$ ]] || {
  echo "BOREAS_VALIDATION_FRAMES must be a positive integer" >&2
  exit 2
}
docker image inspect amazon/aws-cli:latest >/dev/null 2>&1 || docker pull amazon/aws-cli:latest
mkdir -p "$DEST"

INCLUDES=(--include 'imu/*' --include 'applanix/*' --include 'calib/*')
for sensor in lidar camera; do
  prefix="${SEQUENCE}/${sensor}/"
  listing="$(docker run --rm --network host -e AWS_EC2_METADATA_DISABLED=true \
    -e AWS_MAX_ATTEMPTS=20 -e AWS_RETRY_MODE=adaptive amazon/aws-cli s3api list-objects-v2 \
    --bucket boreas --prefix "$prefix" --max-items "$FRAME_COUNT" \
    --no-sign-request --query 'Contents[].Key' --output text)"
  while IFS= read -r key; do
    [[ -n "$key" && "$key" != "None" ]] && INCLUDES+=(--include "${key#"${SEQUENCE}/"}")
  done < <(tr '\t' '\n' <<<"$listing")
done

docker run --rm --network host --user "$(id -u):$(id -g)" \
  -e AWS_CONFIG_FILE=/aws-config -e AWS_EC2_METADATA_DISABLED=true \
  -e AWS_MAX_ATTEMPTS=20 -e AWS_RETRY_MODE=adaptive \
  -v "${AWS_CONFIG}:/aws-config:ro" -v "${DEST_PARENT}:/data" amazon/aws-cli \
  s3 sync "s3://boreas/${SEQUENCE}" "/data/${SEQUENCE}" \
  --no-sign-request --only-show-errors --exclude '*' "${INCLUDES[@]}"

printf 'Boreas validation slice: %s frames per image/lidar stream\n' "$FRAME_COUNT"
printf 'Destination: %s\n' "$DEST"
du -sh "$DEST"
