#!/usr/bin/env python3
"""Pure-Python regression checks for estimator timestamp health state."""
import importlib.util
import math
import sys
import types
from pathlib import Path

import numpy as np


class Stamp:
    def __init__(self, value): self.value = value
    def to_sec(self): return self.value


class Obj:
    pass


def odom(stamp, x):
    msg = Obj()
    msg.header = Obj(); msg.header.stamp = Stamp(stamp)
    msg.pose = Obj(); msg.pose.pose = Obj()
    msg.pose.pose.position = Obj()
    msg.pose.pose.position.x = x
    msg.pose.pose.position.y = 0.0
    msg.pose.pose.position.z = 0.0
    msg.pose.pose.orientation = Obj()
    msg.pose.pose.orientation.x = 0.0
    msg.pose.pose.orientation.y = 0.0
    msg.pose.pose.orientation.z = 0.0
    msg.pose.pose.orientation.w = 1.0
    return msg


def pose_to_matrix(pose):
    values = [pose.position.x, pose.position.y, pose.position.z,
              pose.orientation.x, pose.orientation.y,
              pose.orientation.z, pose.orientation.w]
    if not np.all(np.isfinite(values)):
        raise ValueError("non-finite")
    T = np.eye(4)
    T[:3, 3] = values[:3]
    return T


def rotation_angle(R):
    return math.acos(max(-1.0, min(1.0, (float(np.trace(R)) - 1.0) * 0.5)))


def install_stubs():
    sys.modules["rospy"] = types.ModuleType("rospy")
    rosnode = types.ModuleType("rosnode"); rosnode.get_node_names = lambda: []
    sys.modules["rosnode"] = rosnode
    fm = types.ModuleType("fusion_math")
    fm.pose_to_matrix = pose_to_matrix; fm.rotation_angle = rotation_angle
    sys.modules["fusion_math"] = fm
    for package, names in {
        "diagnostic_msgs.msg": ["DiagnosticArray", "DiagnosticStatus", "KeyValue"],
        "nav_msgs.msg": ["Odometry"],
        "sensor_msgs.msg": ["Image", "Imu", "PointCloud2"],
        "std_msgs.msg": ["String"],
    }.items():
        parent_name = package.split(".")[0]
        parent = types.ModuleType(parent_name)
        module = types.ModuleType(package)
        for name in names:
            setattr(module, name, type(name, (), {}))
        parent.msg = module
        sys.modules[parent_name] = parent
        sys.modules[package] = module


def main():
    install_stubs()
    path = Path(__file__).resolve().parents[1] / "wrappers/e2o_localization_fusion/scripts/localization_health_monitor.py"
    spec = importlib.util.spec_from_file_location("health_monitor", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    state = module.EstimatorState(
        name="test", timeout=1.0, min_rate_hz=1.0, max_rate_window=3.0,
        max_position_jump=3.0, max_orientation_jump_rad=1.0,
        max_velocity=35.0, max_angular_velocity=5.0, max_acceleration=20.0,
        max_timestamp_lag=2.0, process_patterns=[], required_sensors=[]
    )
    state.update_odom(odom(10.0, 0.0))
    assert state.last_stamp == 10.0 and state.last_valid
    state.update_odom(odom(10.0, 0.0))
    assert state.last_stamp == 10.0
    assert "duplicate_timestamp" in state.last_message_reasons
    state.update_odom(odom(9.0, 0.0))
    assert state.last_stamp == 10.0
    assert "timestamp_regression" in state.last_message_reasons
    state.update_odom(odom(11.0, 0.1))
    assert state.last_stamp == 11.0 and state.last_valid
    state.update_odom(odom(12.0, float("nan")))
    assert state.last_stamp == 11.0
    assert "non_finite_or_invalid_pose" in state.last_message_reasons
    print("health-state timestamp test passed")


if __name__ == "__main__":
    main()
