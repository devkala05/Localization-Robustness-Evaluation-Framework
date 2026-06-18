#!/usr/bin/env python3
import argparse
import shlex
import sys
import yaml

ALIASES = {
    "fastlio2": "fast_lio2",
    "lvisam": "lvi_sam",
    "fastlivo2": "fast_livo2",
    "rtabmap": "rtab_map",
    "adaptive_w_lvio": "adaptive_w_lvio",
    "orbslam3": "orb_slam3",
    "r3live": "r3live",
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
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    with open(args.config, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    algorithms = data.get("algorithms") or {}
    if args.list:
        for key, cfg in algorithms.items():
            if cfg.get("enabled", False):
                print(f"{key}\t{cfg.get('display_name', key)}")
        return 0
    key = ALIASES.get(args.algo.strip().lower())
    if not key:
        print(f"ERROR: unknown --algo '{args.algo}'", file=sys.stderr)
        print("Available: fastlio2, lvisam, fastlivo2, rtabmap, adaptive_w_lvio, orbslam3, r3live", file=sys.stderr)
        return 2
    cfg = algorithms.get(key)
    if not cfg:
        print(f"ERROR: algorithm '{key}' is not configured in {args.config}", file=sys.stderr)
        return 2
    if not cfg.get("enabled", False):
        print(f"ERROR: algorithm '{key}' is configured but enabled=false", file=sys.stderr)
        return 2
    ns = cfg.get("standard_topic_ns") or cfg.get("result_id", key)
    selected_output = cfg.get("selected_output_topic", f"/{ns}/odometry/output")
    selected_path = cfg.get("selected_path_topic", f"/{ns}/path/output")
    local_odom = cfg.get("local_odom_topic", f"/{ns}/odometry/local")
    local_path = cfg.get("local_path_topic", f"/{ns}/path/local")
    shell_var("ALGO_ID", args.algo.strip().lower())
    shell_var("ALGO_DISPLAY", cfg.get("display_name", key))
    shell_var("ALGO_RESULT_ID", cfg.get("result_id", key))
    shell_var("ALGO_STANDARD_NS", ns)
    shell_var("ALGO_BUILD_PACKAGES", cfg.get("build_packages", []))
    shell_var("ALGO_BUILD_JOBS", cfg.get("build_jobs", 2))
    shell_var("ALGO_TF_COMMAND", cfg.get("tf_command", ""))
    shell_var("ALGO_ADAPTER_LAUNCH", cfg.get("adapter_launch", ""))
    shell_var("ALGO_ADAPTER_ARGS", cfg.get("adapter_args", ""))
    shell_var("ALGO_LAUNCH", cfg.get("launch", ""))
    shell_var("ALGO_LAUNCH_ARGS", cfg.get("launch_args", ""))
    shell_var("ALGO_OUTPUT_TOPIC", cfg.get("output_topic", ""))
    shell_var("ALGO_PATH_TOPIC", cfg.get("path_topic", ""))
    shell_var("ALGO_LOCAL_ODOM_TOPIC", local_odom)
    shell_var("ALGO_LOCAL_PATH_TOPIC", local_path)
    shell_var("ALGO_SELECTED_OUTPUT_TOPIC", selected_output)
    shell_var("ALGO_SELECTED_PATH_TOPIC", selected_path)
    shell_var("ALGO_STATUS_TOPIC", cfg.get("status_topic", f"/{ns}/status"))
    shell_var("ALGO_NATIVE_LIDAR_TOPIC", cfg.get("native_lidar_topic", ""))
    shell_var("ALGO_NATIVE_IMU_TOPIC", cfg.get("native_imu_topic", ""))
    shell_var("ALGO_NATIVE_CAMERA_TOPIC", cfg.get("native_camera_topic", ""))
    shell_var("ALGO_POINT_TIME_SCALE", cfg.get("point_time_scale", 1.0))
    shell_var("ALGO_RVIZ_CONFIG", cfg.get("rviz_config", ""))
    shell_var("ALGO_NOTES", cfg.get("notes", ""))
    shell_var("ALGO_GPS_STRATEGY", cfg.get("gps_strategy", "external_fusion"))
    shell_var("ALGO_GPS_SUPPORTED", cfg.get("gps_supported", True))
    shell_var("ALGO_BAG_TOPICS", cfg.get("bag_topics", "/velodyne_points /imu/data /zed2/camera/right/image_raw"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
