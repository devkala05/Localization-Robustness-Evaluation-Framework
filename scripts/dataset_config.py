#!/usr/bin/env python3
import argparse
import shlex
import sys
import yaml


def shell_var(name, value):
    if value is None:
        value = ""
    if isinstance(value, bool):
        value = "true" if value else "false"
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    print(f"{name}={shlex.quote(str(value))}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    with open(args.config, "r", encoding="utf-8") as handle:
        datasets = (yaml.safe_load(handle) or {}).get("datasets", {})
    if args.list:
        for key, cfg in datasets.items():
            print(f"{key}\t{cfg.get('display_name', key)}")
        return 0
    key = args.dataset.strip().lower()
    cfg = datasets.get(key)
    if cfg is None:
        print(f"ERROR: unknown dataset '{args.dataset}'. Available: {', '.join(datasets)}", file=sys.stderr)
        return 2
    fields = {
        "DATASET_ID": key,
        "DATASET_DISPLAY": cfg.get("display_name", key),
        "DATASET_LABEL": cfg.get("dataset_label", key),
        "DATASET_DEFAULT_BAG": cfg.get("default_bag", ""),
        "DATASET_DEFAULT_GT": cfg.get("default_gt", ""),
        "DATASET_GT_FORMAT": cfg.get("gt_format", "auto"),
        "DATASET_WORLD_FRAME": cfg.get("world_frame", "camera_init"),
        "DATASET_BODY_FRAME": cfg.get("body_frame", "body"),
        "DATASET_LIDAR_FRAME": cfg.get("lidar_frame", "velodyne"),
        "DATASET_IMU_FRAME": cfg.get("imu_frame", "body"),
        "DATASET_CAMERA_FRAME": cfg.get("camera_frame", "camera_right"),
        "DATASET_SOURCE_LIDAR_TOPIC": cfg.get("source_lidar_topic", ""),
        "DATASET_SOURCE_IMU_TOPIC": cfg.get("source_imu_topic", ""),
        "DATASET_SOURCE_CAMERA_TOPIC": cfg.get("source_camera_topic", ""),
        "DATASET_SOURCE_LEFT_CAMERA_TOPIC": cfg.get("source_left_camera_topic", ""),
        "DATASET_GPS_TOPIC": cfg.get("gps_topic", ""),
        "DATASET_CAMERA_WIDTH": cfg.get("camera_width", ""),
        "DATASET_CAMERA_HEIGHT": cfg.get("camera_height", ""),
        "DATASET_CAMERA_INFO_YAML": cfg.get("camera_info_yaml", ""),
        "DATASET_STATIC_TF_YAML": cfg.get("static_tf_yaml", ""),
        "DATASET_BAG_TOPICS": cfg.get("bag_topics", ""),
        "DATASET_ORB_DEFAULT_MODE": cfg.get("orb_default_mode", "mono"),
        "DATASET_STEREO_SWAP_DEFAULT": cfg.get("stereo_swap_default", False),
        "DATASET_POINT_TIME_FIELD": cfg.get("point_time_field", "time"),
        "DATASET_POINT_TIME_UNIT": cfg.get("point_time_unit", "auto"),
        "DATASET_USE_CLOCK_STAMP": cfg.get("use_clock_stamp", False),
        "DATASET_SCAN_LINES_ASSUMED": cfg.get("scan_lines_assumed", 64),
        "DATASET_PERTURBATIONS_DIR": cfg.get("perturbations_dir", "/root/catkin_ws/src/localization_benchmark/config/perturbations"),
        "DATASET_SEGMENTS_YAML": cfg.get("segments_yaml", "/root/catkin_ws/src/localization_benchmark/config/road_segments.yaml"),
    }
    for name, value in fields.items():
        shell_var(name, value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
