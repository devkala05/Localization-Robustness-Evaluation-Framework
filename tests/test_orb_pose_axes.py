#!/usr/bin/env python3
"""Regression test for ORB optical-to-body axis conversion without scaling."""
import importlib.util
import math
import sys
import types
from pathlib import Path


def stub_module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


class Value:
    pass


class Pose:
    def __init__(self):
        self.position = Value()
        self.orientation = Value()


def quat2mat(q):
    w, x, y, z = q
    return module.np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def mat2quat(m):
    trace = float(m[0, 0] + m[1, 1] + m[2, 2])
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        return [0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s]
    raise AssertionError("test stub only handles positive trace rotations")


stub_module("rospy")
stub_module("transforms3d", quaternions=types.SimpleNamespace(quat2mat=quat2mat, mat2quat=mat2quat))
stub_module("geometry_msgs")
stub_module("geometry_msgs.msg", Pose=Pose, PoseStamped=type("PoseStamped", (), {}))
stub_module("nav_msgs")
stub_module("nav_msgs.msg", Odometry=type("Odometry", (), {}), Path=type("Path", (), {}))
stub_module("std_msgs")
stub_module("std_msgs.msg", String=type("String", (), {}))
stub_module("sensor_msgs", point_cloud2=types.SimpleNamespace())
stub_module("sensor_msgs.msg", PointCloud=type("PointCloud", (), {}), PointCloud2=type("PointCloud2", (), {}))

path = Path(__file__).resolve().parents[1] / "wrappers/orbslam3_e2o/scripts/pose_republisher_node.py"
source = path.read_text(encoding="utf-8")
spec = importlib.util.spec_from_file_location("orb_pose_republisher", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main() -> None:
    forbidden = (
        "E2O_CAMERA_T_BODY",
        "camera_pose_to_body",
        "fixed_pose_scale",
        "normalize_to_start",
        "reanchor_on_discontinuity",
    )
    for item in forbidden:
        assert item not in source

    pose = Pose()
    pose.position.x = 1.0
    pose.position.y = -2.0
    pose.position.z = 3.0
    pose.orientation.x = 0.0
    pose.orientation.y = 0.0
    pose.orientation.z = 0.0
    pose.orientation.w = 1.0
    assert module.pose_values_finite(pose)
    assert module.quaternion_valid(pose)
    base = module.OPTICAL_TO_BODY @ module.np.array([0.0, 0.0, 5.0, 1.0])
    assert module.np.allclose(base[:3], [5.0, 0.0, 0.0])
    rotated = module.yaw_rotation(180.0) @ module.OPTICAL_TO_BODY @ module.np.array([0.0, 0.0, 5.0, 1.0])
    assert module.np.allclose(rotated[:3], [-5.0, 0.0, 0.0])
    transform = module.OPTICAL_TO_BODY.copy()
    transform[:3, 3] = [6.0, 2.0, 0.0]
    pivot = module.np.array([5.0, 2.0, 0.0])
    about_start = module.apply_yaw_about_pivot(transform, 180.0, pivot)
    assert module.np.allclose(about_start[:3, 3], [4.0, 2.0, 0.0])
    right = module.yaw_rotation(180.0) @ module.OPTICAL_TO_BODY @ module.np.array([2.0, 0.0, 0.0, 1.0])
    assert module.np.allclose(right[:3], [0.0, 2.0, 0.0])
    down = module.yaw_rotation(180.0) @ module.OPTICAL_TO_BODY @ module.np.array([0.0, 3.0, 0.0, 1.0])
    assert module.np.allclose(down[:3], [0.0, 0.0, -3.0])

    pose.orientation.w = 0.0
    assert not module.quaternion_valid(pose)
    print("ORB optical-to-body axis test passed")


if __name__ == "__main__":
    main()
