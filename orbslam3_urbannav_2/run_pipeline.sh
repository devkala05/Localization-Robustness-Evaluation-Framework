#!/bin/bash
# ============================================================
# run_pipeline.sh  —  Launch the complete ORB-SLAM3 pipeline
#                     in a tmux session (inside container)
# ============================================================
# Usage (inside container):
#   bash run_pipeline.sh /data/UrbanNav-HK_TST-20210517_sensors.bag mono
#   bash run_pipeline.sh /data/UrbanNav-HK_TST-20210517_sensors.bag stereo
#
# Pane layout:
#   Window 0:
#   ┌─────────────────────┬──────────────────────┐
#   │  0: roscore         │  1: wrapper          │
#   ├─────────────────────┼──────────────────────┤
#   │  2: ORB-SLAM3       │  3: rosbag play      │
#   └─────────────────────┴──────────────────────┘
#   Window 1:
#   ┌─────────────────────┬──────────────────────┐
#   │  0: rviz            │  1: verify_topics    │
#   └─────────────────────┴──────────────────────┘
# ============================================================
set -euo pipefail

BAG_PATH="${1:-/data/UrbanNav-HK_TST-20210517_sensors.bag}"
MODE="${2:-mono}"
SESSION="orbslam3"
SETUP="source /opt/ros/noetic/setup.bash && source /root/catkin_ws/devel/setup.bash"
ROS_ENV="export ROS_MASTER_URI=http://localhost:11311 && export ROS_HOSTNAME=localhost"
ORB_ENV="export ROS_PACKAGE_PATH=\${ROS_PACKAGE_PATH}:/root/ORB_SLAM3/Examples_old/ROS"

if [ ! -f "${BAG_PATH}" ]; then
    echo "ERROR: Bag not found: ${BAG_PATH}"
    echo "Usage: $0 /data/UrbanNav-HK_TST-20210517_sensors.bag"
    exit 1
fi

if [ "${MODE}" != "mono" ] && [ "${MODE}" != "stereo" ]; then
    echo "ERROR: Mode must be 'mono' or 'stereo' (got: ${MODE})"
    exit 1
fi

echo "═══════════════════════════════════════════════════════"
echo "  Launching ORB-SLAM3 UrbanNav Pipeline"
echo "  Bag: ${BAG_PATH}"
echo "  Mode: ${MODE}"
echo "═══════════════════════════════════════════════════════"

tmux kill-session -t "${SESSION}" 2>/dev/null || true
tmux new-session -d -s "${SESSION}" -x 220 -y 50

# ── Pane 0: roscore ───────────────────────────────────────────────────────────
tmux send-keys -t "${SESSION}:0" \
    "${SETUP} && ${ROS_ENV} && roscore" Enter
sleep 3

# ── Pane 1: Wrapper (TF + camera converter + pose republisher) ────────────────
tmux split-window -h -t "${SESSION}:0"
tmux send-keys -t "${SESSION}:0.1" \
    "${SETUP} && ${ROS_ENV} && \
     roslaunch orbslam3_urbannav urbannav_wrapper.launch" Enter
sleep 4

# ── Pane 2: ORB-SLAM3 ─────────────────────────────────────────────────────────
tmux split-window -v -t "${SESSION}:0.0"
tmux send-keys -t "${SESSION}:0.2" \
    "${SETUP} && ${ROS_ENV} && ${ORB_ENV} && \
     roslaunch orbslam3_urbannav orbslam3_urbannav.launch mode:=${MODE}" Enter
sleep 3

# ── Pane 3: rosbag play (camera only) ────────────────────────────────────────
tmux split-window -v -t "${SESSION}:0.1"
tmux send-keys -t "${SESSION}:0.3" \
    "${SETUP} && ${ROS_ENV} && \
     if [ \"${MODE}\" = \"stereo\" ]; then \
       rosbag play --clock --rate 1.0 ${BAG_PATH} --topics \
         /zed2/camera/left/image_raw /zed2/camera/left/camera_info \
         /zed2/camera/right/image_raw /zed2/camera/right/camera_info; \
     else \
       rosbag play --clock --rate 1.0 ${BAG_PATH} --topics \
         /zed2/camera/right/image_raw /zed2/camera/right/camera_info; \
     fi" Enter

# ── Window 1: RViz + verification ─────────────────────────────────────────────
tmux new-window -t "${SESSION}"
tmux send-keys -t "${SESSION}:1" \
    "${SETUP} && ${ROS_ENV} && \
     rviz -d \$(rospack find orbslam3_urbannav)/config/orbslam3_urbannav.rviz" Enter

tmux split-window -v -t "${SESSION}:1"
tmux send-keys -t "${SESSION}:1.1" \
    "${SETUP} && ${ROS_ENV} && \
     sleep 12 && rosrun orbslam3_urbannav verify_topics.py _timeout:=20" Enter

echo ""
echo "Attaching to tmux session '${SESSION}' …"
echo "  Window 0: roscore | wrapper | orb-slam3 | bag"
echo "  Window 1: rviz | verify_topics"
echo "Detach: Ctrl-B d"
echo ""

tmux attach-session -t "${SESSION}:0"
