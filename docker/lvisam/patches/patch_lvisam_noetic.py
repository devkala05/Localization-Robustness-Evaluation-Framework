#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("LVI_SAM_ROOT", "/root/catkin_ws/src/LVI-SAM"))

replacements = {
    "#include <opencv/cv.h>": "#include <opencv2/opencv.hpp>",
    "CV_GRAY2RGB": "cv::COLOR_GRAY2RGB",
    "CV_RGB2GRAY": "cv::COLOR_RGB2GRAY",
    "CV_FONT_HERSHEY_SIMPLEX": "cv::FONT_HERSHEY_SIMPLEX",
}

for path in root.rglob("*"):
    if path.suffix not in {".cpp", ".cc", ".h", ".hpp"}:
        continue
    text = path.read_text()
    original = text
    for old, new in replacements.items():
        text = text.replace(old, new)
    if text != original:
        path.write_text(text)

map_optimization = root / "src/lidar_odometry/mapOptmization.cpp"
text = map_optimization.read_text()
old = '        subGPS                = nh.subscribe<nav_msgs::Odometry>      (gpsTopic,                                   50, &mapOptimization::gpsHandler, this, ros::TransportHints().tcpNoDelay());'
new = '''        if (!gpsTopic.empty())
            subGPS            = nh.subscribe<nav_msgs::Odometry>      (gpsTopic,                                   50, &mapOptimization::gpsHandler, this, ros::TransportHints().tcpNoDelay());'''
if old in text:
    map_optimization.write_text(text.replace(old, new))

cmake = root / "CMakeLists.txt"
text = cmake.read_text()
text = text.replace('set(CMAKE_CXX_FLAGS "-std=c++11")', 'set(CMAKE_CXX_FLAGS "-std=c++14")')
text = text.replace("catkin_package(\n    DEPENDS PCL GTSAM\n)", "catkin_package(\n    DEPENDS PCL\n)")
cmake.write_text(text)
