#!/bin/bash
set -euo pipefail

PER="${1:-0}"
ATTACH="${2:---attach}"
ALGO="${3:-fastlio2}"
ROS_PORT="${ROS_PORT:-11311}"
ROS_MASTER_URI_VALUE="http://localhost:${ROS_PORT}"

if ! [[ "${PER}" =~ ^[0-6]$ ]]; then
    echo "ERROR: --per must be a number from 0 to 6"
    exit 2
fi

ALGO_CONFIG="/root/catkin_ws/src/localization_benchmark/config/algorithms.yaml"
eval "$(python3 /workspace/scripts/algorithm_config.py --config "${ALGO_CONFIG}" --algo "${ALGO}")"

if [ -z "${ALGO_LAUNCH}" ] || [ -z "${ALGO_OUTPUT_TOPIC}" ]; then
    echo "ERROR: ${ALGO_ID} must define launch and output_topic in ${ALGO_CONFIG}"
    exit 2
fi

DATASET_ID="${DATASET_ID:-urbannav}"
RESULTS_BASE="${RESULTS_BASE:-/data/results}"
DATASET_RESULTS_ROOT="${DATASET_RESULTS_ROOT:-${RESULTS_BASE}/${DATASET_ID}}"
DATASET_FRAME_ID="${DATASET_FRAME_ID:-camera_init}"
DATASET_LIDAR_MODEL="${DATASET_LIDAR_MODEL:-velodyne_32}"
DATASET_SCAN_LINE="${DATASET_SCAN_LINE:-32}"
DATASET_USE_CLOCK_STAMP="${DATASET_USE_CLOCK_STAMP:-false}"
DATASET_CAMERA_FRAME="${DATASET_CAMERA_FRAME:-camera_right_optical}"
DATASET_PERTURBATIONS_DIR="${DATASET_PERTURBATIONS_DIR:-/root/catkin_ws/src/localization_benchmark/config/perturbations}"
DATASET_SEGMENTS_YAML="${DATASET_SEGMENTS_YAML:-/root/catkin_ws/src/localization_benchmark/config/road_segments.yaml}"
ALGO_BAG_TOPICS="${DATASET_BAG_TOPICS:-${ALGO_BAG_TOPICS}}"
if [ -z "${ALGO_BAG_TOPICS}" ]; then
    ALGO_BAG_TOPICS="/velodyne_points /imu/data /zed2/camera/right/image_raw"
fi

GPS_ENABLE="${GPS_ENABLE:-off}"
case "${GPS_ENABLE}" in
    on|true|1|yes) GPS_BOOL="true"; GPS_FOLDER="with_gps" ;;
    off|false|0|no) GPS_BOOL="false"; GPS_FOLDER="without_gps" ;;
    *) echo "ERROR: GPS_ENABLE/GPS --gps must be on/off"; exit 2 ;;
esac
STAMP="$(date +%Y-%m-%d_%H-%M-%S)"
SESSION="${DATASET_ID}_${ALGO_RESULT_ID}_${GPS_FOLDER}_per_${PER}"
SETUP="source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash"
ROS_ENV="export ROS_MASTER_URI=${ROS_MASTER_URI_VALUE} && export ROS_HOSTNAME=localhost"
BAG_PATH="${BAG_PATH_OVERRIDE:-/data/UrbanNav-HK_TST-20210517_sensors.bag}"
BAG_RATE="${BAG_RATE:-0.5}"
GT_YAW_OFFSET_DEG="${GT_YAW_OFFSET_DEG:-0.0}"
GT_PATH="${GT_PATH_OVERRIDE:-/data/UrbanNav_TST_GT_raw.txt}"
CONFIG_PATH="${DATASET_PERTURBATIONS_DIR:-/root/catkin_ws/src/localization_benchmark/config/perturbations}/per_${PER}.yaml"
RESULT_GROUP_DIR="${DATASET_RESULTS_ROOT}/${ALGO_RESULT_ID}/${GPS_FOLDER}"
PERTURBATION_RESULT_DIR="${RESULT_GROUP_DIR}/per_${PER}"
RESULT_DIR="${PERTURBATION_RESULT_DIR}/${STAMP}"
BASELINE_CSV=""
BASELINE_ROOT="${RESULT_GROUP_DIR}/per_0"
if [ -d "${BASELINE_ROOT}" ]; then
    BASELINE_LATEST="$(find "${BASELINE_ROOT}" -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1)"
    if [ -n "${BASELINE_LATEST}" ] && [ -f "${BASELINE_LATEST}/trajectory.csv" ]; then
        BASELINE_CSV="${BASELINE_LATEST}/trajectory.csv"
    fi
fi
RVIZ_CONFIG="${ALGO_RVIZ_CONFIG:-/root/catkin_ws/src/localization_benchmark/config/benchmark_paths.rviz}"
GPS_SOURCE="${GPS_SOURCE:-auto}"
GPS_FILE="${GPS_FILE:-}"
GPS_TOPIC="${GPS_TOPIC:-/gps/fix_raw}"
GPS_REQUIRED="${GPS_REQUIRED:-false}"
GPS_USE_Z="${GPS_USE_Z:-off}"
GPS_ALPHA="${GPS_ALPHA:-0.08}"
GPS_MAX_COV_XY="${GPS_MAX_COV_XY:-100.0}"
GPS_MAX_COV_Z="${GPS_MAX_COV_Z:-400.0}"
GPS_TIME_OFFSET_SEC="${GPS_TIME_OFFSET_SEC:-0.0}"
case "${GPS_USE_Z}" in
    on|true|1|yes) GPS_USE_Z_BOOL="true" ;;
    *) GPS_USE_Z_BOOL="false" ;;
esac

append_unique_topic() {
    local list="$1"
    local topic="$2"
    [ -z "$topic" ] && { echo "$list"; return; }
    case " $list " in
        *" $topic "*) echo "$list" ;;
        *) echo "${list} ${topic}" ;;
    esac
}

# When GPS is replayed from a bag topic (E2O), include that NavSatFix topic in
# rosbag play. Without this, --gps on can silently save under with_gps while
# output_selector only falls back to local odometry. CSV GPS sources do not need
# an extra bag topic because gnss_solution_replayer publishes /gps/fix_raw from file.
if [ "${GPS_BOOL}" = "true" ] && [ "${GPS_SOURCE}" = "topic" ]; then
    ALGO_BAG_TOPICS="$(append_unique_topic "${ALGO_BAG_TOPICS:-}" "${GPS_TOPIC:-}")"
fi


source /opt/ros/noetic/setup.bash
cd /root/catkin_ws
if [ "${SKIP_RUNTIME_BUILD:-false}" = "true" ]; then
    source /root/catkin_ws/devel/setup.bash
    for pkg in ${ALGO_BUILD_PACKAGES}; do
        rospack find "${pkg}" >/dev/null || {
            echo "ERROR: --skip-build was used, but ROS package '${pkg}' is not available."
            echo "Build this image once without --skip-build."
            exit 1
        }
    done
else
    echo "[benchmark] runtime_build algo=${ALGO_DISPLAY}"
    catkin build ${ALGO_BUILD_PACKAGES} -j"${ALGO_BUILD_JOBS}" -p"${ALGO_BUILD_JOBS}" >/tmp/localization_build.log || {
        echo "ERROR: failed to build packages for ${ALGO_DISPLAY}: ${ALGO_BUILD_PACKAGES}"
        echo "Check /tmp/localization_build.log inside the container."
        exit 1
    }
    source /root/catkin_ws/devel/setup.bash
fi

test -f "${BAG_PATH}"
test -f "${GT_PATH}"
test -f "${CONFIG_PATH}"
mkdir -p "${RESULTS_BASE}/analysis" "${RESULTS_BASE}/e2o" "${RESULTS_BASE}/urbannav" "${RESULT_DIR}"

if [ "${ALGO_STANDARD_NS}" = "rtabmap" ]; then
    RTABMAP_DATABASE_PATH="${RESULT_DIR}/rtabmap.db"
    rm -f "${RTABMAP_DATABASE_PATH}"
    ALGO_LAUNCH_ARGS="${ALGO_LAUNCH_ARGS} rtabmap_database_path:=${RTABMAP_DATABASE_PATH} delete_db_on_start:=true"
fi

if [ "${ALGO_STANDARD_NS}" = "r3live" ]; then
    # Always run native r3live_mapping. The LiDAR-front-end-only executable uses
    # livox_ros_driver/CustomMsg on some upstream builds, while r3live_mapping
    # consumes sensor_msgs/PointCloud2 after the adapter converts Velodyne scans to
    # PCL PointXYZINormal with R3LIVE-compatible millisecond curvature timestamps.
    case "${R3LIVE_RUN_VISUAL:-true}" in
        off|false|0|no) R3LIVE_VISUAL_BOOL="false" ;;
        *) R3LIVE_VISUAL_BOOL="true" ;;
    esac
    ALGO_LAUNCH_ARGS="enable_fastlio_fallback:=false run_visual:=${R3LIVE_VISUAL_BOOL} native_role:=mapping dataset_id:=${DATASET_ID} lidar_type:=2"
fi

if [ "${ALGO_STANDARD_NS}" = "lvisam" ] && [ "${DATASET_ID}" = "e2o" ]; then
    # Keep LVISAM visual frontend enabled. The old scan-line based branch
    # disabled run_visual for every 16-line dataset, reducing LVI-SAM to
    # LiDAR-IMU and breaking the visual/lidar frame consistency.
    ALGO_LAUNCH_ARGS="${ALGO_LAUNCH_ARGS} lidar_param_file:=/root/catkin_ws/src/lvi_sam_urbannav/config/lvisam_e2o.yaml"
    ALGO_LAUNCH_ARGS="${ALGO_LAUNCH_ARGS} vins_param_file:=/root/catkin_ws/src/lvi_sam_urbannav/config/params_camera_e2o_front.yaml"
fi

STD_EXTRA_ARGS=""
if [ "${ALGO_STANDARD_NS}" = "lvisam" ]; then
    # Do not rotate only the benchmark odometry to GT in RViz. LVISAM's native
    # map/cloud/path are in odom/map; evaluation aligns trajectories offline.
    STD_EXTRA_ARGS="_align_to_gt:=false _rebase_origin:=false _fixed_frame:=odom _preserve_native_child_frame:=true"
fi

case "${ALGO_STANDARD_NS}" in
    fastlio2|fastlivo2|r3live)
        ALGO_LAUNCH_ARGS="${ALGO_LAUNCH_ARGS} scan_line:=${DATASET_SCAN_LINE}"
        ;;
esac

# Dataset-specific algorithm configs. UrbanNav remains the default path; E2O
# intentionally uses the working lidar103/body-reference configs from
# e2o_work_example instead of the previous /merged cloud setup.
if [ "${DATASET_ID}" = "e2o" ]; then
    case "${ALGO_STANDARD_NS}" in
        fastlio2)
            ALGO_LAUNCH_ARGS="${ALGO_LAUNCH_ARGS} config_path:=/root/catkin_ws/src/fast_lio_urbannav/config/velodyne_e2o.yaml"
            ;;
        fastlivo2)
            ALGO_LAUNCH_ARGS="${ALGO_LAUNCH_ARGS} config_path:=/root/catkin_ws/src/fast_livo2_wrapper/config/fast_livo2_e2o.yaml img_en:=1 lidar_en:=1 imu_en:=true"
            ;;
        rtabmap)
            # Standalone RTAB-Map ICP uses the common raw/perturbed scan_cloud topic.
            # No FAST-LIO2 config or scan_line argument is passed.
            ;;
        adaptive_w_lvio)
            if [ "${ADAPTIVE_LVIO_MONO_DEPTH:-false}" = "true" ]; then
                ALGO_LAUNCH_ARGS="${ALGO_LAUNCH_ARGS} use_native_lvio_fusion:=true config_file:=/root/catkin_ws/src/adaptive_w_lvio_urbannav/config/lvio_fusion_e2o_mono_depth.yaml"
            else
                ALGO_LAUNCH_ARGS="${ALGO_LAUNCH_ARGS} use_native_lvio_fusion:=false"
            fi
            ;;
        r3live)
            ALGO_LAUNCH_ARGS="${ALGO_LAUNCH_ARGS} config_path:=/root/catkin_ws/src/r3live_urbannav/config/r3live_e2o.yaml"
            ;;
        orbslam3)
            ALGO_LAUNCH_ARGS="${ALGO_LAUNCH_ARGS} mode:=mono mono_camera_config:=/root/catkin_ws/src/orbslam3_urbannav/config/e2o_front_mono_orbslam3.yaml use_camera_to_body_extrinsic:=true pose_scale:=${ORB_MONO_SCALE:-${DATASET_ORB_MONO_SCALE:-1.0}} yaw_offset_deg:=${ORB_YAW_OFFSET_DEG:-${DATASET_ORB_YAW_OFFSET_DEG:-0.0}} align_to_gt:=${ORB_ALIGN_TO_GT:-false} dataset_id:=${DATASET_ID}"
            ;;
    esac
fi

tmux kill-session -t "${SESSION}" 2>/dev/null || true
tmux new-session -d -s "${SESSION}" -x 240 -y 60

tmux rename-window -t "${SESSION}:0" "run"
ROSCORE_PANE="${SESSION}:0.0"
tmux send-keys -t "${ROSCORE_PANE}" "${SETUP} && ${ROS_ENV} && roscore -p ${ROS_PORT}" Enter
sleep 3
export ROS_MASTER_URI=${ROS_MASTER_URI_VALUE}
export ROS_HOSTNAME=localhost
rosparam set /use_sim_time true

TF_PANE="$(tmux split-window -h -t "${ROSCORE_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${TF_PANE}" "${SETUP} && ${ROS_ENV} && ${ALGO_TF_COMMAND} _dataset_id:=${DATASET_ID}" Enter

BRIDGE_PANE="$(tmux split-window -v -t "${ROSCORE_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${BRIDGE_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark custom_bridge.launch dataset:=${DATASET_NAME:-${DATASET_ID}} source_lidar_topic:=${DATASET_SOURCE_LIDAR_TOPIC:-/velodyne_points} source_imu_topic:=${DATASET_SOURCE_IMU_TOPIC:-/imu/data} source_camera_topic:=${DATASET_SOURCE_CAMERA_TOPIC:-/zed2/camera/right/image_raw} source_left_camera_topic:=${DATASET_SOURCE_LEFT_CAMERA_TOPIC:-} use_clock_stamp:=${DATASET_USE_CLOCK_STAMP:-false} lidar_sensor_name:=${DATASET_LIDAR_FRAME:-velodyne} imu_sensor_name:=${DATASET_IMU_FRAME:-body} camera_sensor_name:=camera_right left_camera_sensor_name:=camera_left monotonic_clock_stamp:=true min_stamp_step_sec:=0.000001" Enter

ADAPTER_PANE="$(tmux split-window -v -t "${TF_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${ADAPTER_PANE}" "${SETUP} && ${ROS_ENV} && ${ALGO_ADAPTER_LAUNCH} run_id:=${PER} perturbation_config:=${CONFIG_PATH} native_lidar_topic:=${ALGO_NATIVE_LIDAR_TOPIC} native_imu_topic:=${ALGO_NATIVE_IMU_TOPIC} native_camera_topic:=${ALGO_NATIVE_CAMERA_TOPIC} point_time_scale:=${ALGO_POINT_TIME_SCALE} ring_count:=${DATASET_SCAN_LINE} camera_right_k:='${DATASET_CAMERA_RIGHT_K:-}' camera_right_d:='${DATASET_CAMERA_RIGHT_D:-}' camera_left_k:='${DATASET_CAMERA_LEFT_K:-}' camera_left_d:='${DATASET_CAMERA_LEFT_D:-}' camera_frame_id:=${DATASET_CAMERA_FRAME:-camera_right_optical} ${ALGO_ADAPTER_ARGS}" Enter

ALGO_PANE="$(tmux new-window -t "${SESSION}" -n "algo" -P -F "#{pane_id}")"
tmux send-keys -t "${ALGO_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch ${ALGO_LAUNCH} ${ALGO_LAUNCH_ARGS}" Enter

STD_PANE="$(tmux split-window -h -t "${ALGO_PANE}" -P -F "#{pane_id}")"
STD_PUBLISH_TF=true
# RTAB-Map and Adaptive-W already publish or manage their own local frame outputs.
# Keep BenchmarkOutput TF off for them to avoid duplicate camera_init->body authority
# and TF_REPEATED_DATA warnings.
if [ "${ALGO_STANDARD_NS}" = "rtabmap" ] || [ "${ALGO_STANDARD_NS}" = "adaptive_w_lvio" ] || [ "${ALGO_STANDARD_NS}" = "lvisam" ] || [ "${ALGO_STANDARD_NS}" = "r3live" ]; then
    STD_PUBLISH_TF=false
fi
tmux send-keys -t "${STD_PANE}" "${SETUP} && ${ROS_ENV} && rosrun localization_benchmark standard_output_republisher.py _source_topic:=${ALGO_OUTPUT_TOPIC} _algo_ns:=${ALGO_STANDARD_NS} _local_odom_topic:=${ALGO_LOCAL_ODOM_TOPIC} _local_path_topic:=${ALGO_LOCAL_PATH_TOPIC} _output_odom_topic:=${ALGO_SELECTED_OUTPUT_TOPIC} _output_path_topic:=${ALGO_SELECTED_PATH_TOPIC} _status_topic:=/${ALGO_STANDARD_NS}/benchmark_status _gps_enabled:=${GPS_BOOL} _publish_tf:=${STD_PUBLISH_TF:-true} _tf_child_frame:=body ${STD_EXTRA_ARGS}" Enter

GPS_PANE="$(tmux split-window -v -t "${STD_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${GPS_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark gps_provider.launch gps_enable:=${GPS_BOOL} gps_source:=${GPS_SOURCE} gps_file:=${GPS_FILE} gps_topic:=${GPS_TOPIC} gps_required:=${GPS_REQUIRED} max_cov_xy:=${GPS_MAX_COV_XY} max_cov_z:=${GPS_MAX_COV_Z} frame_id:=gnss_antenna time_offset_sec:=${GPS_TIME_OFFSET_SEC} && true" Enter

SELECT_PANE="$(tmux new-window -t "${SESSION}" -n "select_record" -P -F "#{pane_id}")"
tmux send-keys -t "${SELECT_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark gps_fusion.launch gps_enable:=${GPS_BOOL} algo_ns:=${ALGO_STANDARD_NS} local_odom_topic:=${ALGO_LOCAL_ODOM_TOPIC} gps_fix_topic:=/gps/fix imu_topic:=${ALGO_NATIVE_IMU_TOPIC} output_odom_topic:=${ALGO_SELECTED_OUTPUT_TOPIC} output_path_topic:=${ALGO_SELECTED_PATH_TOPIC} status_topic:=${ALGO_STATUS_TOPIC} use_z:=${GPS_USE_Z_BOOL} position_alpha:=${GPS_ALPHA}" Enter
RECORDER_PANE="$(tmux split-window -h -t "${SELECT_PANE}" -P -F "#{pane_id}")"
tmux send-keys -t "${RECORDER_PANE}" "${SETUP} && ${ROS_ENV} && roslaunch localization_benchmark record_output.launch algorithm:=${ALGO_RESULT_ID} run_id:=${PER} source_topic:=${ALGO_SELECTED_OUTPUT_TOPIC} csv_path:=${RESULT_DIR}/trajectory.csv" Enter

BAG_PANE="$(tmux new-window -t "${SESSION}" -n "bag" -P -F "#{pane_id}")"
tmux send-keys -t "${BAG_PANE}" "${SETUP} && ${ROS_ENV} && echo 'Waiting 8s for bridge, adapter, algorithm, output selector, recorder, and RViz...' && echo 'Press Space here to pause/resume rosbag.' && sleep 8 && rosbag play --clock --rate ${BAG_RATE} ${BAG_PATH} --topics ${ALGO_BAG_TOPICS}" Enter

STATUS_PANE="$(tmux new-window -t "${SESSION}" -n "status" -P -F "#{pane_id}")"
tmux send-keys -t "${STATUS_PANE}" "${SETUP} && ${ROS_ENV} && watch -n 2 'echo RESULT; [ -f ${RESULT_DIR}/trajectory.csv ] && wc -l ${RESULT_DIR}/trajectory.csv || true; echo; echo LOCAL ${ALGO_LOCAL_ODOM_TOPIC}; echo OUTPUT ${ALGO_SELECTED_OUTPUT_TOPIC}; echo GPS ${GPS_BOOL} ${GPS_SOURCE}; echo; echo TOPICS; rostopic list | egrep \"velodyne_points|mycar|cloud_registered|livox|Odometry|odometry|path$|camera/right|camera/image|ground_truth|gps\" || true; echo; echo RATES; timeout 1 rostopic hz ${ALGO_NATIVE_LIDAR_TOPIC} ${ALGO_NATIVE_IMU_TOPIC} ${ALGO_LOCAL_ODOM_TOPIC} ${ALGO_SELECTED_OUTPUT_TOPIC} /camera/right/image_raw /camera/image_raw /gps/fix 2>/dev/null || true'" Enter

RVIZ_PANE="$(tmux new-window -t "${SESSION}" -n "rviz" -P -F "#{pane_id}")"
tmux send-keys -t "${RVIZ_PANE}" "${SETUP} && ${ROS_ENV} && rosrun fast_lio_urbannav ground_truth_path_node.py _ground_truth_path:=${GT_PATH} _topic:=/ground_truth_path _odom_topic:=/ground_truth_odometry _frame_id:=${DATASET_FRAME_ID} _publish_rate:=10.0 _yaw_offset_deg:=${GT_YAW_OFFSET_DEG} _publish_full_path:=true & rosrun localization_benchmark bag_clock_marker.py _frame_id:=${DATASET_FRAME_ID} & if [ -n '${BASELINE_CSV}' ] && [ -f '${BASELINE_CSV}' ]; then rosrun localization_benchmark path_from_csv.py _csv_path:=${BASELINE_CSV} _topic:=/benchmark/baseline_path _frame_id:=${DATASET_FRAME_ID} & fi; rosrun localization_benchmark path_from_csv.py _csv_path:=${RESULT_DIR}/trajectory.csv _topic:=/benchmark/selected_run_path _frame_id:=${DATASET_FRAME_ID} & LIBGL_ALWAYS_SOFTWARE=1 MESA_LOADER_DRIVER_OVERRIDE=llvmpipe rviz -d ${RVIZ_CONFIG}" Enter

tmux select-window -t "${SESSION}:5"
echo "[benchmark] mode=interactive dataset=${DATASET_ID} algo=${ALGO_DISPLAY} key=${ALGO_ID} case=per_${PER}"
echo "[benchmark] launch=roslaunch ${ALGO_LAUNCH} ${ALGO_LAUNCH_ARGS}"
echo "[benchmark] topics native=${ALGO_OUTPUT_TOPIC} selected=${ALGO_SELECTED_OUTPUT_TOPIC}"
echo "[benchmark] lidar=${DATASET_LIDAR_MODEL} scan_line=${DATASET_SCAN_LINE}"
echo "[benchmark] gps=${GPS_BOOL} folder=${GPS_FOLDER} source=${GPS_SOURCE} file=${GPS_FILE:-none}"
echo "[benchmark] result_dir=${RESULT_DIR}"
echo "[benchmark] csv=${RESULT_DIR}/trajectory.csv"
echo "[benchmark] tmux=run,algo,select_record,bag,status,rviz detach=Ctrl-B-d"
if [ "${ATTACH}" = "--attach" ]; then
    tmux attach-session -t "${SESSION}:5"
fi
