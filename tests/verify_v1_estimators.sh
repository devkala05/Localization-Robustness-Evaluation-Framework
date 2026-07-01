#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
V1="$(cd "$ROOT/../v1" && pwd)"
RUNTIME_DIR="${1:-}"

pass() { printf 'PASS: %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }

cmp -s "$V1/wrappers/fast_livo2_wrapper/config/fast_livo2_e2o.yaml" \
  "$ROOT/wrappers/fast_livo2_e2o/config/fast_livo2_e2o.yaml" || fail "FAST-LIVO2 E2O config differs from v1"
pass "FAST-LIVO2 E2O config matches v1"
grep -q '^DepthMapFactor:' "$ROOT/wrappers/orbslam3_e2o/config/e2o_front_mono_orbslam3.yaml" || fail "ORB-SLAM3 RGB-D config missing depth factor"
pass "ORB-SLAM3 E2O config is RGB-D"
cmp -s "$V1/wrappers/fast_livo2_wrapper/scripts/odometry_alias_node.py" \
  "$ROOT/wrappers/fast_livo2_e2o/scripts/odometry_alias_node.py" || fail "FAST odometry adapter differs from v1"
pass "FAST odometry adapter matches v1"

docker image inspect fastlivo2-e2o:latest >/dev/null || fail "fastlivo2-e2o image missing"
docker image inspect orbslam3-e2o:latest >/dev/null || fail "orbslam3-e2o image missing"
pass "estimator images exist"

FAST_EXPECTED="$(sed -n 's/^ARG FAST_LIVO2_REF=//p' "$ROOT/docker/fastlivo2/Dockerfile")"
ORB_EXPECTED="$(sed -n 's/^ARG ORB_SLAM3_REF=//p' "$ROOT/docker/orbslam3/Dockerfile")"
FAST_ACTUAL="$(docker run --rm fastlivo2-e2o:latest git -C /root/catkin_ws/src/FAST-LIVO2 rev-parse HEAD)"
ORB_ACTUAL="$(docker run --rm orbslam3-e2o:latest git -C /root/ORB_SLAM3 rev-parse HEAD)"
[[ "$FAST_ACTUAL" == "$FAST_EXPECTED" ]] || fail "FAST image commit $FAST_ACTUAL != $FAST_EXPECTED"
[[ "$ORB_ACTUAL" == "$ORB_EXPECTED" ]] || fail "ORB image commit $ORB_ACTUAL != $ORB_EXPECTED"
pass "native source commits match Docker locks"

docker run --rm fastlivo2-e2o:latest bash -c \
  'source /root/catkin_ws/devel/setup.bash; rospack find fast_livo >/dev/null; test -x /root/catkin_ws/devel/lib/fast_livo/fastlivo_mapping' || fail "FAST native executable unavailable"
pass "FAST native package and executable are available"
docker run --rm orbslam3-e2o:latest bash -c \
  'test -x /root/ORB_SLAM3/Examples_old/ROS/ORB_SLAM3/RGBD; grep -q "RGBD,false" /root/ORB_SLAM3/Examples_old/ROS/ORB_SLAM3/src/ros_rgbd.cc; grep -q "/orb_slam3/camera_pose" /root/ORB_SLAM3/Examples_old/ROS/ORB_SLAM3/src/ros_rgbd.cc' || fail "ORB native executable/pose patch invalid"
pass "ORB native executable is headless and publishes camera pose"

"$ROOT/tests/static_validation.sh"
pass "repository unit/static validation"

if [[ -n "$RUNTIME_DIR" ]]; then
  [[ "$(wc -l < "$RUNTIME_DIR/fast_livo2_trajectory.csv")" -gt 1 ]] || fail "FAST runtime trajectory has no poses"
  [[ "$(wc -l < "$RUNTIME_DIR/orbslam3_trajectory.csv")" -gt 1 ]] || fail "ORB runtime trajectory has no poses"
  [[ -s "$RUNTIME_DIR/localization_timeline.jsonl" ]] || fail "fusion timeline missing"
  python3 "$ROOT/tests/robustness_status.py" "$RUNTIME_DIR"
  pass "runtime evidence exists for both estimators"
fi
