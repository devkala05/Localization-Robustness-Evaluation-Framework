#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW_DIR="${ROOT_DIR}/data/raw/kitti"
BASE_URL="https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data"
FREE_GB="$(df -BG /home/devil/Desktop/car/ | awk 'NR==2 {print $4}' | tr -d 'G')"

echo "Free disk: ${FREE_GB} GB"
if [ "${FREE_GB}" -lt 15 ]; then
  echo "ERROR: Insufficient disk space. Need 15 GB, have ${FREE_GB} GB." >&2
  exit 1
fi

mkdir -p "${RAW_DIR}"
cd "${RAW_DIR}"

download_zip() {
  local rel="$1"
  local zip_name
  zip_name="$(basename "${rel}")"
  if [ ! -f "${zip_name}" ]; then
    curl -L -C - -o "${zip_name}" "${BASE_URL}/${rel}"
  fi
  unzip -n "${zip_name}"
}

download_zip "2011_09_26_drive_0001/2011_09_26_drive_0001_sync.zip"
download_zip "2011_09_26_drive_0005/2011_09_26_drive_0005_sync.zip"
download_zip "2011_09_26_calib.zip"

mkdir -p "${ROOT_DIR}/config/calibration/kitti"
cp -f 2011_09_26/calib_cam_to_cam.txt "${ROOT_DIR}/config/calibration/kitti/"
cp -f 2011_09_26/calib_imu_to_velo.txt "${ROOT_DIR}/config/calibration/kitti/"
cp -f 2011_09_26/calib_velo_to_cam.txt "${ROOT_DIR}/config/calibration/kitti/"

echo "KITTI raw data and calibration files are ready under ${RAW_DIR}"
