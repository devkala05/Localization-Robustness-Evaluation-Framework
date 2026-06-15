#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BAG_PATH="${1:-${SCRIPT_DIR}/one_full_loop.bag}"
OUT_CSV="${2:-${SCRIPT_DIR}/gt_one_full_loop_fastlivo2_lidar103.csv}"
IMAGE="${FASTLIVO_DOCKER_IMAGE:-fastlivo2-urbannav:latest}"
LIDAR_TOPIC="${LIDAR_TOPIC:-/lidar103/velodyne_points}"
IMU_TOPIC="${IMU_TOPIC:-/mavros/imu/data}"
CAMERA_TOPIC="${CAMERA_TOPIC:-/camera/color/image_raw}"
RATE="${BAG_PLAY_RATE:-2.0}"
OUTPUT_DIR="${SCRIPT_DIR}/fastlivo_output"

if [[ ! -f "${BAG_PATH}" ]]; then
  echo "Bag not found: ${BAG_PATH}" >&2
  exit 1
fi

rm -rf "${OUTPUT_DIR}"
mkdir -p "${OUTPUT_DIR}"
rm -f "${OUT_CSV}"

set +e
docker run --rm \
  -v "${SCRIPT_DIR}:/ws" \
  -v "$(dirname "${BAG_PATH}"):/bag:ro" \
  -w /ws \
  "${IMAGE}" \
  bash -lc "
    set -euo pipefail
    source /opt/ros/noetic/setup.bash
    source /root/catkin_ws/devel/setup.bash
    roscore >/tmp/gt_roscore.log 2>&1 &
    trap 'pkill -f roslaunch || true; pkill -f roscore || true; pkill -f rosbag || true' EXIT
    sleep 2
    roslaunch fast_livo2_wrapper topic_bridge.launch \
      lidar_topic_in:=${LIDAR_TOPIC} \
      imu_topic_in:=${IMU_TOPIC} \
      cam_topic_in:=${CAMERA_TOPIC} >/tmp/gt_bridge.log 2>&1 &
    roslaunch fast_livo2_wrapper record_outputs.launch \
      output_dir:=/ws/fastlivo_output \
      record_bag:=false >/tmp/gt_recorder.log 2>&1 &
    roslaunch fast_livo2_wrapper fast_livo2.launch \
      img_en:=0 \
      lidar_en:=1 \
      imu_en:=true \
      pcd_save_en:=false >/tmp/gt_fastlivo.log 2>&1 &
    sleep 8
    rosbag play /bag/$(basename "${BAG_PATH}") \
      --clock \
      --rate ${RATE} \
      --topics ${LIDAR_TOPIC} ${IMU_TOPIC} >/tmp/gt_bagplay.log 2>&1
    sleep 3
    chmod -R a+rw /ws/fastlivo_output
    echo 'FAST-LIVO2 recorder log:'
    tail -40 /tmp/gt_recorder.log || true
    echo 'FAST-LIVO2 mapping log:'
    tail -80 /tmp/gt_fastlivo.log || true
  "
docker_status=$?
set -e
if [[ "${docker_status}" -ne 0 && "${docker_status}" -ne 143 ]]; then
  echo "FAST-LIVO2 Docker run failed with exit code ${docker_status}" >&2
  exit "${docker_status}"
fi

python3 "${SCRIPT_DIR}/convert_fastlivo_csv_to_gt.py" \
  --input "${OUTPUT_DIR}/odometry.csv" \
  --output "${OUT_CSV}"

echo "FAST-LIVO2 pseudo-GT ready: ${OUT_CSV}"
