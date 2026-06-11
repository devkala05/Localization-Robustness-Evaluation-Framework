#!/usr/bin/env python3
import argparse
import shlex
import sys

import yaml


ALIASES = {
    "orbslam3": "orb_slam3",
    "orb_slam3": "orb_slam3",
    "orb-slam3": "orb_slam3",
    "orb": "orb_slam3",
    "fastlio2": "fast_lio2",
    "fast_lio2": "fast_lio2",
    "fast-lio2": "fast_lio2",
    "fastlivo2": "fast_livo2",
    "fast_livo2": "fast_livo2",
    "fast-livo2": "fast_livo2",
    "rtabmap": "rtab_map",
    "rtab_map": "rtab_map",
    "rtab-map": "rtab_map",
    "adap_w": "adaptive_w_lvio",
    "adap-w": "adaptive_w_lvio",
    "adaptive_w": "adaptive_w_lvio",
    "adaptive-w": "adaptive_w_lvio",
    "adaptive_w_lvio": "adaptive_w_lvio",
    "adaptive-w-lvio": "adaptive_w_lvio",
    "adaptivewlvio": "adaptive_w_lvio",
}


def shell_var(name, value):
    if value is None:
        value = ""
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    print(f"{name}={shlex.quote(str(value))}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--algo", required=True)
    args = parser.parse_args()

    key = ALIASES.get(args.algo.strip().lower())
    if not key:
        print(f"ERROR: unknown --algo '{args.algo}'", file=sys.stderr)
        print("Available aliases: fastlio2, fastlivo2, rtabmap, adaptive_w_lvio, adap_w, orbslam3", file=sys.stderr)
        return 2

    with open(args.config, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    algorithms = data.get("algorithms") or {}
    cfg = algorithms.get(key)
    if not cfg:
        print(f"ERROR: algorithm '{key}' is not configured in {args.config}", file=sys.stderr)
        return 2

    if not cfg.get("enabled", False):
        print(f"ERROR: algorithm '{key}' is configured but enabled=false", file=sys.stderr)
        return 2

    shell_var("ALGO_ID", key)
    shell_var("ALGO_DISPLAY", cfg.get("display_name", key))
    shell_var("ALGO_RESULT_ID", cfg.get("result_id", key))
    shell_var("ALGO_BUILD_PACKAGES", cfg.get("build_packages", []))
    shell_var("ALGO_BUILD_JOBS", cfg.get("build_jobs", 2))
    shell_var("ALGO_TF_COMMAND", cfg.get("tf_command", ""))
    shell_var("ALGO_ADAPTER_LAUNCH", cfg.get("adapter_launch", ""))
    shell_var("ALGO_LAUNCH", cfg.get("launch", ""))
    shell_var("ALGO_OUTPUT_TOPIC", cfg.get("output_topic", ""))
    shell_var("ALGO_NATIVE_LIDAR_TOPIC", cfg.get("native_lidar_topic", ""))
    shell_var("ALGO_NATIVE_IMU_TOPIC", cfg.get("native_imu_topic", ""))
    shell_var("ALGO_NATIVE_CAMERA_TOPIC", cfg.get("native_camera_topic", ""))
    shell_var("ALGO_POINT_TIME_SCALE", cfg.get("point_time_scale", 1.0))
    shell_var("ALGO_RVIZ_CONFIG", cfg.get("rviz_config", ""))
    shell_var("ALGO_BAG_TOPICS", cfg.get("bag_topics", "/velodyne_points /imu/data /zed2/camera/right/image_raw"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
