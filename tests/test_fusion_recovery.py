#!/usr/bin/env python3
"""Pure-Python regression checks for the fusion1/fusion2 switching logic."""
import importlib.util
import sys
import types
from pathlib import Path


class Obj:
    pass


class Publisher:
    def __init__(self, *args, **kwargs):
        self.published = []

    def publish(self, msg):
        self.published.append(msg)


class Bool:
    def __init__(self, data=False):
        self.data = data


class String:
    def __init__(self, data=""):
        self.data = data


class Pose:
    def __init__(self):
        self.position = Obj()
        self.position.x = self.position.y = self.position.z = 0.0
        self.orientation = Quaternion()


class Quaternion:
    def __init__(self):
        self.x = self.y = self.z = 0.0
        self.w = 1.0


def install_stubs():
    rospy = types.ModuleType("rospy")
    rospy.Publisher = Publisher
    rospy.ROSInitException = RuntimeError
    def _now_stamp():
        stamp = Obj()
        stamp.to_sec = lambda: 100.0
        return stamp

    rospy.Time = type("Time", (), {"now": staticmethod(_now_stamp)})
    rospy.Duration = lambda *args, **kwargs: None
    rospy.logwarn = lambda *args, **kwargs: None
    rospy.logwarn_throttle = lambda *args, **kwargs: None
    rospy.loginfo = lambda *args, **kwargs: None
    sys.modules["rospy"] = rospy

    tf2_ros = types.ModuleType("tf2_ros")
    tf2_ros.TransformBroadcaster = object
    tf2_ros.StaticTransformBroadcaster = object
    tf2_ros.Buffer = object
    tf2_ros.TransformListener = object
    sys.modules["tf2_ros"] = tf2_ros

    for package, names in {
        "geometry_msgs.msg": ["PoseStamped", "TransformStamped", "Twist"],
        "nav_msgs.msg": ["Odometry", "Path"],
        "std_msgs.msg": ["Bool", "String"],
    }.items():
        parent_name = package.split(".")[0]
        parent = types.ModuleType(parent_name)
        module = types.ModuleType(package)
        for name in names:
            cls = {"Bool": Bool, "String": String}.get(name, type(name, (), {}))
            setattr(module, name, cls)
        module.Pose = Pose
        module.Quaternion = Quaternion
        parent.msg = module
        sys.modules[parent_name] = parent
        sys.modules[package] = module


def load_fusion_node():
    install_stubs()
    root = Path(__file__).resolve().parents[1]
    scripts = root / "wrappers/e2o_localization_fusion/scripts"
    sys.path.insert(0, str(scripts))
    path = scripts / "fusion_node.py"
    spec = importlib.util.spec_from_file_location("fusion_node", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_base_node(module, mode, active_source, metric_source=None, tertiary_source=None):
    """Builds a minimally-stubbed LocalizationFusion for exercising
    evaluate_fusion1/evaluate_fusion2 directly (bypassing the ROS plumbing and
    the ORB-alignment/overlap-reset bookkeeping done in evaluate_state_machine)."""
    metric_source = metric_source or module.FAST
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.mode = mode
    node.primary = metric_source
    node.metric_source = metric_source
    node.tertiary_source = tertiary_source or ""
    node.enable_tertiary = mode == "fusion1"
    node.active_source = active_source
    node.state = "INIT"
    node.recovery_stabilization = 3.0
    node.primary_recovery = 5.0
    node.minimum_dwell = 3.0
    node.failure_hold = 0.35
    node.last_switch_wall = 0.0
    node.require_recovery_consistency = False
    node.recovery_disagreement = {"position_m": None, "orientation_rad": None, "scale_ratio": None, "valid": False}
    node.disagreement = {"position_m": None, "orientation_rad": None, "scale_ratio": None, "valid": False}
    node.recovery_disagreement_m = 2.0
    node.recovery_disagreement_rad = 0.35
    node.max_disagreement_m = 4.0
    node.max_disagreement_rad = 0.6
    node.scale_ratio_min = 8.0
    node.scale_ratio_max = 15.0
    node.allow_orb_without_validated_scale = False
    node.cross_fast_from_orb = object()
    node.orb_metric_scale = 10.0
    node.nav_ok_pub = Publisher()
    node.event_pub = Publisher()
    node.append_event_log = lambda *args, **kwargs: None

    def healthy_source(name):
        data = module.SourceData(name)
        data.health = {"healthy": True, "reasons": []}
        data.healthy_since = 90.0
        return data

    def unhealthy_source(name, reasons):
        data = module.SourceData(name)
        data.health = {"healthy": False, "reasons": reasons}
        data.unhealthy_since = 90.0
        return data

    node.sources = {metric_source: healthy_source(metric_source), module.ORB: healthy_source(module.ORB)}
    if node.enable_tertiary:
        node.sources[node.tertiary_source] = healthy_source(node.tertiary_source)

    node.switched = None
    node.switch_to = lambda source, reason: setattr(node, "switched", (source, reason))
    return node


def set_unhealthy(node, source, reasons):
    node.sources[source].health = {"healthy": False, "reasons": reasons}
    node.sources[source].unhealthy_since = 90.0


def set_unusable(node, source):
    """Mark a source as never having been healthy, so source_usable() is False."""
    node.sources[source].health = {"healthy": False, "reasons": ["no_health_status"]}
    node.sources[source].healthy_since = None
    node.sources[source].unhealthy_since = 90.0


def test_fusion1():
    module = load_fusion_node()

    # metric unhealthy due to lidar/imu -> ORB sensor-specific fallback
    node = make_base_node(module, "fusion1", module.FAST, tertiary_source=module.LVISAM)
    set_unhealthy(node, module.FAST, ["lidar_unavailable"])
    node.evaluate_fusion1(100.0)
    assert node.switched == (module.ORB, "fast_livo2_unhealthy_sensor_fallback:lidar_unavailable")

    # metric unhealthy due to camera only -> LVI-SAM tertiary fallback
    node = make_base_node(module, "fusion1", module.FAST, tertiary_source=module.LVISAM)
    set_unhealthy(node, module.FAST, ["camera_unavailable"])
    node.evaluate_fusion1(100.0)
    assert node.switched == (module.LVISAM, "fast_livo2_unhealthy_camera_fallback:camera_unavailable")

    # metric unhealthy for a non-sensor-specific reason -> prefer LVI-SAM over ORB
    node = make_base_node(module, "fusion1", module.FAST, tertiary_source=module.LVISAM)
    set_unhealthy(node, module.FAST, ["unrealistic_acceleration"])
    node.evaluate_fusion1(100.0)
    assert node.switched == (module.LVISAM, "fast_livo2_unhealthy_fallback:unrealistic_acceleration")

    # metric unhealthy, tertiary not usable -> falls back to ORB
    node = make_base_node(module, "fusion1", module.FAST, tertiary_source=module.LVISAM)
    set_unhealthy(node, module.FAST, ["unrealistic_acceleration"])
    set_unusable(node, module.LVISAM)
    node.evaluate_fusion1(100.0)
    assert node.switched == (module.ORB, "fast_livo2_unhealthy_fallback:unrealistic_acceleration")

    # metric unhealthy, nothing usable -> no-fallback state, nav gated off
    node = make_base_node(module, "fusion1", module.FAST, tertiary_source=module.LVISAM)
    set_unhealthy(node, module.FAST, ["unrealistic_acceleration"])
    set_unusable(node, module.LVISAM)
    set_unusable(node, module.ORB)
    node.evaluate_fusion1(100.0)
    assert node.switched is None
    assert node.state == "PRIMARY_FAST_LIVO2_UNHEALTHY_NO_FALLBACK"
    assert node.nav_ok_pub.published[-1].data is False

    # tertiary active, primary recovered and stable -> smooth return to primary
    node = make_base_node(module, "fusion1", module.LVISAM, tertiary_source=module.LVISAM)
    node.last_switch_wall = 0.0
    node.evaluate_fusion1(100.0)
    assert node.switched == (module.FAST, "primary_recovered_continuity_aligned")

    # tertiary active, tertiary fails -> ORB fallback
    node = make_base_node(module, "fusion1", module.LVISAM, tertiary_source=module.LVISAM)
    set_unusable(node, module.FAST)
    set_unhealthy(node, module.LVISAM, ["imu_unavailable"])
    node.evaluate_fusion1(100.0)
    assert node.switched == (module.ORB, "lvisam_unhealthy_fallback:imu_unavailable")

    # ORB active, primary (lidar/imu) recovered -> switch back to primary
    node = make_base_node(module, "fusion1", module.ORB, tertiary_source=module.LVISAM)
    node.evaluate_fusion1(100.0)
    assert node.switched == (module.FAST, "primary_recovered_continuity_aligned")

    # ORB active, only camera still down (lidar/imu recovered but tertiary unusable
    # because camera_source unhealthy) -> stays on ORB until failure persists then fails
    node = make_base_node(module, "fusion1", module.ORB, tertiary_source=module.LVISAM)
    set_unusable(node, module.FAST)
    set_unusable(node, module.LVISAM)
    set_unhealthy(node, module.ORB, ["tracking_lost"])
    node.evaluate_fusion1(100.0)
    assert node.switched is None
    assert node.state == "FAILED_ALL_UNHEALTHY"
    assert node.active_source == module.FAILED
    print("fusion1 switching tests passed")


def test_fusion2():
    module = load_fusion_node()

    # metric (LVI-SAM) unhealthy, ORB usable -> switch to ORB
    node = make_base_node(module, "fusion2", module.LVISAM, metric_source=module.LVISAM)
    set_unhealthy(node, module.LVISAM, ["lidar_unavailable"])
    node.evaluate_fusion2(100.0)
    assert node.switched == (module.ORB, "lvisam_unhealthy_fallback:lidar_unavailable")

    # metric unhealthy, ORB not usable -> no-fallback state, nav gated off
    node = make_base_node(module, "fusion2", module.LVISAM, metric_source=module.LVISAM)
    set_unhealthy(node, module.LVISAM, ["lidar_unavailable"])
    set_unusable(node, module.ORB)
    node.evaluate_fusion2(100.0)
    assert node.switched is None
    assert node.state == "PRIMARY_LVISAM_UNHEALTHY_NO_ORB_FALLBACK"
    assert node.nav_ok_pub.published[-1].data is False

    # ORB active, LVI-SAM recovered and stable -> smooth return to LVI-SAM
    node = make_base_node(module, "fusion2", module.ORB, metric_source=module.LVISAM)
    node.evaluate_fusion2(100.0)
    assert node.switched == (module.LVISAM, "primary_recovered_continuity_aligned")

    # ORB active, nothing recovers and ORB itself fails -> fusion fails, no further fallback
    node = make_base_node(module, "fusion2", module.ORB, metric_source=module.LVISAM)
    set_unusable(node, module.LVISAM)
    set_unhealthy(node, module.ORB, ["tracking_lost"])
    node.declare_failed = lambda reason: (setattr(node, "state", "FAILED_ALL_UNHEALTHY"), setattr(node, "declared_failed_reason", reason))
    node.evaluate_fusion2(100.0)
    assert node.switched is None
    assert node.state == "FAILED_ALL_UNHEALTHY"
    assert node.declared_failed_reason == "orb_unhealthy_no_lvisam_fallback"
    print("fusion2 switching tests passed")


def main():
    test_fusion1()
    test_fusion2()
    print("fusion recovery state-machine tests passed")


if __name__ == "__main__":
    main()
