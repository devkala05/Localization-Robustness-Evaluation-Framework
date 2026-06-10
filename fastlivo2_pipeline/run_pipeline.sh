#!/bin/bash
# ============================================================
# run_pipeline.sh
# ============================================================
# Single-command automation for the FAST-LIVO2 black-box test:
#
#   rosbag → topic bridge → FAST-LIVO2 → record outputs
#          → save results → export trajectory
#
# Usage (inside the container or native workspace):
#   ./run_pipeline.sh /data/your_dataset.bag [rate] [start_delay]
#
# Examples:
#   ./run_pipeline.sh /data/UrbanNav-HK-TST-20210517_sensors.bag
#   ./run_pipeline.sh /data/my.bag 0.5 10
#
# Pane layout (tmux):
#   Window 0 ─────────────────────────────────────────
#   ┌─────────────────────┬──────────────────────────┐
#   │  [0] roscore        │  [1] bridge              │
#   ├─────────────────────┼──────────────────────────┤
#   │  [2] FAST-LIVO2     │  [3] recorder            │
#   └─────────────────────┴──────────────────────────┘
#   Window 1 ─────────────────────────────────────────
#   ┌─────────────────────┬──────────────────────────┐
#   │  [4] rosbag play    │  [5] RViz                │
#   ├─────────────────────┼──────────────────────────┤
#   │  [6] verify_topics  │  [7] exporter (post-run) │
#   └─────────────────────┴──────────────────────────┘
# ============================================================
set -euo pipefail

# ── Arguments ────────────────────────────────────────────────────────────────
BAG_PATH="${1:-/data/UrbanNav-HK-TST-20210517_sensors.bag}"
RATE="${2:-1.0}"
START_DELAY="${3:-8.0}"

# ── Config ───────────────────────────────────────────────────────────────────
SESSION="fastlivo2"
OUTPUT_DIR="/data/output"
SETUP="source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash"
ROS_ENV="export ROS_MASTER_URI=http://localhost:11311 && export ROS_HOSTNAME=localhost"
PKG="fast_livo2_wrapper"

# ── Validation ───────────────────────────────────────────────────────────────
if [ ! -f "${BAG_PATH}" ]; then
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  ERROR: Bag file not found                                   ║"
    echo "║  Expected: ${BAG_PATH}"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo "Usage: $0 /data/your_bag.bag [rate] [start_delay_secs]"
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       FAST-LIVO2 Black-Box Testing Pipeline                  ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Bag:          ${BAG_PATH}"
echo "║  Rate:         ${RATE}x"
echo "║  Start delay:  ${START_DELAY}s"
echo "║  Output dir:   ${OUTPUT_DIR}"
echo "╚══════════════════════════════════════════════════════════════╝"

# Kill any previous session
tmux kill-session -t "${SESSION}" 2>/dev/null || true

# Create new 2-window session
tmux new-session -d -s "${SESSION}" -x 220 -y 60

# ════════════════════════════════════════════════════════════════
# Window 0: Core pipeline
# ════════════════════════════════════════════════════════════════

# Pane 0: roscore
tmux send-keys -t "${SESSION}:0.0" \
    "${SETUP} && ${ROS_ENV} && roscore" Enter

sleep 2

# Pane 1: Topic bridge (TF broadcaster + UrbanNav→FAST-LIVO2 converter)
tmux split-window -h -t "${SESSION}:0"
tmux send-keys -t "${SESSION}:0.1" \
    "${SETUP} && ${ROS_ENV} && \
     sleep 2 && \
     roslaunch ${PKG} topic_bridge.launch" Enter

sleep 2

# Pane 2: FAST-LIVO2 (black-box algorithm)
tmux split-window -v -t "${SESSION}:0.0"
tmux send-keys -t "${SESSION}:0.2" \
    "${SETUP} && ${ROS_ENV} && \
     sleep 4 && \
     roslaunch ${PKG} fast_livo2.launch" Enter

# Pane 3: Output recorder
tmux split-window -v -t "${SESSION}:0.1"
tmux send-keys -t "${SESSION}:0.3" \
    "${SETUP} && ${ROS_ENV} && \
     sleep 4 && \
     roslaunch ${PKG} record_outputs.launch \
         output_dir:=${OUTPUT_DIR}" Enter

# ════════════════════════════════════════════════════════════════
# Window 1: Playback, visualisation, verification
# ════════════════════════════════════════════════════════════════
tmux new-window -t "${SESSION}" -n "viz+bag"

# Pane 4: Rosbag playback — only the three allowed sensor streams
tmux send-keys -t "${SESSION}:1.0" \
    "${SETUP} && ${ROS_ENV} && \
     sleep ${START_DELAY} && \
     rosbag play --clock --rate ${RATE} \
         --topics /velodyne_points /imu/data /zed2/camera/right/image_raw \
         ${BAG_PATH}" Enter

# Pane 5: RViz
tmux split-window -h -t "${SESSION}:1"
tmux send-keys -t "${SESSION}:1.1" \
    "${SETUP} && ${ROS_ENV} && \
     sleep 6 && \
     rviz -d \$(rospack find ${PKG})/config/fast_livo2.rviz" Enter

# Pane 6: Topic verifier
tmux split-window -v -t "${SESSION}:1.0"
tmux send-keys -t "${SESSION}:1.2" \
    "${SETUP} && ${ROS_ENV} && \
     sleep 12 && \
     rosrun ${PKG} verify_topics.py _timeout:=30.0" Enter

# Pane 7: Trajectory exporter (runs after bag finishes)
tmux split-window -v -t "${SESSION}:1.1"
tmux send-keys -t "${SESSION}:1.3" \
    "${SETUP} && ${ROS_ENV} && \
     echo 'Waiting for bag to finish, then exporting trajectory …' && \
     sleep 9999 && \
     python3 \$(rospack find ${PKG})/scripts/trajectory_exporter.py \
         --bag ${OUTPUT_DIR}/fast_livo2_output.bag \
         --output_dir ${OUTPUT_DIR} --format all" Enter

# ── Attach ───────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Attaching to tmux session: ${SESSION}"
echo "║  Window 0: roscore | bridge | fastlivo2 | recorder"
echo "║  Window 1: bag | rviz | verify | exporter"
echo "║"
echo "║  Detach:  Ctrl-B  d"
echo "║  Results: ${OUTPUT_DIR}/"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

tmux attach-session -t "${SESSION}:0"
