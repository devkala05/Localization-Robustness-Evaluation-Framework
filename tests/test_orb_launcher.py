#!/usr/bin/env python3
"""Regression test that roslaunch remaps survive the Python exec wrapper."""
import importlib.util
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "wrappers/orbslam3_e2o/scripts/run_orbslam3_native.py"
spec = importlib.util.spec_from_file_location("run_orbslam3_native", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        binary = root / "Examples_old/ROS/ORB_SLAM3/RGBD"
        binary.parent.mkdir(parents=True)
        binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        binary.chmod(0o755)
        argv = [
            "run_orbslam3_native.py",
            "/root/ORB_SLAM3/Vocabulary/ORBvoc.txt",
            "/workspace/e2o.yaml",
            "__name:=orbslam3_rgbd",
            "/camera/rgb/image_raw:=/camera/rgb/image_raw",
            "/camera/depth_registered/image_raw:=/camera/depth_registered/image_raw",
            "/tf:=/native/orbslam3/tf",
            "__log:=/tmp/orb.log",
        ]
        found, command = module.build_exec_argv(argv, root)
        assert found == binary
        assert command[:3] == [str(binary), argv[1], argv[2]]
        assert command[3:] == argv[3:]
        positional, remaps = module.split_arguments(argv)
        assert positional == argv[:3]
        assert remaps == argv[3:]

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        binary = root / "Examples_old/ROS/ORB_SLAM3/RGBD_Inertial"
        binary.parent.mkdir(parents=True)
        binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        binary.chmod(0o755)
        argv = [
            "run_orbslam3_native.py",
            "/root/ORB_SLAM3/Vocabulary/ORBvoc.txt",
            "/workspace/e2o.yaml",
            "__name:=orbslam3_rgbd",
        ]
        with patch.dict(os.environ, {"ORB_SLAM3_EXECUTABLE": "RGBD_Inertial"}):
            found, command = module.build_exec_argv(argv, root)
        assert found == binary
        assert command[:3] == [str(binary), argv[1], argv[2]]
        assert command[3:] == argv[3:]
    print("ORB native launcher remap test passed")


if __name__ == "__main__":
    main()
