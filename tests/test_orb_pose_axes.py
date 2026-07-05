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
    body_pose = module.optical_pose_to_body_axes(pose, 0.0)
    assert module.np.allclose(
        [body_pose.position.x, body_pose.position.y, body_pose.position.z],
        [2.52590165, -1.52390068, 2.30164016],
    )
    assert module.np.allclose(
        [body_pose.orientation.x, body_pose.orientation.y, body_pose.orientation.z, body_pose.orientation.w],
        [0.0, 0.0, 0.0, 1.0],
    )
    base = module.GENERIC_OPTICAL_TO_BODY @ module.np.array([0.0, 0.0, 5.0, 1.0])
    assert module.np.allclose(base[:3], [5.0, 0.0, 0.0])
    pose_forward = Pose()
    pose_forward.position.x = 0.0
    pose_forward.position.y = 0.0
    pose_forward.position.z = 5.0
    pose_forward.orientation.x = 0.0
    pose_forward.orientation.y = 0.0
    pose_forward.orientation.z = 0.0
    pose_forward.orientation.w = 1.0
    calibrated_forward = module.optical_pose_to_body_axes(pose_forward, 0.0)
    assert module.np.allclose(
        [calibrated_forward.position.x, calibrated_forward.position.y, calibrated_forward.position.z],
        [4.88447515, -0.9160968, 0.5501535],
    )
    rotated = module.yaw_rotation(0.0) @ module.GENERIC_OPTICAL_TO_BODY @ module.np.array([0.0, 0.0, 5.0, 1.0])
    assert module.np.allclose(rotated[:3], [5.0, 0.0, 0.0])
    right = module.yaw_rotation(0.0) @ module.GENERIC_OPTICAL_TO_BODY @ module.np.array([2.0, 0.0, 0.0, 1.0])
    assert module.np.allclose(right[:3], [0.0, -2.0, 0.0])
    down = module.yaw_rotation(0.0) @ module.GENERIC_OPTICAL_TO_BODY @ module.np.array([0.0, 3.0, 0.0, 1.0])
    assert module.np.allclose(down[:3], [0.0, 0.0, -3.0])
    last = module.np.eye(4)
    last[:3, 3] = [4.0, -1.0, 0.2]
    jumped = module.np.eye(4)
    jumped[:3, 3] = [-12.0, 5.0, 0.2]
    correction = module.continuity_correction(last, jumped)
    assert module.np.allclose(correction @ jumped, last)

    pose.orientation.w = 0.0
    assert not module.quaternion_valid(pose)
    print("ORB optical-to-body axis test passed")


if __name__ == "__main__":
    main()
