#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATASET=""; SEQUENCE=""; ALGORITHM=""; RATE=""; DURATION="0"; START_OFFSET="0"
PHASE="production"; RVIZ="false"
# Use ORB-SLAM3's native RGB-D mode with calibrated LiDAR-projected depth.
# Pure monocular remains available for ablations, but forward driving makes it
# scale-unobservable and poorly conditioned on these public sequences.
ORB_MODE="rgbd"; ALIGNMENT="se3"; ALIGNMENT_REASON="native metric RGB-D mode; LiDAR depth makes scale observable"
# The full visual branch is opt-in: both public sequences trigger native VINS
# reboots over a complete route.  The default remains LVI-SAM's own LIO mode.
LVISAM_MODE="lidar-inertial"

usage() {
  printf '%s\n' \
    'Usage: ./run_benchmark.sh --dataset urbanloco|boreas_rt --sequence NAME --algorithm NAME [options]' \
    'Algorithms: lvisam fastlivo2 orbslam3 rtabmap fastlio2' \
    'Options: --start-offset SECONDS --duration SECONDS --rate FACTOR' \
    '         --phase tuning|validation|holdout|production' \
    '         --orb-mode rgbd-inertial|rgbd|mono-inertial|mono' \
    '         --lvisam-mode visual-lidar-inertial|lidar-inertial --rviz'
}

while (($#)); do
  case "$1" in
    --dataset) DATASET="${2:-}"; shift 2 ;;
    --sequence) SEQUENCE="${2:-}"; shift 2 ;;
    --algorithm) ALGORITHM="${2:-}"; shift 2 ;;
    --duration) DURATION="${2:-}"; shift 2 ;;
    --start-offset) START_OFFSET="${2:-}"; shift 2 ;;
    --rate) RATE="${2:-}"; shift 2 ;;
    --phase) PHASE="${2:-}"; shift 2 ;;
    --orb-mode) ORB_MODE="${2:-}"; shift 2 ;;
    --lvisam-mode) LVISAM_MODE="${2:-}"; shift 2 ;;
    --rviz) RVIZ=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

# LVI-SAM's scan-to-map path cannot process these dense public LiDAR streams
# in real time on the benchmark host. Slow only wall-clock delivery by default;
# ROS/message timestamps remain native and an explicit --rate still wins.
if [[ -z "$RATE" ]]; then
  case "$ALGORITHM" in
    lvisam) RATE="0.10" ;;
    rtabmap) RATE="0.10" ;;
    orbslam3) RATE="0.50" ;;
    *) RATE="1.0" ;;
  esac
fi

case "$PHASE" in tuning|validation|holdout|production) ;; *)
  printf 'Invalid phase: %s\n' "$PHASE" >&2; usage >&2; exit 2 ;;
esac
case "$ORB_MODE" in rgbd-inertial|rgbd|mono-inertial|mono) ;; *)
  printf 'Invalid ORB mode: %s\n' "$ORB_MODE" >&2; usage >&2; exit 2 ;;
esac
case "$LVISAM_MODE" in visual-lidar-inertial|lidar-inertial) ;; *)
  printf 'Invalid LVI-SAM mode: %s\n' "$LVISAM_MODE" >&2; usage >&2; exit 2 ;;
esac
python3 - "$START_OFFSET" "$DURATION" "$RATE" <<'PY' || exit 2
import math, sys
start, duration, rate = map(float, sys.argv[1:])
if not all(map(math.isfinite, (start, duration, rate))) or start < 0 or duration < 0 or rate <= 0:
    raise SystemExit("start offset and duration must be non-negative; rate must be positive")
PY
PLAYBACK_START="$START_OFFSET"; PLAYBACK_DURATION="$DURATION"
if [[ "$PHASE" == validation || "$PHASE" == holdout ]] && [[ "$START_OFFSET" != 0 ]]; then
  PLAYBACK_START=0
  if [[ "$DURATION" != 0 ]]; then
    PLAYBACK_DURATION="$(python3 -c 'import sys; print(float(sys.argv[1])+float(sys.argv[2]))' "$START_OFFSET" "$DURATION")"
  fi
fi

[[ "$DATASET" == "boreas" ]] && DATASET=boreas_rt
case "$DATASET:$SEQUENCE" in
  urbanloco:ca_20190828184706)
    INPUT_KIND=bag
    INPUT_HOST="$ROOT/data/datasets/urbanloco/$SEQUENCE/CA-20190828184706_blur_align-002.bag"
    SENSOR_CONFIG=/workspace/wrappers/localization_benchmark/config/urbanloco_ca_20190828184706.yaml
    LIDAR_TOPIC=/rslidar_points; IMU_TOPIC=/imu_raw
    CAMERA_TOPIC=/camera_array/cam0/image_raw/compressed
    SEQUENCE_START_TIME=1567043229.035060
    SEQUENCE_DURATION=248.743
    ORB_ROTATION='[-0.999905182,-0.012990044,-0.004570194,0.004732473,-0.012489447,-0.999910805,0.012931806,-0.999837623,0.012549737]'
    ORB_TRANSLATION='[-0.024227447,-0.184995634,-0.412094702]'
    BASE_TO_LIDAR='[0.0,0.0,-0.0762,0.0,1.0,0.0,-1.0,0.0,0.0,0.0,0.0,1.0]'
    LIDAR_TO_BODY='[0.0,-1.0,0.0,0.0,1.0,0.0,0.0,0.0,0.0,0.0,1.0,0.0762,0.0,0.0,0.0,1.0]'
    ;;
  boreas_rt:boreas_2024_12_04_14_44)
    INPUT_KIND=boreas
    INPUT_HOST="$ROOT/data/datasets/boreas_rt/boreas-2024-12-04-14-44"
    SENSOR_CONFIG=/workspace/wrappers/localization_benchmark/config/boreas_2024_12_04_14_44.yaml
    LIDAR_TOPIC=/dataset/lidar; IMU_TOPIC=/dataset/imu; CAMERA_TOPIC=/dataset/camera
    # Earliest event among raw camera, lidar, and DMU streams. The supplied
    # ground truth begins 36.4 seconds earlier and is not the playback origin.
    SEQUENCE_START_TIME=1733341473.191912
    SEQUENCE_DURATION=169.35
    ORB_ROTATION='[0.999985098,0.001080950,-0.005294156,-0.005294444,-0.000369157,-0.999985645,-0.001083823,0.999999247,-0.000363770]'
    ORB_TRANSLATION='[-0.077635296,-0.489184591,-0.055849794]'
    BASE_TO_LIDAR='[-0.000396915,0.000071663,-0.279999699,0.728264316,-0.685294210,-0.001417554,-0.685295070,-0.728264816,0.000255938,-0.001208116,0.000785312,-0.999998924]'
    LIDAR_TO_BODY='[0.728264544,-0.685295257,-0.001207749,0.0,-0.685295313,-0.728265958,0.000785053,0.0,-0.001418000,0.000256000,-0.999999000,-0.28,0.0,0.0,0.0,1.0]'
    ;;
  *) usage >&2; printf 'Unsupported dataset/sequence: %s/%s\n' "$DATASET" "$SEQUENCE" >&2; exit 2 ;;
esac

case "$ALGORITHM" in
  fastlivo2) IMAGE=fastlivo2-e2o:latest; OUTPUT_TOPIC=/fast_livo2/odometry ;;
  orbslam3) IMAGE=orbslam3-e2o:latest; OUTPUT_TOPIC=/orbslam3/camera_odometry ;;
  lvisam) IMAGE=lvisam-e2o:latest; OUTPUT_TOPIC=/lvisam/odometry ;;
  fastlio2) IMAGE=fastlio2-benchmark:latest; OUTPUT_TOPIC=/fastlio2/odometry ;;
  rtabmap) IMAGE=rtabmap-benchmark:latest; OUTPUT_TOPIC=/rtabmap/odometry ;;
  *) usage >&2; printf 'Unsupported algorithm: %s\n' "$ALGORITHM" >&2; exit 2 ;;
esac
if [[ "$ALGORITHM" != orbslam3 ]]; then
  ALIGNMENT_REASON="native metric estimator; sensor calibration makes scale observable"
fi

# Start only the sensor and adapter branches required by the declared native
# algorithm mode. This prevents the Python adapter from decoding/resizing and
# duplicating unrelated high-bandwidth streams during a benchmark.
NEED_LIDAR=false; NEED_IMU=false; NEED_CAMERA=false
ENABLE_FASTLIVO=false; ENABLE_ORB=false; ENABLE_LVISAM=false; ENABLE_RAW=false
case "$ALGORITHM" in
  fastlivo2)
    NEED_LIDAR=true; NEED_IMU=true; NEED_CAMERA=true; ENABLE_FASTLIVO=true ;;
  lvisam)
    NEED_LIDAR=true; NEED_IMU=true; ENABLE_LVISAM=true
    [[ "$LVISAM_MODE" == visual-lidar-inertial ]] && NEED_CAMERA=true ;;
  orbslam3)
    NEED_CAMERA=true; ENABLE_ORB=true
    [[ "$ORB_MODE" == rgbd || "$ORB_MODE" == rgbd-inertial ]] && NEED_LIDAR=true
    [[ "$ORB_MODE" == mono-inertial || "$ORB_MODE" == rgbd-inertial ]] && NEED_IMU=true ;;
  fastlio2|rtabmap)
    NEED_LIDAR=true; NEED_IMU=true; ENABLE_RAW=true ;;
esac

[[ -e "$INPUT_HOST" ]] || { printf 'Dataset input missing: %s\nRun the scripts/datasets downloader first.\n' "$INPUT_HOST" >&2; exit 1; }
for required_image in e2o-localization-fusion:latest "$IMAGE"; do
  docker image inspect "$required_image" >/dev/null 2>&1 || {
    printf 'Missing Docker image %s; run ./build.sh %s\n' "$required_image" "${ALGORITHM/fastlivo2/fast_livo2}" >&2
    exit 1
  }
done

RUN_ID="$(date +%Y%m%d_%H%M%S)_${DATASET}_${SEQUENCE}_${ALGORITHM}_$$"
OUT_HOST="$ROOT/results/$DATASET/$SEQUENCE/$ALGORITHM/$RUN_ID"
OUT_CONTAINER="/data/output/$RUN_ID"
STACK="public_loc_$RUN_ID"
mkdir -p "$OUT_HOST"
CONTAINERS=()
COMMON=(--network host -e ROS_MASTER_URI=http://localhost:11311 -e ROS_HOSTNAME=localhost
        -v "$ROOT:/workspace:ro" -v "$OUT_HOST:$OUT_CONTAINER")

cleanup() {
  set +e
  for ((index=${#CONTAINERS[@]}-1; index>=0; index--)); do
    docker stop -t 5 "${CONTAINERS[$index]}" >/dev/null 2>&1 || true
  done
  for name in "${CONTAINERS[@]}"; do
    docker logs "$name" >"$OUT_HOST/${name##${STACK}_}.log" 2>&1 || true
  done
  for ((index=${#CONTAINERS[@]}-1; index>=0; index--)); do
    docker rm -f "${CONTAINERS[$index]}" >/dev/null 2>&1 || true
  done
}
trap cleanup EXIT INT TERM

start() {
  local name="$1" image="$2"; shift 2
  docker run -d --name "${STACK}_${name}" "${COMMON[@]}" "$image" "$@" >/dev/null
  CONTAINERS+=("${STACK}_${name}")
}

printf 'dataset=%s\nsequence=%s\nalgorithm=%s\nrate=%s\nstart_offset=%s\nduration=%s\nphase=%s\nrun_id=%s\n' \
  "$DATASET" "$SEQUENCE" "$ALGORITHM" "$RATE" "$START_OFFSET" "$DURATION" "$PHASE" "$RUN_ID" >"$OUT_HOST/run_metadata.env"
printf 'playback_start_offset=%s\nplayback_duration=%s\nevaluation_start_offset=%s\nevaluation_duration=%s\n' \
  "$PLAYBACK_START" "$PLAYBACK_DURATION" "$START_OFFSET" "$DURATION" >>"$OUT_HOST/run_metadata.env"
printf 'sequence_start_time=%s\n' "$SEQUENCE_START_TIME" >>"$OUT_HOST/run_metadata.env"
printf 'sequence_duration=%s\n' "$SEQUENCE_DURATION" >>"$OUT_HOST/run_metadata.env"
printf './run_benchmark.sh --dataset %q --sequence %q --algorithm %q --rate %q --start-offset %q --duration %q --phase %q --orb-mode %q --lvisam-mode %q%s\n' \
  "$DATASET" "$SEQUENCE" "$ALGORITHM" "$RATE" "$START_OFFSET" "$DURATION" "$PHASE" "$ORB_MODE" "$LVISAM_MODE" "$([[ "$RVIZ" == true ]] && printf ' --rviz')" \
  >"$OUT_HOST/reproduction_command.txt"
docker image inspect -f '{{.Id}}' "$IMAGE" >"$OUT_HOST/docker_image_id.txt"
cp "$ROOT/wrappers/localization_benchmark/config/${SEQUENCE/ca_20190828184706/urbanloco_ca_20190828184706}.yaml" "$OUT_HOST/sensor_adapter.yaml"

start roscore e2o-localization-fusion:latest roscore
sleep 2
INPUT_COMMAND='for f in e2o_sensor_adapter.py e2o_static_tf_publisher.py; do cp "/workspace/wrappers/localization_benchmark/scripts/${f}" "/root/catkin_ws/devel/.private/localization_benchmark/lib/localization_benchmark/${f}"; chmod +x "/root/catkin_ws/devel/.private/localization_benchmark/lib/localization_benchmark/${f}"; done; source /opt/ros/noetic/setup.bash; source /root/catkin_ws/devel/setup.bash; export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH}; rospack profile >/dev/null; exec roslaunch /workspace/wrappers/localization_benchmark/launch/dataset_input_pipeline.launch "$@"'
start input e2o-localization-fusion:latest bash -lc "$INPUT_COMMAND" _ config:="$SENSOR_CONFIG" source_lidar_topic:="$LIDAR_TOPIC" source_imu_topic:="$IMU_TOPIC" source_camera_topic:="$CAMERA_TOPIC" source_depth_topic:="" \
  enable_lidar:="$NEED_LIDAR" enable_imu:="$NEED_IMU" enable_camera:="$NEED_CAMERA" \
  enable_fastlivo:="$ENABLE_FASTLIVO" enable_orb:="$ENABLE_ORB" \
  enable_lvisam:="$ENABLE_LVISAM" enable_raw:="$ENABLE_RAW" orb_mode:="$ORB_MODE"

case "$ALGORITHM" in
  fastlivo2)
    CONFIG="/workspace/wrappers/fast_livo2_e2o/config/${SEQUENCE/ca_20190828184706/urbanloco_ca_20190828184706}.yaml"
    [[ "$DATASET" == urbanloco ]] && SCAN_LINES=32 || SCAN_LINES=128
    COMMAND='source /opt/ros/noetic/setup.bash; source /root/catkin_ws/devel/setup.bash; export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH}; exec roslaunch /workspace/wrappers/fast_livo2_e2o/launch/algorithm.launch "$@"'
    start algorithm "$IMAGE" bash -lc "$COMMAND" _ config_path:="$CONFIG" output_topic:="$OUTPUT_TOPIC" pcd_save_en:=false scan_line:="$SCAN_LINES" rebase_on_start:=false
    ;;
  lvisam)
    LIDAR_CONFIG="/workspace/wrappers/lvisam_e2o/config/params_lidar_${SEQUENCE/ca_20190828184706/urbanloco_ca_20190828184706}.yaml"
    CAMERA_CONFIG="/workspace/wrappers/lvisam_e2o/config/params_camera_${SEQUENCE/ca_20190828184706/urbanloco_ca_20190828184706}.yaml"
    COMMAND='source /opt/ros/noetic/setup.bash; source /root/catkin_ws/devel/setup.bash; export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH}; exec roslaunch /workspace/wrappers/lvisam_e2o/launch/algorithm.launch "$@"'
    [[ "$LVISAM_MODE" == visual-lidar-inertial ]] && ENABLE_VISUAL=true || ENABLE_VISUAL=false
    # A public benchmark must export native LVI-SAM motion in its own frame.
    # In particular, do not seed it from the fusion stack (which may itself be
    # using another estimator); global registration is evaluation-only.
    start algorithm "$IMAGE" bash -lc "$COMMAND" _ lidar_config:="$LIDAR_CONFIG" camera_config:="$CAMERA_CONFIG" output_topic:="$OUTPUT_TOPIC" enable_visual:="$ENABLE_VISUAL" sensor_to_body:="$LIDAR_TO_BODY" rebase_on_start:=false
    cp "${LIDAR_CONFIG/\/workspace/$ROOT}" "$OUT_HOST/lidar_config.yaml"
    cp "${CAMERA_CONFIG/\/workspace/$ROOT}" "$OUT_HOST/camera_config.yaml"
    ;;
  orbslam3)
    CONFIG="/workspace/wrappers/orbslam3_e2o/config/${SEQUENCE/ca_20190828184706/urbanloco_ca_20190828184706}.yaml"
    COMMAND='for f in pose_republisher_node.py run_orbslam3_native.py; do cp "/workspace/wrappers/orbslam3_e2o/scripts/${f}" "/root/catkin_ws/devel/.private/orbslam3_e2o/lib/orbslam3_e2o/${f}"; chmod +x "/root/catkin_ws/devel/.private/orbslam3_e2o/lib/orbslam3_e2o/${f}"; done; source /opt/ros/noetic/setup.bash; source /root/catkin_ws/devel/setup.bash; export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH}; exec roslaunch /workspace/wrappers/orbslam3_e2o/launch/algorithm.launch "$@"'
    # Public-dataset evaluation records the native metric trajectory. Disable
    # the E2O continuity/re-anchor policy so real motion, resets, and jumps are
    # measured instead of being rewritten by wrapper-side heuristics.
    case "$ORB_MODE" in
      mono)
        ORB_EXECUTABLE=Mono
        ALIGNMENT=sim3
        ALIGNMENT_REASON="pure monocular mode; scale is unobservable"
        ;;
      mono-inertial)
        ORB_EXECUTABLE=Mono_Inertial
        ALIGNMENT_REASON="native metric monocular-inertial mode; IMU makes scale observable"
        ;;
      rgbd)
        ORB_EXECUTABLE=RGBD
        ALIGNMENT_REASON="native metric RGB-D mode; LiDAR depth makes scale observable"
        ;;
      rgbd-inertial)
        ORB_EXECUTABLE=RGBD_Inertial
        ;;
    esac
    start algorithm "$IMAGE" bash -lc "$COMMAND" _ camera_config:="$CONFIG" executable:="$ORB_EXECUTABLE" \
      output_odom_topic:="$OUTPUT_TOPIC" optical_to_body_rotation:="$ORB_ROTATION" \
      optical_to_body_translation:="$ORB_TRANSLATION" max_step_m:=1000000 \
      max_gap_step_m:=1000000 max_speed_mps:=1000000 max_yaw_step_deg:=360 \
      max_backtrack_m:=1000000 reanchor_on_loop_closure:=false
    ;;
  fastlio2)
    CONFIG="/workspace/wrappers/fastlio2_benchmark/config/${SEQUENCE/ca_20190828184706/urbanloco_ca_20190828184706}.yaml"
    COMMAND='source /opt/ros/noetic/setup.bash; source /root/catkin_ws/devel/setup.bash; export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH}; exec roslaunch /workspace/wrappers/fastlio2_benchmark/launch/algorithm.launch "$@"'
    start algorithm "$IMAGE" bash -lc "$COMMAND" _ config:="$CONFIG" output_topic:="$OUTPUT_TOPIC"
    ;;
  rtabmap)
    CONFIG="/workspace/wrappers/rtabmap_benchmark/config/${SEQUENCE/ca_20190828184706/urbanloco_ca_20190828184706}.yaml"
    COMMAND='source /opt/ros/noetic/setup.bash; source /root/catkin_ws/devel/setup.bash; export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH}; exec roslaunch /workspace/wrappers/rtabmap_benchmark/launch/algorithm.launch "$@"'
    start algorithm "$IMAGE" bash -lc "$COMMAND" _ config:="$CONFIG" database_path:="$OUT_CONTAINER/rtabmap.db"
    ;;
esac
ALGORITHM_CONFIG_PATH="${CONFIG:-$LIDAR_CONFIG}"
cp "${ALGORITHM_CONFIG_PATH/\/workspace/$ROOT}" "$OUT_HOST/algorithm_config.yaml"
printf 'image=%s\noutput_topic=%s\nsensor_config=%s\nalgorithm_config=%s\n' \
  "$IMAGE" "$OUTPUT_TOPIC" "$SENSOR_CONFIG" "$ALGORITHM_CONFIG_PATH" >>"$OUT_HOST/run_metadata.env"
printf 'lidar_topic=%s\nimu_topic=%s\ncamera_topic=%s\nbase_to_lidar=%s\norb_body_rotation=%s\norb_body_translation=%s\n' \
  "$LIDAR_TOPIC" "$IMU_TOPIC" "$CAMERA_TOPIC" "$BASE_TO_LIDAR" "$ORB_ROTATION" "$ORB_TRANSLATION" \
  >>"$OUT_HOST/run_metadata.env"
printf 'orb_mode=%s\nalignment=%s\nalignment_reason=%s\n' \
  "$ORB_MODE" "$ALIGNMENT" "$ALIGNMENT_REASON" >>"$OUT_HOST/run_metadata.env"
printf 'lvisam_mode=%s\n' "$LVISAM_MODE" >>"$OUT_HOST/run_metadata.env"

RECORDER_COMMAND='cp /workspace/wrappers/e2o_localization_fusion/scripts/multi_trajectory_recorder.py /root/catkin_ws/devel/.private/e2o_localization_fusion/lib/e2o_localization_fusion/; chmod +x /root/catkin_ws/devel/.private/e2o_localization_fusion/lib/e2o_localization_fusion/multi_trajectory_recorder.py; source /opt/ros/noetic/setup.bash; source /root/catkin_ws/devel/setup.bash; export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH}; exec roslaunch /workspace/wrappers/e2o_localization_fusion/launch/recorder_only.launch "$@"'
RECORDER_STANDALONE=true
[[ "$ALGORITHM" == orbslam3 ]] && RECORDER_STANDALONE=false
start recorder e2o-localization-fusion:latest bash -lc "$RECORDER_COMMAND" _ algorithm:="$ALGORITHM" topic:="$OUTPUT_TOPIC" output_dir:="$OUT_CONTAINER" standalone:="$RECORDER_STANDALONE"

if [[ "$RVIZ" == true ]]; then
  if [[ "$INPUT_KIND" == bag ]]; then GT_HOST="$(dirname "$INPUT_HOST")/ground_truth.csv"; else GT_HOST="$INPUT_HOST/ground_truth.csv"; fi
  [[ -f "$GT_HOST" ]] || { printf 'RViz requested but converted ground truth is missing: %s\n' "$GT_HOST" >&2; exit 1; }
  REFERENCE_COMMAND='cp /workspace/wrappers/localization_benchmark/scripts/reference_visualizer.py /root/catkin_ws/devel/.private/localization_benchmark/lib/localization_benchmark/; chmod +x /root/catkin_ws/devel/.private/localization_benchmark/lib/localization_benchmark/reference_visualizer.py; source /opt/ros/noetic/setup.bash; source /root/catkin_ws/devel/setup.bash; export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH}; exec roslaunch /workspace/wrappers/localization_benchmark/launch/reference_visualization.launch "$@"'
  start reference e2o-localization-fusion:latest bash -lc "$REFERENCE_COMMAND" _ ground_truth_csv:="/workspace/${GT_HOST#"$ROOT/"}" base_to_lidar:="$BASE_TO_LIDAR"
  xhost +local:docker >/dev/null 2>&1 || true
  docker run -d --name "${STACK}_rviz" "${COMMON[@]}" -e DISPLAY="${DISPLAY:-:0}" \
    -e LIBGL_ALWAYS_SOFTWARE=1 \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw e2o-localization-fusion:latest \
    rviz -d /workspace/rviz/public_dataset_reference.rviz >/dev/null
  CONTAINERS+=("${STACK}_rviz")
fi
sleep 8

GRAPH_COMMAND='source /opt/ros/noetic/setup.bash; source /root/catkin_ws/devel/setup.bash; printf "NODES\n"; rosnode list; for topic in /livox/lidar /livox/imu /camera/right/image_raw /camera/rgb/image_raw /lvisam/points_raw /lvisam/imu_raw /lvisam/camera/image_raw /benchmark/points_raw /benchmark/imu_raw /benchmark/camera/image_raw; do printf "\nTOPIC %s\n" "$topic"; rostopic info "$topic" || true; done'
docker run --rm "${COMMON[@]}" e2o-localization-fusion:latest bash -lc "$GRAPH_COMMAND" \
  >"$OUT_HOST/topic_graph_before_playback.txt" 2>&1 || true

PLAYER_EXIT=0
if [[ "$INPUT_KIND" == bag ]]; then
  PLAYER_COMMAND='cp /workspace/wrappers/localization_benchmark/scripts/urban_bag_player.py /root/catkin_ws/devel/.private/localization_benchmark/lib/localization_benchmark/; chmod +x /root/catkin_ws/devel/.private/localization_benchmark/lib/localization_benchmark/urban_bag_player.py; source /opt/ros/noetic/setup.bash; source /root/catkin_ws/devel/setup.bash; export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH}; exec roslaunch /workspace/wrappers/localization_benchmark/launch/urban_bag_player.launch "$@"'
  docker run --name "${STACK}_player" "${COMMON[@]}" -v "$(dirname "$INPUT_HOST"):/bags:ro" e2o-localization-fusion:latest \
    bash -lc "$PLAYER_COMMAND" _ bag_path:="/bags/$(basename "$INPUT_HOST")" rate:="$RATE" \
    start_offset:="$PLAYBACK_START" duration:="$PLAYBACK_DURATION" \
    lidar_topic:="$LIDAR_TOPIC" imu_topic:="$IMU_TOPIC" camera_topic:="$CAMERA_TOPIC" \
    enable_lidar:="$NEED_LIDAR" enable_imu:="$NEED_IMU" enable_camera:="$NEED_CAMERA" \
    2>&1 | tee "$OUT_HOST/player.log" || PLAYER_EXIT=$?
  CONTAINERS+=("${STACK}_player")
else
  PLAYER_COMMAND='cp /workspace/wrappers/localization_benchmark/scripts/boreas_player.py /root/catkin_ws/devel/.private/localization_benchmark/lib/localization_benchmark/; chmod +x /root/catkin_ws/devel/.private/localization_benchmark/lib/localization_benchmark/boreas_player.py; source /opt/ros/noetic/setup.bash; source /root/catkin_ws/devel/setup.bash; export ROS_PACKAGE_PATH=/workspace/wrappers:${ROS_PACKAGE_PATH}; exec roslaunch /workspace/wrappers/localization_benchmark/launch/boreas_player.launch "$@"'
  docker run --name "${STACK}_player" "${COMMON[@]}" -v "$INPUT_HOST:/sequence:ro" e2o-localization-fusion:latest bash -lc "$PLAYER_COMMAND" _ sequence_root:=/sequence rate:="$RATE" start_offset:="$PLAYBACK_START" duration:="$PLAYBACK_DURATION" enable_lidar:="$NEED_LIDAR" enable_imu:="$NEED_IMU" enable_camera:="$NEED_CAMERA" || PLAYER_EXIT=$?
  CONTAINERS+=("${STACK}_player")
fi
sleep 4

ALGORITHM_RUNNING="$(docker inspect -f '{{.State.Running}}' "${STACK}_algorithm" 2>/dev/null || printf false)"
# ORB-SLAM3's optimized Path is rewritten when loop closures and Atlas map
# merges finish. Stop the recorder cleanly before evaluation so its shutdown
# hook atomically selects that native optimized trajectory over the live
# map-local odometry stream. This is output finalization, not pose correction.
docker stop -t 5 "${STACK}_recorder" >/dev/null 2>&1 || true
TRAJECTORY="$OUT_HOST/${ALGORITHM}_trajectory.csv"
POSES=0
[[ -f "$TRAJECTORY" ]] && POSES=$(( $(wc -l < "$TRAJECTORY") - 1 ))
TRAJECTORY_VALID=false
if [[ "$POSES" -gt 0 ]] && python3 "$ROOT/tools/validate_trajectory.py" "$TRAJECTORY" \
    --output "$OUT_HOST/trajectory_validation.json" >/dev/null; then
  TRAJECTORY_VALID=true
fi
STATUS=failed; REASON=""
if [[ "$PLAYER_EXIT" -ne 0 ]]; then REASON="dataset player exited $PLAYER_EXIT"
elif [[ "$ALGORITHM_RUNNING" != true ]]; then REASON="algorithm process exited before playback completed"
elif [[ "$POSES" -le 0 ]]; then REASON="no trajectory poses recorded"
elif [[ "$TRAJECTORY_VALID" != true ]]; then REASON="trajectory failed finite/quaternion/monotonic validation"
else STATUS=completed; REASON="player completed; trajectory is finite and strictly monotonic"; fi
printf '{"status":"%s","reason":"%s","player_exit":%d,"trajectory_poses":%d}\n' "$STATUS" "$REASON" "$PLAYER_EXIT" "$POSES" >"$OUT_HOST/execution_status.json"

QUALITY_STATUS=not_evaluated
if [[ "$STATUS" == completed ]]; then
  if [[ "$INPUT_KIND" == bag ]]; then GT="$(dirname "$INPUT_HOST")/ground_truth.csv"; else GT="$INPUT_HOST/ground_truth.csv"; fi
  if [[ -f "$GT" ]]; then
    if python3 "$ROOT/evaluation/evaluate_public.py" --run-dir "$OUT_HOST" --gt "$GT" \
      --trajectory "$TRAJECTORY" --algorithm "$ALGORITHM" --alignment "$ALIGNMENT" \
      --alignment-reason "$ALIGNMENT_REASON" --eval-start-offset "$START_OFFSET" \
      --eval-duration "$DURATION" --sequence-start-time "$SEQUENCE_START_TIME" \
      --sequence-duration "$SEQUENCE_DURATION"; then
      QUALITY_STATUS=accepted
    else
      QUALITY_STATUS="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["status"])' \
        "$OUT_HOST/quality_status.json" 2>/dev/null || printf rejected)"
    fi
  else
    printf 'Ground truth not converted yet: %s\n' "$GT" >&2
  fi
fi
printf 'status=%s quality=%s poses=%d output=%s\n' "$STATUS" "$QUALITY_STATUS" "$POSES" "$OUT_HOST"
[[ "$STATUS" == completed && "$QUALITY_STATUS" == accepted ]]
