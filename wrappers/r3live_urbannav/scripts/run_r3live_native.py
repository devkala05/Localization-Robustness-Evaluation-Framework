#!/usr/bin/env python3
"""Launch the correct upstream R3LIVE executable.

Upstream hku-mars/r3live builds one full LVIO executable named
`r3live_mapping` and one optional LiDAR-only frontend named
`r3live_LiDAR_front_end`.  It does NOT build a separate VIO executable.

The previous wrapper tried to launch LIO and VIO as two separate required
nodes.  On the official upstream tree that makes the VIO runner fail and the
whole launch exits, leaving only the bag/camera/adapter running and no odometry.
This wrapper defaults to the full `mapping` role and keeps `lio` as an optional
fallback/debug role.
"""
import os
import stat
import subprocess
import sys
from pathlib import Path

import rospy

CANDIDATES = {
    # For UrbanNav/PointCloud2, use full mapping first. The LiDAR front-end
    # may subscribe to livox_ros_driver/CustomMsg and then never produce odom.
    "stable": [
        "r3live_mapping",
        "r3live_LiDAR_mapping",
        "r3live_lidar_mapping",
        "r3live_LiDAR_front_end",
        "r3live_lidar_front_end",
    ],
    "mapping": ["r3live_mapping"],
    "lio": [
        "r3live_LiDAR_front_end",
        "r3live_lidar_front_end",
        "r3live_LiDAR_mapping",
        "r3live_lidar_mapping",
    ],
}


def executable(path: Path) -> bool:
    try:
        st = path.stat()
    except OSError:
        return False
    return path.is_file() and bool(st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))


def rospack_find(pkg: str) -> Path:
    out = subprocess.check_output(["rospack", "find", pkg], text=True).strip()
    return Path(out)


def search_paths(pkg_path: Path):
    catkin_ws = Path(os.environ.get("CATKIN_WS", "/root/catkin_ws"))
    paths = [
        catkin_ws / "devel" / "lib" / "r3live",
        Path("/root/catkin_ws/devel/lib/r3live"),
        pkg_path / "../../devel/lib/r3live",
        pkg_path / "build",
        pkg_path,
    ]
    seen = set()
    for p in paths:
        p = p.resolve()
        if p not in seen:
            seen.add(p)
            yield p


def main():
    rospy.init_node("run_r3live_native", anonymous=True, disable_signals=True)
    role = rospy.get_param("~role", "stable").strip().lower()
    if role not in CANDIDATES:
        rospy.logerr("[R3LIVE NativeRunner] unknown role=%s; valid=%s", role, sorted(CANDIDATES))
        return 2

    config_path = rospy.get_param("~config_path", "")
    run_visual = rospy.get_param("~run_visual", False)
    rospy.loginfo("[R3LIVE NativeRunner] config_path=%s run_visual=%s", config_path, run_visual)
    pkg_path = rospack_find("r3live")
    candidates = CANDIDATES[role]
    for base in search_paths(pkg_path):
        for name in candidates:
            path = base / name
            if executable(path):
                rospy.loginfo("[R3LIVE NativeRunner] role=%s exec=%s", role, path)
                os.execv(str(path), [str(path)] + sys.argv[1:])

    rospy.logerr("[R3LIVE NativeRunner] no executable found for role=%s", role)
    rospy.logerr("[R3LIVE NativeRunner] tried names: %s", ", ".join(candidates))
    rospy.logerr("[R3LIVE NativeRunner] searched under package path: %s", pkg_path)
    return 1


if __name__ == "__main__":
    sys.exit(main())
