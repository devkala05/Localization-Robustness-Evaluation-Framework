#!/usr/bin/env python3
import argparse
import copy
import os
import re
import shlex
import sys
import yaml

ALIASES = {
    "fastlio2": "fast_lio2", "lvisam": "lvi_sam", "fastlivo2": "fast_livo2",
    "rtabmap": "rtab_map", "adaptive_w_lvio": "adaptive_w_lvio",
    "orbslam3": "orb_slam3", "r3live": "r3live",
}


def shell_var(name, value):
    if value is None:
        value = ""
    if isinstance(value, bool):
        value = "true" if value else "false"
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    print(f"{name}={shlex.quote(str(value))}")


def expand(value):
    if not isinstance(value, str):
        return value
    # Support the ${NAME:-fallback} form used by the original registry.
    value = re.sub(
        r"\$\{([A-Za-z_][A-Za-z0-9_]*):-([^}]*)\}",
        lambda m: os.environ.get(m.group(1), m.group(2)), value,
    )
    return os.path.expandvars(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--algo", required=True)
    parser.add_argument("--dataset", default="urbannav")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    with open(args.config, "r", encoding="utf-8") as handle:
        algorithms = (yaml.safe_load(handle) or {}).get("algorithms", {})
    if args.list:
        for key, cfg in algorithms.items():
            if cfg.get("enabled", False):
                print(f"{key}\t{cfg.get('display_name', key)}")
        return 0
    key = ALIASES.get(args.algo.strip().lower())
    if not key:
        print(f"ERROR: unknown --algo '{args.algo}'", file=sys.stderr)
        return 2
    base = algorithms.get(key)
    if not base or not base.get("enabled", False):
        print(f"ERROR: algorithm '{key}' is missing or disabled", file=sys.stderr)
        return 2
    cfg = copy.deepcopy(base)
    override = (cfg.pop("dataset_overrides", {}) or {}).get(args.dataset, {}) or {}
    cfg.update(override)
    cfg = {k: expand(v) for k, v in cfg.items()}

    ns = cfg.get("standard_topic_ns") or cfg.get("result_id", key)
    selected_output = cfg.get("selected_output_topic", f"/{ns}/odometry/output")
    selected_path = cfg.get("selected_path_topic", f"/{ns}/path/output")
    local_odom = cfg.get("local_odom_topic", f"/{ns}/odometry/local")
    local_path = cfg.get("local_path_topic", f"/{ns}/path/local")
    values = {
        "ALGO_ID": args.algo.strip().lower(), "ALGO_DISPLAY": cfg.get("display_name", key),
        "ALGO_RESULT_ID": cfg.get("result_id", key), "ALGO_STANDARD_NS": ns,
        "ALGO_BUILD_PACKAGES": cfg.get("build_packages", []), "ALGO_BUILD_JOBS": cfg.get("build_jobs", 2),
        "ALGO_TF_COMMAND": cfg.get("tf_command", ""), "ALGO_ADAPTER_LAUNCH": cfg.get("adapter_launch", ""),
        "ALGO_ADAPTER_ARGS": cfg.get("adapter_args", ""), "ALGO_LAUNCH": cfg.get("launch", ""),
        "ALGO_LAUNCH_ARGS": cfg.get("launch_args", ""), "ALGO_OUTPUT_TOPIC": cfg.get("output_topic", ""),
        "ALGO_PATH_TOPIC": cfg.get("path_topic", ""), "ALGO_LOCAL_ODOM_TOPIC": local_odom,
        "ALGO_LOCAL_PATH_TOPIC": local_path, "ALGO_SELECTED_OUTPUT_TOPIC": selected_output,
        "ALGO_SELECTED_PATH_TOPIC": selected_path, "ALGO_STATUS_TOPIC": cfg.get("status_topic", f"/{ns}/status"),
        "ALGO_NATIVE_LIDAR_TOPIC": cfg.get("native_lidar_topic", ""),
        "ALGO_NATIVE_IMU_TOPIC": cfg.get("native_imu_topic", ""),
        "ALGO_NATIVE_CAMERA_TOPIC": cfg.get("native_camera_topic", ""),
        "ALGO_POINT_TIME_SCALE": cfg.get("point_time_scale", 1.0),
        "ALGO_RVIZ_CONFIG": cfg.get("rviz_config", ""), "ALGO_NOTES": cfg.get("notes", ""),
        "ALGO_GPS_STRATEGY": cfg.get("gps_strategy", "external_fusion"),
        "ALGO_GPS_SUPPORTED": cfg.get("gps_supported", True),
        "ALGO_BAG_TOPICS": cfg.get("bag_topics", ""),
        "ALGO_EVAL_ALIGNMENT": cfg.get("evaluation_alignment", "none"),
    }
    for name, value in values.items():
        shell_var(name, value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
