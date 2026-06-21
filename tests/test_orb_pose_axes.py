#!/usr/bin/env python3
"""Regression test for the v1 E2O optical-camera/body axis conversion."""
import importlib.util
import sys
import types
from pathlib import Path

import numpy as np


class Pose:
    pass


def stub_module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


stub_module("rospy")
stub_module("transforms3d", quaternions=types.SimpleNamespace())
stub_module("geometry_msgs")
stub_module("geometry_msgs.msg", Pose=Pose, PoseStamped=type("PoseStamped", (), {}))
stub_module("nav_msgs")
stub_module("nav_msgs.msg", Odometry=type("Odometry", (), {}), Path=type("Path", (), {}))
stub_module("std_msgs")
stub_module("std_msgs.msg", String=type("String", (), {}))
stub_module("sensor_msgs", point_cloud2=types.SimpleNamespace())
stub_module("sensor_msgs.msg", PointCloud=type("PointCloud", (), {}), PointCloud2=type("PointCloud2", (), {}))

path = Path(__file__).resolve().parents[1] / "wrappers/orbslam3_e2o/scripts/pose_republisher_node.py"
spec = importlib.util.spec_from_file_location("orb_pose_republisher", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main() -> None:
    calibrated_camera_T_body = np.array([
        [-0.18256836, -0.98306216, -0.01604916, 0.07383026],
        [0.11110754, -0.00440978, -0.99379861, -0.5358112],
        [0.97689503, -0.18321936, 0.1100307, -0.31010858],
        [0.0, 0.0, 0.0, 1.0],
    ])
    assert np.allclose(module.E2O_CAMERA_T_BODY, calibrated_camera_T_body)
    optical_ground = np.array([3.0, 0.0, 7.0, 1.0])
    grid_ground = module.ORB_WORLD_T_GRID @ optical_ground
    assert np.isclose(grid_ground[2], 0.0), grid_ground
    start_camera = np.eye(4)
    moved_camera = np.eye(4)
    moved_camera[2, 3] = 5.0
    start_body = module.camera_pose_to_body(start_camera)
    moved_body = module.camera_pose_to_body(moved_camera)
    relative = module.invert_rigid(start_body) @ moved_body
    expected_translation = calibrated_camera_T_body[:3, :3].T @ np.array([0.0, 0.0, 5.0])
    assert np.allclose(relative[:3, 3], expected_translation), relative[:3, 3]
    assert np.allclose(relative[:3, :3], np.eye(3)), relative[:3, :3]
    assert np.allclose(start_body, module.E2O_CAMERA_T_BODY)

    # A loop-closure correction must re-anchor without freezing or jumping the
    # externally published trajectory.
    last_output = np.eye(4)
    last_output[0, 3] = 20.0
    corrected_raw = np.eye(4)
    corrected_raw[1, 3] = -8.0
    continuity = last_output @ module.invert_rigid(corrected_raw)
    assert np.allclose(continuity @ corrected_raw, last_output)
    next_raw = corrected_raw.copy()
    next_raw[0, 3] += 1.0
    assert np.allclose((continuity @ next_raw)[:3, 3], [21.0, 0.0, 0.0])
    print("ORB E2O optical/body axis test passed")


if __name__ == "__main__":
    main()
