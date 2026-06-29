#!/usr/bin/env bash
set -u
OUT="${1:-/tmp/e2o_diagnostics_$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$OUT"
run() { local name="$1"; shift; { echo "+ $*"; "$@"; } >"$OUT/$name.txt" 2>&1 || true; }
run rostopic_list rostopic list
run rosnode_list rosnode list
run fast_rate rostopic hz -w 20 /fast_livo2/odometry
run orb_rate rostopic hz -w 20 /orbslam3/camera_odometry
run fused_rate rostopic hz -w 20 /fused_localization/odometry
run fused_status rostopic echo -n 1 /fused_localization/status
run health rostopic echo -n 1 /localization_health/summary
run fast_node rosnode info /laserMapping
run orb_node rosnode info /orbslam3_mono
run roswtf roswtf
run rqt_graph_snapshot rosrun rqt_graph rqt_graph --force-discover
run frames rosrun tf2_tools view_frames.py
[[ -f frames.pdf ]] && mv frames.pdf "$OUT/frames.pdf"
echo "$OUT"
