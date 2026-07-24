#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SEQUENCE="ca_20190828184706"
DEST="${ROOT}/data/datasets/urbanloco/${SEQUENCE}"
BAG="${DEST}/CA-20190828184706_blur_align-002.bag"
CALIB="${DEST}/calibration/calibration_CA.txt"
EXPECTED_BYTES=14079033456
BAG_URL='https://www.dropbox.com/scl/fo/zrsmoddbq96t4go1wbxwp/APPKAk7BMyK59ItcE3qRAjU/ca/CA-20190828184706_blur_align-002.bag?rlkey=rk11n8tt62ejbg8mbixrm6quz&dl=1'
CALIB_URL='https://www.dropbox.com/scl/fo/zrsmoddbq96t4go1wbxwp/AGkoyJokKqKu39kefGG6wRI/ca/calibration_CA.txt?rlkey=rk11n8tt62ejbg8mbixrm6quz&dl=1'
DOC_REF='1c59f12794f6d2252779a3fd240358c2cc0f3099'

mkdir -p "${DEST}/calibration"

download() {
  local url="$1" output="$2"
  local attempt
  if command -v aria2c >/dev/null 2>&1; then
    aria2c --continue=true --max-connection-per-server=8 --split=8 \
      --min-split-size=16M --file-allocation=none --auto-file-renaming=false \
      --dir "$(dirname "$output")" --out "$(basename "$output").part" "$url"
    mv "${output}.part" "$output"
    return
  fi
  for attempt in $(seq 1 12); do
    # Invoke curl afresh after each failure so `-C -` re-stats the partial file.
    # curl's internal retry can reuse the original offset and truncate a large
    # partial transfer after a redirected Dropbox connection is interrupted.
    if curl --fail --location --continue-at - --output "${output}.part" "$url"; then
      break
    fi
    [[ "$attempt" -lt 12 ]] || { echo "download failed after ${attempt} attempts: ${url}" >&2; return 1; }
    sleep 3
  done
  mv "${output}.part" "$output"
}

if [[ ! -f "$BAG" || "$(stat -c %s "$BAG")" -ne "$EXPECTED_BYTES" ]]; then
  download "$BAG_URL" "$BAG"
fi
[[ "$(stat -c %s "$BAG")" -eq "$EXPECTED_BYTES" ]] || {
  echo "UrbanLoco size mismatch: expected ${EXPECTED_BYTES}, got $(stat -c %s "$BAG")" >&2
  exit 1
}

download "$CALIB_URL" "$CALIB"
mkdir -p "${DEST}/documentation"
curl --fail --location --retry 8 --output "${DEST}/documentation/UrbanLoco_README.md" \
  "https://raw.githubusercontent.com/weisongwen/UrbanLoco/${DOC_REF}/README.md"
curl --fail --location --retry 8 --output "${DEST}/documentation/UrbanLoco_dataset_paper.pdf" \
  "https://raw.githubusercontent.com/weisongwen/UrbanLoco/${DOC_REF}/papers/Full_Sensor_Suite_Dataset_for_Mapping_and_Localization_in_Urban.pdf"
find "$DEST" -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > "${DEST}/SHA256SUMS"
echo "UrbanLoco ${SEQUENCE}: ${BAG}"
