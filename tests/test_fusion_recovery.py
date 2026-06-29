#!/usr/bin/env python3
"""Pure-Python regression checks for primary recovery switching."""
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
    rospy.Time = type("Time", (), {"now": staticmethod(lambda: Obj())})
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


def make_node(module, recovery_disagreement):
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.primary = module.FAST
    node.metric_source = module.FAST
    node.secondary = module.ORB
    node.active_source = module.ORB
    node.state = "BACKUP_ORB_SLAM3"
    node.primary_recovery = 5.0
    node.minimum_dwell = 3.0
    node.failure_hold = 0.35
    node.last_switch_wall = 90.0
    node.require_recovery_consistency = True
    node.recovery_disagreement = recovery_disagreement
    node.recovery_disagreement_m = 2.0
    node.recovery_disagreement_rad = 0.35
    node.disagreement = {"position_m": None, "orientation_rad": None, "scale_ratio": None, "valid": False}
    node.scale_ratio_min = 8.0
    node.scale_ratio_max = 15.0
    node.cross_fast_from_orb = object()
    node.orb_metric_scale = 10.0
    node.last_metric_fault_reset_reason = None
    node.nav_ok_pub = Publisher()

    metric = module.SourceData(module.FAST)
    metric.health = {"healthy": True, "reasons": []}
    metric.healthy_since = 90.0
    orb = module.SourceData(module.ORB)
    orb.health = {"healthy": True, "reasons": []}
    orb.healthy_since = 90.0
    node.sources = {module.FAST: metric, module.ORB: orb}
    node.switched = None
    node.switch_to = lambda source, reason: setattr(node, "switched", (source, reason))
    return node


def make_fallback_node(module, metric_reasons, metric_source=None, scale_ready=True):
    metric_source = metric_source or module.FAST
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.primary = metric_source
    node.metric_source = metric_source
    node.secondary = module.ORB
    node.active_source = metric_source
    node.state = f"PRIMARY_{metric_source.upper()}"
    node.recovery_stabilization = 3.0
    node.failure_hold = 0.35
    node.last_metric_fault_reset_reason = None
    node.nav_ok_pub = Publisher()
    node.cross_fast_from_orb = object() if scale_ready else None
    node.orb_metric_scale = 10.0 if scale_ready else None
    node.allow_orb_without_validated_scale = False

    metric = module.SourceData(metric_source)
    metric.health = {"healthy": False, "reasons": metric_reasons}
    metric.unhealthy_since = 90.0
    orb = module.SourceData(module.ORB)
    orb.health = {"healthy": True, "reasons": []}
    orb.healthy_since = 90.0
    node.sources = {metric_source: metric, module.ORB: orb}
    node.switched = None
    node.switch_to = lambda source, reason: setattr(node, "switched", (source, reason))
    node.clear_overlap_buffers = lambda reason: None
    return node


def main():
    module = load_fusion_node()
    missing_overlap = {"position_m": None, "orientation_rad": None, "scale_ratio": None, "valid": False}
    node = make_node(module, missing_overlap)
    node.evaluate_state_machine(100.0)
    assert node.switched == (module.FAST, "primary_recovered_without_recovery_overlap")

    bad_overlap = {"position_m": 4.0, "orientation_rad": 0.1, "scale_ratio": 10.0, "valid": True}
    node = make_node(module, bad_overlap)
    node.evaluate_state_machine(100.0)
    assert node.switched is None

    node = make_fallback_node(module, ["unrealistic_acceleration"])
    node.evaluate_state_machine(100.0)
    assert node.switched is None
    assert node.state == "PRIMARY_FAST_LIVO2_UNHEALTHY_NO_ORB_FALLBACK"

    node = make_fallback_node(module, ["lidar_unavailable"])
    node.evaluate_state_machine(100.0)
    assert node.switched == (module.ORB, "active_unhealthy:lidar_unavailable")

    node = make_fallback_node(module, ["lidar_unavailable"], metric_source=module.LVISAM, scale_ready=True)
    node.evaluate_state_machine(100.0)
    assert node.switched == (module.ORB, "active_unhealthy:lidar_unavailable")

    node = make_fallback_node(module, ["lidar_unavailable"], metric_source=module.LVISAM, scale_ready=False)
    node.evaluate_state_machine(100.0)
    assert node.switched is None
    print("fusion recovery state-machine tests passed")


if __name__ == "__main__":
    main()
