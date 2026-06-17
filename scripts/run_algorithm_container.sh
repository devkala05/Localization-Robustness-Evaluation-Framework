#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ALGO=""; PER=""; MODE=""; EVALUATE="false"; EVAL_DURATION="0"
SKIP_RUNTIME_BUILD="${SKIP_RUNTIME_BUILD:-true}"
DOCKER_CPUS="${DOCKER_CPUS:-}"; DOCKER_MEMORY="${DOCKER_MEMORY:-}"
BAG_RATE="${BAG_RATE:-0.35}"; GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG:-0.0}"
ORB_MODE="${ORB_MODE:-stereo}"; STEREO_SWAP_BOOL="${STEREO_SWAP_BOOL:-true}"; R3LIVE_RUN_VISUAL="${R3LIVE_RUN_VISUAL:-true}"
DATASET_ID="${DATASET_ID:-urbannav}"
usage(){ echo "Internal runner. Use ./run --help"; }
while [ "$#" -gt 0 ]; do
  case "$1" in
    --algo) ALGO="${2:-}"; shift 2;; --algo=*) ALGO="${1#*=}"; shift;;
    --per) MODE="per"; PER="${2:-}"; shift 2;; --per=*) MODE="per"; PER="${1#*=}"; shift;;
    --eval|--summary|--evaluate) EVALUATE="true"; shift;;
    --duration|--seconds) EVAL_DURATION="${2:-}"; shift 2;; --duration=*|--seconds=*) EVAL_DURATION="${1#*=}"; shift;;
    --skip-build) SKIP_RUNTIME_BUILD="true"; shift;; --runtime-build) SKIP_RUNTIME_BUILD="false"; shift;;
    --shell) MODE="shell"; shift;; -h|--help) usage; exit 0;;
    *) echo "ERROR: unknown internal run argument: $1"; exit 2;;
  esac
done
[ -n "${ALGO}" ] || { echo "ERROR: --algo is required"; exit 2; }
[ -n "${MODE}" ] || { echo "ERROR: --per or --shell is required"; exit 2; }
if [ "${MODE}" = "per" ] && ! [[ "${PER}" =~ ^[0-6]$ ]]; then echo "ERROR: --per must be 0..6"; exit 2; fi
if ! [[ "${EVAL_DURATION}" =~ ^[0-9]+([.][0-9]+)?$ ]]; then echo "ERROR: --duration must be numeric"; exit 2; fi
case "${ALGO}" in
  fastlio2) DISPLAY_NAME="FAST-LIO2"; IMAGE_NAME="fastlio2-urbannav:latest"; RESULT_DIR="fast_lio2"; EXTRA_MOUNTS=();;
  lvisam) DISPLAY_NAME="LVI-SAM"; IMAGE_NAME="lvisam-urbannav:latest"; RESULT_DIR="lvi_sam"; EXTRA_MOUNTS=(-v "${SCRIPT_DIR}/wrappers/lvi_sam_urbannav:/root/catkin_ws/src/lvi_sam_urbannav" -v "${SCRIPT_DIR}/algorithms/lvi_sam/config:/root/catkin_ws/src/lvi_sam/config");;
  fastlivo2) DISPLAY_NAME="FAST-LIVO2"; IMAGE_NAME="fastlivo2-urbannav:latest"; RESULT_DIR="fast_livo2"; EXTRA_MOUNTS=(-v "${SCRIPT_DIR}/wrappers/fast_livo2_wrapper:/root/catkin_ws/src/fast_livo2_wrapper");;
  rtabmap) DISPLAY_NAME="RTAB-Map"; IMAGE_NAME="rtabmap-urbannav:latest"; RESULT_DIR="rtab_map"; EXTRA_MOUNTS=(-v "${SCRIPT_DIR}/wrappers/rtabmap_urbannav:/root/catkin_ws/src/rtabmap_urbannav");;
  adaptive_w_lvio) DISPLAY_NAME="Adaptive-W LVIO"; IMAGE_NAME="adap-w-lvio-urbannav:latest"; RESULT_DIR="adaptive_w_lvio"; EXTRA_MOUNTS=(-v "${SCRIPT_DIR}/wrappers/adaptive_w_lvio_urbannav:/root/catkin_ws/src/adaptive_w_lvio_urbannav");;
  orbslam3) DISPLAY_NAME="ORB-SLAM3"; IMAGE_NAME="orbslam3-urbannav:latest"; RESULT_DIR="orb_slam3"; EXTRA_MOUNTS=(-v "${SCRIPT_DIR}/wrappers/orbslam3_urbannav:/root/catkin_ws/src/orbslam3_urbannav");;
  r3live) DISPLAY_NAME="R3LIVE"; IMAGE_NAME="r3live-urbannav:latest"; RESULT_DIR="r3live"; EXTRA_MOUNTS=(-v "${SCRIPT_DIR}/wrappers/r3live_urbannav:/root/catkin_ws/src/r3live_urbannav");;
  *) echo "ERROR: unknown canonical algorithm '${ALGO}'"; exit 2;;
esac
if [ -n "${CONTAINER_NAME:-}" ]; then CONTAINER="${CONTAINER_NAME}"; elif [ "${MODE}" = "per" ]; then CONTAINER="${DATASET_ID}_${ALGO}_run_${PER}"; else CONTAINER="${DATASET_ID}_${ALGO}_shell"; fi
if [ -z "${DISPLAY:-}" ] && [ -S /tmp/.X11-unix/X1 ]; then export DISPLAY=:1; fi
mkdir -p "${SCRIPT_DIR}/data/results/${DATASET_ID}/${RESULT_DIR}" "${SCRIPT_DIR}/data/output"
chmod +x "${SCRIPT_DIR}"/scripts/*.sh 2>/dev/null || true
chmod +x "${SCRIPT_DIR}"/wrappers/localization_benchmark/scripts/*.py 2>/dev/null || true
chmod +x "${SCRIPT_DIR}"/wrappers/fast-lio_urbannav/scripts/*.py 2>/dev/null || true
for d in "${SCRIPT_DIR}"/wrappers/*/scripts; do [ -d "$d" ] && chmod +x "$d"/*.py 2>/dev/null || true; done
case "${MODE}" in
  per) if [ "${EVALUATE}" = "true" ]; then CMD=(/workspace/scripts/container_run_summary.sh "${PER}" "${EVAL_DURATION}" "${ALGO}"); else CMD=(/workspace/scripts/container_run_per.sh "${PER}" --attach "${ALGO}"); fi;;
  shell) CMD=(bash);;
esac
RESOURCE_ARGS=(); [ -n "${DOCKER_CPUS}" ] && RESOURCE_ARGS+=(--cpus="${DOCKER_CPUS}"); [ -n "${DOCKER_MEMORY}" ] && RESOURCE_ARGS+=(--memory="${DOCKER_MEMORY}")
TTY_ARGS=(); [ -t 0 ] && TTY_ARGS=(-it)
xhost +local:docker >/dev/null 2>&1 || true
docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
echo "[run] dataset=${DATASET_ID} algorithm=${DISPLAY_NAME} key=${ALGO} case=${MODE}${PER:+:per_${PER}} gps=${GPS_ENABLE:-off} eval=${EVALUATE}"
echo "[run] image=${IMAGE_NAME} container=${CONTAINER} bag_rate=${BAG_RATE} duration=${EVAL_DURATION}s"
exec docker run "${TTY_ARGS[@]}" \
  --name "${CONTAINER}" --network host --privileged "${RESOURCE_ARGS[@]}" \
  -e DISPLAY="${DISPLAY:-:0}" -e ROS_MASTER_URI=http://localhost:11311 -e ROS_HOSTNAME=localhost \
  -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
  -e SKIP_RUNTIME_BUILD="${SKIP_RUNTIME_BUILD}" -e BAG_RATE="${BAG_RATE}" -e GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG}" \
  -e GPS_ENABLE="${GPS_ENABLE:-off}" -e GPS_SOURCE="${GPS_SOURCE:-auto}" -e GPS_FILE="${GPS_FILE:-}" \
  -e GPS_TOPIC="${GPS_TOPIC:-/gps/fix_raw}" -e GPS_REQUIRED="${GPS_REQUIRED:-false}" -e GPS_USE_Z="${GPS_USE_Z:-off}" \
  -e GPS_ALPHA="${GPS_ALPHA:-0.08}" -e RTK_MODE="${RTK_MODE:-auto}" \
  -e STEREO_SWAP_BOOL="${STEREO_SWAP_BOOL}" -e R3LIVE_RUN_VISUAL="${R3LIVE_RUN_VISUAL}" \
  -e BAG_PATH_OVERRIDE="${BAG_PATH_OVERRIDE:-}" -e GT_PATH_OVERRIDE="${GT_PATH_OVERRIDE:-}" \
  -e DATASET_ID="${DATASET_ID}" -e DATASET_NAME="${DATASET_NAME:-urbannav_hk_tst_20210517}" \
  -e DATASET_RESULTS_ROOT="${DATASET_RESULTS_ROOT:-/data/results/${DATASET_ID}}" -e DATASET_FRAME_ID="${DATASET_FRAME_ID:-camera_init}" \
  -e DATASET_GT_FORMAT="${DATASET_GT_FORMAT:-auto}" -e DATASET_USE_CLOCK_STAMP="${DATASET_USE_CLOCK_STAMP:-false}" \
  -e DATASET_WORLD_FRAME="${DATASET_WORLD_FRAME:-camera_init}" -e DATASET_BODY_FRAME="${DATASET_BODY_FRAME:-body}" \
  -e DATASET_LIDAR_FRAME="${DATASET_LIDAR_FRAME:-velodyne}" -e DATASET_IMU_FRAME="${DATASET_IMU_FRAME:-body}" -e DATASET_CAMERA_FRAME="${DATASET_CAMERA_FRAME:-camera_right_optical}" \
  -e DATASET_LIDAR_MODEL="${DATASET_LIDAR_MODEL:-velodyne_32}" -e DATASET_SCAN_LINE="${DATASET_SCAN_LINE:-32}" \
  -e DATASET_PERTURBATIONS_DIR="${DATASET_PERTURBATIONS_DIR:-/root/catkin_ws/src/localization_benchmark/config/perturbations}" \
  -e DATASET_SEGMENTS_YAML="${DATASET_SEGMENTS_YAML:-/root/catkin_ws/src/localization_benchmark/config/road_segments.yaml}" \
  -e DATASET_POINT_TIME_FIELD="${DATASET_POINT_TIME_FIELD:-time}" -e DATASET_POINT_TIME_UNIT="${DATASET_POINT_TIME_UNIT:-s}" \
  -e DATASET_BAG_TOPICS="${DATASET_BAG_TOPICS:-}" \
  -e DATASET_SOURCE_LIDAR_TOPIC="${DATASET_SOURCE_LIDAR_TOPIC-/velodyne_points}" \
  -e DATASET_SOURCE_IMU_TOPIC="${DATASET_SOURCE_IMU_TOPIC-/imu/data}" \
  -e DATASET_SOURCE_CAMERA_TOPIC="${DATASET_SOURCE_CAMERA_TOPIC-/zed2/camera/right/image_raw}" \
  -e DATASET_SOURCE_LEFT_CAMERA_TOPIC="${DATASET_SOURCE_LEFT_CAMERA_TOPIC-/zed2/camera/left/image_raw}" \
  -e DATASET_SOURCE_GPS_TOPIC="${DATASET_SOURCE_GPS_TOPIC-}" \
  -e DATASET_CAMERA_RIGHT_K="${DATASET_CAMERA_RIGHT_K:-}" -e DATASET_CAMERA_RIGHT_D="${DATASET_CAMERA_RIGHT_D:-}" \
  -e DATASET_CAMERA_RIGHT_WIDTH="${DATASET_CAMERA_RIGHT_WIDTH:-}" -e DATASET_CAMERA_RIGHT_HEIGHT="${DATASET_CAMERA_RIGHT_HEIGHT:-}" \
  -e DATASET_CAMERA_LEFT_K="${DATASET_CAMERA_LEFT_K:-}" -e DATASET_CAMERA_LEFT_D="${DATASET_CAMERA_LEFT_D:-}" \
  -e ORB_MODE="${ORB_MODE}" -e ORB_SLAM3_ROOT="/root/ORB_SLAM3" \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw -v "${SCRIPT_DIR}/data:/data" -v "${SCRIPT_DIR}:/workspace" \
  -v "${SCRIPT_DIR}/wrappers/custom_localization_msgs:/root/catkin_ws/src/custom_localization_msgs" \
  -v "${SCRIPT_DIR}/wrappers/localization_benchmark:/root/catkin_ws/src/localization_benchmark" \
  -v "${SCRIPT_DIR}/wrappers/fast-lio_urbannav:/root/catkin_ws/src/fast_lio_urbannav" \
  "${EXTRA_MOUNTS[@]}" \
  "${IMAGE_NAME}" "${CMD[@]}"
