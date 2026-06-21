#!/usr/bin/env python3
"""Fix measurement timestamps and configurable PCD output in pinned FAST-LIVO2."""
import os
from pathlib import Path


root = Path(os.environ.get("FAST_LIVO2_ROOT", "/root/catkin_ws/src/FAST-LIVO2"))
path = root / "src/LIVMapper.cpp"
text = path.read_text()

old_stamp = "odomAftMapped.header.stamp = ros::Time::now(); //.ros::Time()fromSec(last_timestamp_lidar);"
new_stamp = (
    "odomAftMapped.header.stamp = "
    "ros::Time().fromSec(LidarMeasures.measures.back().lio_time);"
)
if old_stamp in text:
    text = text.replace(old_stamp, new_stamp, 1)
elif new_stamp not in text:
    raise RuntimeError("FAST-LIVO2 odometry timestamp pattern not found")

old_paths = '''    std::string raw_points_dir = std::string(ROOT_DIR) + "Log/pcd/all_raw_points.pcd";
    std::string downsampled_points_dir = std::string(ROOT_DIR) + "Log/pcd/all_downsampled_points.pcd";'''
new_paths = '''    std::string configured_pcd_path;
    ros::param::param<std::string>("pcd_save/pcd_path", configured_pcd_path, "");
    std::string raw_points_dir = configured_pcd_path.empty()
        ? std::string(ROOT_DIR) + "Log/pcd/all_raw_points.pcd"
        : configured_pcd_path + ".raw.pcd";
    std::string downsampled_points_dir = configured_pcd_path.empty()
        ? std::string(ROOT_DIR) + "Log/pcd/all_downsampled_points.pcd"
        : configured_pcd_path;'''
if old_paths in text:
    text = text.replace(old_paths, new_paths, 1)
elif new_paths not in text:
    raise RuntimeError("FAST-LIVO2 PCD output path pattern not found")

path.write_text(text)
