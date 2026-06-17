#!/usr/bin/env python3
import argparse
import os
import shlex
import sys

import yaml


ALIASES = {
    "urbannav": "urbannav",
    "urban": "urbannav",
    "urbannav_hk_tst": "urbannav",
    "urbannav_hk_tst_20210517": "urbannav",
    "e2o": "e2o",
    "e20": "e2o",
    "e2o/urban": "e2o",
    "e20/urban": "e2o",
    "one_full_loop": "e2o",
    "e2o_one_full_loop": "e2o",
}


def shell_var(name, value):
    if value is None:
        value = ""
    if isinstance(value, bool):
        value = "true" if value else "false"
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    print("{}={}".format(name, shlex.quote(str(value))))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="urbannav")
    parser.add_argument("--config-dir", default="wrappers/localization_benchmark/config/datasets")
    parser.add_argument("--algo", default="")
    args = parser.parse_args()

    key = ALIASES.get(args.dataset.strip().lower())
    if not key:
        print("ERROR: unknown dataset '{}'. Available: urbannav, e2o".format(args.dataset), file=sys.stderr)
        return 2

    cfg_path = os.path.join(args.config_dir, "{}.yaml".format(key))
    if not os.path.isfile(cfg_path):
        print("ERROR: dataset config not found: {}".format(cfg_path), file=sys.stderr)
        return 2
    with open(cfg_path, "r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle) or {}

    dataset = cfg.get("dataset") or {}
    lidar = cfg.get("lidar") or {}
    source = cfg.get("source_topics") or {}
    calibration = cfg.get("calibration") or {}
    camera_right = calibration.get("camera_right") or {}
    camera_left = calibration.get("camera_left") or {}
    bag_topics = cfg.get("bag_topics") or {}
    paths = cfg.get("paths") or {}
    frames = cfg.get("frames") or {}
    algo_topics = bag_topics.get(args.algo) if args.algo else None
    selected_bag_topics = algo_topics or bag_topics.get("default") or ""

    shell_var("DATASET_ID", dataset.get("id", key))
    shell_var("DATASET_NAME", dataset.get("name", key))
    shell_var("DATASET_CONFIG", cfg_path)
    shell_var("DATASET_BAG_PATH", dataset.get("bag_path", ""))
    shell_var("DATASET_GT_PATH", dataset.get("ground_truth_path", ""))
    shell_var("DATASET_GT_YAW_OFFSET_DEG", dataset.get("gt_yaw_offset_deg", 0.0))
    shell_var("DATASET_RESULTS_ROOT", dataset.get("results_root", "/data/results/{}".format(key)))
    shell_var("DATASET_FRAME_ID", dataset.get("frame_id", "camera_init"))
    shell_var("DATASET_GT_FORMAT", dataset.get("gt_format", "auto"))
    shell_var("DATASET_USE_CLOCK_STAMP", dataset.get("use_clock_stamp", False))
    shell_var("DATASET_WORLD_FRAME", frames.get("world", dataset.get("frame_id", "camera_init")))
    shell_var("DATASET_BODY_FRAME", frames.get("body", "body"))
    shell_var("DATASET_LIDAR_FRAME", frames.get("lidar", "velodyne"))
    shell_var("DATASET_IMU_FRAME", frames.get("imu", "body"))
    shell_var("DATASET_CAMERA_FRAME", frames.get("camera_right", "camera_right_optical"))
    shell_var("DATASET_GPS_SOURCE", dataset.get("gps_source", "auto"))
    shell_var("DATASET_GPS_FILE", dataset.get("gps_file", ""))
    shell_var("DATASET_GPS_TOPIC", dataset.get("gps_topic", "/gps/fix_raw"))
    shell_var("DATASET_ORB_MODE", dataset.get("default_orb_mode", "stereo"))
    shell_var("DATASET_STEREO_SWAP", dataset.get("stereo_swap", True))
    shell_var("DATASET_LIDAR_MODEL", lidar.get("model", "velodyne_32"))
    shell_var("DATASET_SCAN_LINE", lidar.get("scan_line", 32))
    shell_var("DATASET_SOURCE_LIDAR_TOPIC", source.get("lidar", ""))
    shell_var("DATASET_SOURCE_IMU_TOPIC", source.get("imu", ""))
    shell_var("DATASET_SOURCE_CAMERA_TOPIC", source.get("camera_right", ""))
    shell_var("DATASET_SOURCE_LEFT_CAMERA_TOPIC", source.get("camera_left", ""))
    shell_var("DATASET_SOURCE_GPS_TOPIC", source.get("gps", ""))
    shell_var("DATASET_BAG_TOPICS", selected_bag_topics)
    shell_var("DATASET_PERTURBATIONS_DIR", paths.get("perturbations_dir", "/root/catkin_ws/src/localization_benchmark/config/perturbations"))
    shell_var("DATASET_SEGMENTS_YAML", paths.get("segments_yaml", "/root/catkin_ws/src/localization_benchmark/config/road_segments.yaml"))
    shell_var("DATASET_POINT_TIME_FIELD", lidar.get("point_time_field", "time"))
    shell_var("DATASET_POINT_TIME_UNIT", lidar.get("point_time_unit", "s"))
    shell_var("DATASET_CAMERA_RIGHT_K", camera_right.get("K", ""))
    shell_var("DATASET_CAMERA_RIGHT_D", camera_right.get("D", ""))
    shell_var("DATASET_CAMERA_RIGHT_WIDTH", camera_right.get("width", ""))
    shell_var("DATASET_CAMERA_RIGHT_HEIGHT", camera_right.get("height", ""))
    shell_var("DATASET_CAMERA_LEFT_K", camera_left.get("K", ""))
    shell_var("DATASET_CAMERA_LEFT_D", camera_left.get("D", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
