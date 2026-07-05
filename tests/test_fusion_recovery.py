#!/usr/bin/env python3
"""Pure-Python regression checks for the fusion1/fusion2 switching logic."""
import importlib.util
import json
import sys
import types
from pathlib import Path
import numpy as np


class Obj:
    pass


class Publisher:
    def __init__(self, *args, **kwargs):
        self.published = []

    def publish(self, msg):
        self.published.append(msg)


class DummyLock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


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

    # metric unhealthy for a non-sensor-specific reason -> do not switch away
    # from FAST, because ORB/LVI fallback is reserved for hard sensor loss.
    node = make_base_node(module, "fusion1", module.FAST, tertiary_source=module.LVISAM)
    set_unhealthy(node, module.FAST, ["unrealistic_acceleration"])
    node.evaluate_fusion1(100.0)
    assert node.switched is None
    assert node.state == "PRIMARY_FAST_LIVO2_UNHEALTHY_NO_FALLBACK"

    # metric unhealthy for a non-sensor-specific reason, tertiary not usable -> no fallback
    node = make_base_node(module, "fusion1", module.FAST, tertiary_source=module.LVISAM)
    set_unhealthy(node, module.FAST, ["unrealistic_acceleration"])
    set_unusable(node, module.LVISAM)
    node.evaluate_fusion1(100.0)
    assert node.switched is None
    assert node.state == "PRIMARY_FAST_LIVO2_UNHEALTHY_NO_FALLBACK"

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

    # Camera recovery path: LVI-SAM is metric-to-metric backup, so strict ORB
    # recovery overlap is not required to continuity-align back to FAST.
    node = make_base_node(module, "fusion1", module.LVISAM, tertiary_source=module.LVISAM)
    node.require_recovery_consistency = True
    node.last_switch_wall = 0.0
    node.evaluate_fusion1(100.0)
    assert node.switched == (module.FAST, "primary_recovered_without_recovery_overlap")

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

    # Example-style LiDAR recovery: when ORB is active and consistency is
    # required, primary cannot retake control until fresh FAST/ORB recovery
    # overlap is valid.
    node = make_base_node(module, "fusion1", module.ORB, tertiary_source=module.LVISAM)
    node.require_recovery_consistency = True
    node.evaluate_fusion1(100.0)
    assert node.switched is None
    node.recovery_disagreement = {"position_m": 0.2, "orientation_rad": 0.01, "scale_ratio": 10.0, "valid": True}
    node.evaluate_fusion1(100.0)
    assert node.switched == (module.FAST, "primary_recovered_and_consistent")

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


def test_metric_recovery_switch_preserves_continuity():
    module = load_fusion_node()
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.metric_source = module.FAST
    node.tertiary_source = ""
    node.enable_tertiary = False
    node.active_source = module.ORB
    node.last_output_T = np.eye(4)
    node.last_output_T[:3, 3] = [10.0, -2.0, 0.5]
    recovered = np.eye(4)
    recovered[:3, 3] = [2.0, 3.0, 0.0]
    data = module.SourceData(module.FAST)
    data.latest_T = recovered
    node.sources = {module.FAST: data, module.ORB: module.SourceData(module.ORB)}
    node.source_to_output = {module.FAST: np.eye(4), module.ORB: np.eye(4)}
    node.source_scale = {module.FAST: 1.0, module.ORB: 1.0}
    node.orb_metric_scale = 1.0
    node.orb_camera_to_base = np.eye(4)
    node.cross_fast_from_orb = None
    node.recovery_cross_fast_from_orb = None
    node.recovery_orb_metric_scale = None
    node.recovery_alignment_quality = {"position_rmse_m": None, "orientation_rmse_rad": None}
    node.synchronized_pairs = module.collections.deque(maxlen=10)
    node.recovery_pairs = module.collections.deque(maxlen=10)
    node.reset_recovery_alignment = lambda: None
    node.last_switch_wall = 0.0
    node.switch_start_wall = None
    node.switch_anchor_T = None
    node.last_output_source_stamp = {module.FAST: None, module.ORB: None}
    node.switch_count = 0
    node.state = ""
    node.pending_switch_event = None
    node.event_pub = Publisher()
    node.append_event_log = lambda *args, **kwargs: None

    node.switch_to(module.FAST, "primary_recovered_continuity_aligned")
    aligned = node.source_to_output[module.FAST] @ recovered
    assert np.allclose(aligned, node.last_output_T)
    assert node.active_source == module.FAST
    print("metric recovery continuity switch test passed")


def test_weighted_fusion_blends_healthy_metric_and_orb():
    module = load_fusion_node()
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.weighted_fusion_enabled = True
    node.mode = "fusion1"
    node.metric_source = module.FAST
    node.enable_tertiary = False
    node.tertiary_source = ""
    node.active_source = module.FAST
    node.metric_nominal_weight = 0.9
    node.orb_nominal_weight = 0.1
    node.orb_backup_weight = 1.0
    node.weight_rise_time = 6.0
    node.weight_fall_time = 1.0
    node.max_disagreement_m = 4.0
    node.max_disagreement_rad = 0.6
    node.recovery_disagreement_m = 2.0
    node.recovery_disagreement_rad = 0.35
    node.scale_ratio_min = 1.0
    node.scale_ratio_max = 1.0
    node.disagreement = {"position_m": 0.2, "orientation_rad": 0.01, "scale_ratio": 1.0, "valid": True}
    node.fusion_weights = {module.FAST: 0.0, module.ORB: 0.0}
    node.target_fusion_weights = dict(node.fusion_weights)
    node.last_weight_update_wall = None
    node.last_output_T = None
    node.weighted_last_stamp = None
    node.weighted_active_label = module.FAILED
    node.weighted_state = "WAITING_FOR_LOCALIZATION"
    node.source_to_output = {module.FAST: np.eye(4), module.ORB: np.eye(4)}
    node.orb_metric_scale = 1.0
    node.cross_fast_from_orb = np.eye(4)
    node.orb_camera_to_base = np.eye(4)
    node.source_scale = {module.FAST: 1.0, module.ORB: 1.0}
    node.event_pub = Publisher()
    node.append_event_log = lambda *args, **kwargs: None

    def make_msg(stamp):
        msg = Obj()
        msg.header = Obj()
        msg.header.stamp = Obj()
        msg.header.stamp.to_sec = lambda: stamp
        return msg

    fast_T = np.eye(4)
    orb_T = np.eye(4)
    orb_T[:3, 3] = [10.0, 0.0, 0.0]
    fast = module.SourceData(module.FAST)
    fast.latest_msg = make_msg(10.0)
    fast.latest_T = fast_T
    fast.health = {"healthy": True, "reasons": []}
    orb = module.SourceData(module.ORB)
    orb.latest_msg = make_msg(10.1)
    orb.latest_T = orb_T
    orb.health = {"healthy": True, "reasons": []}
    node.sources = {module.FAST: fast, module.ORB: orb}

    msg, fused = node.weighted_fused_pose(100.0)
    assert msg.header.stamp.to_sec() == 10.1
    assert node.weighted_active_label == "weighted"
    assert node.weighted_state == "FUSED_FAST_LIVO2_ORB_SLAM3"
    assert abs(fused[0, 3] - 1.0) < 1.0e-6, fused[0, 3]
    print("weighted fusion blend test passed")


def test_weighted_fusion_uses_lvisam_when_fast_recovery_is_bad():
    module = load_fusion_node()
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.weighted_fusion_enabled = True
    node.mode = "fusion1"
    node.metric_source = module.FAST
    node.enable_tertiary = True
    node.tertiary_source = module.LVISAM
    node.weighted_sources = [module.FAST, module.LVISAM, module.ORB]
    node.metric_nominal_weight = 0.9
    node.lvisam_recovery_weight = 1.0
    node.orb_nominal_weight = 0.1
    node.orb_backup_weight = 1.0
    node.max_disagreement_m = 4.0
    node.max_disagreement_rad = 0.6
    node.disagreement = {"position_m": 0.2, "orientation_rad": 0.01, "scale_ratio": 1.0, "valid": True}
    node.fusion_weights = {module.FAST: 0.2, module.LVISAM: 0.0, module.ORB: 0.8}
    node.source_to_output = {module.FAST: np.eye(4), module.LVISAM: np.eye(4), module.ORB: np.eye(4)}
    node.source_scale = {module.FAST: 1.0, module.LVISAM: 1.0, module.ORB: 1.0}
    node.orb_metric_scale = 1.0
    node.cross_fast_from_orb = np.eye(4)
    node.orb_camera_to_base = np.eye(4)
    node.last_output_T = np.eye(4)

    def make_source(name, healthy=True, x=0.0):
        data = module.SourceData(name)
        msg = Obj()
        msg.header = Obj()
        msg.header.stamp = Obj()
        msg.header.stamp.to_sec = lambda: 10.0
        data.latest_msg = msg
        data.latest_T = np.eye(4)
        data.latest_T[:3, 3] = [x, 0.0, 0.0]
        data.health = {"healthy": healthy, "reasons": [] if healthy else ["position_discontinuity", "unrealistic_velocity"]}
        return data

    node.sources = {
        module.FAST: make_source(module.FAST, healthy=False, x=100.0),
        module.LVISAM: make_source(module.LVISAM, healthy=True, x=0.2),
        module.ORB: make_source(module.ORB, healthy=True, x=0.1),
    }

    targets = node.weighted_targets(100.0)
    assert targets[module.FAST] == 0.0
    assert abs(targets[module.LVISAM] - 1.0) < 1.0e-6
    assert targets[module.ORB] == 0.0
    print("weighted LVI-SAM recovery target test passed")


def test_recovered_lidar_source_is_rebased_to_current_fused_pose():
    module = load_fusion_node()
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.metric_source = module.FAST
    node.enable_tertiary = True
    node.tertiary_source = module.LVISAM
    node.weighted_sources = [module.FAST, module.LVISAM, module.ORB]
    node.last_output_T = np.eye(4)
    node.last_output_T[:3, 3] = [4.0, 5.0, 0.0]
    node.fusion_weights = {module.FAST: 0.0, module.LVISAM: 0.0, module.ORB: 1.0}
    node.source_to_output = {module.FAST: np.eye(4), module.LVISAM: np.eye(4), module.ORB: np.eye(4)}
    node.source_scale = {module.FAST: 1.0, module.LVISAM: 1.0, module.ORB: 1.0}
    node.force_reanchor = {module.LVISAM: True}
    node.orb_metric_scale = 1.0
    node.cross_fast_from_orb = np.eye(4)
    node.orb_camera_to_base = np.eye(4)
    node.event_pub = Publisher()
    node.append_event_log = lambda *args, **kwargs: None

    lvi = module.SourceData(module.LVISAM)
    msg = Obj()
    msg.header = Obj()
    msg.header.stamp = Obj()
    msg.header.stamp.to_sec = lambda: 10.0
    lvi.latest_msg = msg
    lvi.latest_T = np.eye(4)
    lvi.latest_T[:3, 3] = [1000.0, -200.0, 0.0]
    lvi.health = {"healthy": True, "reasons": []}
    node.sources = {module.LVISAM: lvi, module.FAST: module.SourceData(module.FAST), module.ORB: module.SourceData(module.ORB)}

    assert node.source_output_consistent(module.LVISAM)
    rebased = node.transformed_source_pose(module.LVISAM)[1]
    assert np.allclose(rebased, node.last_output_T)
    assert node.force_reanchor[module.LVISAM] is False
    print("recovered LiDAR source rebase test passed")


def test_recovered_inactive_metric_pose_is_rebased_before_path_publish():
    module = load_fusion_node()
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.metric_source = module.FAST
    node.enable_tertiary = True
    node.tertiary_source = module.LVISAM
    node.last_output_T = np.eye(4)
    node.last_output_T[:3, 3] = [7.0, -2.0, 0.0]
    node.source_to_output = {module.FAST: np.eye(4), module.LVISAM: np.eye(4), module.ORB: np.eye(4)}
    node.source_scale = {module.FAST: 1.0, module.LVISAM: 1.0, module.ORB: 1.0}
    node.force_reanchor = {module.FAST: True, module.LVISAM: False, module.ORB: False}
    node.orb_metric_scale = 1.0
    node.cross_fast_from_orb = np.eye(4)
    node.orb_camera_to_base = np.eye(4)
    node.event_pub = Publisher()
    node.append_event_log = lambda *args, **kwargs: None

    fast = module.SourceData(module.FAST)
    msg = Obj()
    msg.header = Obj()
    msg.header.stamp = Obj()
    msg.header.stamp.to_sec = lambda: 20.0
    fast.latest_msg = msg
    fast.latest_T = np.eye(4)
    fast.latest_T[:3, 3] = [1200.0, -900.0, 0.0]
    fast.health = {"healthy": True, "reasons": []}
    node.sources = {module.FAST: fast, module.LVISAM: module.SourceData(module.LVISAM), module.ORB: module.SourceData(module.ORB)}

    rebased = node.transformed_source_pose(module.FAST)[1]
    assert np.allclose(rebased, node.last_output_T)
    assert node.force_reanchor[module.FAST] is False
    print("inactive recovered metric path rebase test passed")


def test_active_metric_recovery_is_rebased_before_publish():
    module = load_fusion_node()
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.metric_source = module.FAST
    node.enable_tertiary = False
    node.tertiary_source = ""
    node.active_source = module.FAST
    node.last_output_T = np.eye(4)
    node.last_output_T[:3, 3] = [9.0, 1.0, 0.0]
    node.last_output_source_stamp = {module.FAST: None}
    node.source_to_output = {module.FAST: np.eye(4), module.ORB: np.eye(4)}
    node.source_scale = {module.FAST: 1.0, module.ORB: 1.0}
    node.force_reanchor = {module.FAST: True, module.ORB: False}
    node.switch_anchor_T = None
    node.switch_start_wall = None
    node.blend_duration = 1.0
    node.orb_metric_scale = 1.0
    node.cross_fast_from_orb = np.eye(4)
    node.orb_camera_to_base = np.eye(4)
    node.event_pub = Publisher()
    node.append_event_log = lambda *args, **kwargs: None

    fast = module.SourceData(module.FAST)
    msg = Obj()
    msg.header = Obj()
    msg.header.stamp = Obj()
    msg.header.stamp.to_sec = lambda: 21.0
    fast.latest_msg = msg
    fast.latest_stamp = 21.0
    fast.latest_T = np.eye(4)
    fast.latest_T[:3, 3] = [-600.0, 300.0, 0.0]
    fast.health = {"healthy": True, "reasons": []}
    node.sources = {module.FAST: fast, module.ORB: module.SourceData(module.ORB)}

    _msg, rebased = node.transformed_active_pose(100.0)
    assert np.allclose(rebased, node.last_output_T)
    assert node.force_reanchor[module.FAST] is False
    print("active metric recovery publish rebase test passed")


def test_metric_restart_health_reanchors_without_force_admitting_source():
    module = load_fusion_node()
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.lock = DummyLock()
    node.metric_source = module.FAST
    node.enable_tertiary = True
    node.tertiary_source = module.LVISAM
    node.weighted_sources = [module.FAST, module.LVISAM, module.ORB]
    node.lidar_recovery_override = 8.0
    node.last_output_T = np.eye(4)
    node.last_output_T[:3, 3] = [2.0, 3.0, 0.0]
    node.fusion_weights = {module.FAST: 0.0, module.LVISAM: 0.0, module.ORB: 1.0}
    node.source_to_output = {module.FAST: np.eye(4), module.LVISAM: np.eye(4), module.ORB: np.eye(4)}
    node.source_scale = {module.FAST: 1.0, module.LVISAM: 1.0, module.ORB: 1.0}
    node.force_reanchor = {module.FAST: False, module.LVISAM: False, module.ORB: False}
    node.recovery_override_until = {module.FAST: 0.0, module.LVISAM: 0.0, module.ORB: 0.0}
    node.event_pub = Publisher()
    node.append_event_log = lambda *args, **kwargs: None
    node.orb_metric_scale = 1.0
    node.cross_fast_from_orb = np.eye(4)
    node.orb_camera_to_base = np.eye(4)

    fast = module.SourceData(module.FAST)
    msg = Obj()
    msg.header = Obj()
    msg.header.stamp = Obj()
    msg.header.stamp.to_sec = lambda: 11.0
    fast.latest_msg = msg
    fast.latest_T = np.eye(4)
    fast.latest_T[:3, 3] = [500.0, 100.0, 0.0]
    fast.health = {"healthy": False, "reasons": ["lidar_unavailable"]}
    node.sources = {module.FAST: fast, module.LVISAM: module.SourceData(module.LVISAM), module.ORB: module.SourceData(module.ORB)}

    status = {
        "healthy": False,
        "reasons": ["position_discontinuity", "unrealistic_velocity"],
        "sensor_available": {"lidar": True, "imu": True},
    }
    node.health_cb(module.FAST, String(data=json.dumps(status)))

    assert node.force_reanchor[module.FAST] is True
    assert not node.source_fusion_ready(module.FAST)
    assert node.source_output_consistent(module.FAST)
    rebased = node.transformed_source_pose(module.FAST)[1]
    assert np.allclose(rebased, node.last_output_T)
    print("metric restart health reanchor-only test passed")


def test_camera_recovery_reanchors_without_force_admitting_fast():
    module = load_fusion_node()
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.lock = DummyLock()
    node.metric_source = module.FAST
    node.enable_tertiary = True
    node.tertiary_source = module.LVISAM
    node.weighted_sources = [module.FAST, module.LVISAM, module.ORB]
    node.lidar_recovery_override = 8.0
    node.last_output_T = np.eye(4)
    node.last_output_T[:3, 3] = [6.0, -1.0, 0.0]
    node.fusion_weights = {module.FAST: 0.0, module.LVISAM: 0.0, module.ORB: 1.0}
    node.source_to_output = {module.FAST: np.eye(4), module.LVISAM: np.eye(4), module.ORB: np.eye(4)}
    node.source_scale = {module.FAST: 1.0, module.LVISAM: 1.0, module.ORB: 1.0}
    node.force_reanchor = {module.FAST: False, module.LVISAM: False, module.ORB: False}
    node.recovery_override_until = {module.FAST: 0.0, module.LVISAM: 0.0, module.ORB: 0.0}
    node.event_pub = Publisher()
    node.append_event_log = lambda *args, **kwargs: None
    node.orb_metric_scale = 1.0
    node.cross_fast_from_orb = np.eye(4)
    node.orb_camera_to_base = np.eye(4)

    fast = module.SourceData(module.FAST)
    msg = Obj()
    msg.header = Obj()
    msg.header.stamp = Obj()
    msg.header.stamp.to_sec = lambda: 12.0
    fast.latest_msg = msg
    fast.latest_T = np.eye(4)
    fast.latest_T[:3, 3] = [800.0, -400.0, 0.0]
    fast.health = {"healthy": False, "reasons": ["camera_unavailable"]}
    node.sources = {module.FAST: fast, module.LVISAM: module.SourceData(module.LVISAM), module.ORB: module.SourceData(module.ORB)}

    status = {
        "healthy": False,
        "reasons": ["position_discontinuity", "unrealistic_velocity"],
        "sensor_available": {"lidar": True, "imu": True, "camera": True},
    }
    node.health_cb(module.FAST, String(data=json.dumps(status)))

    assert node.force_reanchor[module.FAST] is True
    assert not node.source_fusion_ready(module.FAST)
    assert node.source_output_consistent(module.FAST)
    rebased = node.transformed_source_pose(module.FAST)[1]
    assert np.allclose(rebased, node.last_output_T)
    print("camera recovery FAST reanchor-only test passed")


def test_available_sensors_do_not_force_fast_target_with_bad_health_reason():
    module = load_fusion_node()
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.lock = DummyLock()
    node.weighted_fusion_enabled = True
    node.mode = "fusion1"
    node.metric_source = module.FAST
    node.enable_tertiary = True
    node.tertiary_source = module.LVISAM
    node.weighted_sources = [module.FAST, module.LVISAM, module.ORB]
    node.metric_nominal_weight = 0.9
    node.lvisam_recovery_weight = 1.0
    node.orb_nominal_weight = 0.1
    node.orb_backup_weight = 1.0
    node.lidar_recovery_override = 8.0
    node.max_disagreement_m = 4.0
    node.max_disagreement_rad = 0.6
    node.scale_ratio_min = 1.0
    node.scale_ratio_max = 1.0
    node.disagreement = {"position_m": 0.2, "orientation_rad": 0.01, "scale_ratio": 1.0, "valid": True}
    node.last_output_T = np.eye(4)
    node.last_output_T[:3, 3] = [3.0, 2.0, 0.0]
    node.fusion_weights = {module.FAST: 0.0, module.LVISAM: 0.0, module.ORB: 1.0}
    node.source_to_output = {module.FAST: np.eye(4), module.LVISAM: np.eye(4), module.ORB: np.eye(4)}
    node.source_scale = {module.FAST: 1.0, module.LVISAM: 1.0, module.ORB: 1.0}
    node.force_reanchor = {module.FAST: False, module.LVISAM: False, module.ORB: False}
    node.recovery_override_until = {module.FAST: 0.0, module.LVISAM: 0.0, module.ORB: 0.0}
    node.orb_metric_scale = 1.0
    node.cross_fast_from_orb = np.eye(4)
    node.orb_camera_to_base = np.eye(4)
    node.event_pub = Publisher()
    node.append_event_log = lambda *args, **kwargs: None

    def make_source(name, stamp, x, healthy=True):
        data = module.SourceData(name)
        msg = Obj()
        msg.header = Obj()
        msg.header.stamp = Obj()
        msg.header.stamp.to_sec = lambda: stamp
        data.latest_msg = msg
        data.latest_T = np.eye(4)
        data.latest_T[:3, 3] = [x, 0.0, 0.0]
        data.health = {"healthy": healthy, "reasons": []}
        return data

    fast = make_source(module.FAST, 13.0, 500.0, healthy=False)
    fast.health = {
        "healthy": False,
        "reasons": ["pose_rate_too_low"],
        "sensor_available": {"lidar": True, "imu": True, "camera": True},
    }
    orb = make_source(module.ORB, 13.1, 0.1, healthy=True)
    lvi = make_source(module.LVISAM, 13.0, 0.2, healthy=True)
    node.sources = {module.FAST: fast, module.LVISAM: lvi, module.ORB: orb}

    node.health_cb(module.FAST, String(data=json.dumps(fast.health)))
    targets = node.weighted_targets(100.0)
    assert targets[module.FAST] == 0.0
    assert abs(targets[module.LVISAM] - 1.0) < 1.0e-6
    assert targets[module.ORB] == 0.0
    rebased = node.transformed_source_pose(module.FAST)[1]
    assert np.allclose(rebased, node.last_output_T)
    print("available sensors do not force bad FAST target test passed")


def test_orb_jump_is_reanchored_to_current_fused_pose():
    module = load_fusion_node()
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.metric_source = module.FAST
    node.enable_tertiary = False
    node.tertiary_source = ""
    node.last_output_T = np.eye(4)
    node.last_output_T[:3, 3] = [1.0, 2.0, 0.0]
    node.fusion_weights = {module.FAST: 0.0, module.ORB: 1.0}
    node.source_to_output = {module.FAST: np.eye(4), module.ORB: np.eye(4)}
    node.source_scale = {module.FAST: 1.0, module.ORB: 1.0}
    node.force_reanchor = {module.ORB: False}
    node.max_disagreement_m = 4.0
    node.max_disagreement_rad = 0.6
    node.orb_metric_scale = 1.0
    node.cross_fast_from_orb = np.eye(4)
    node.orb_camera_to_base = np.eye(4)
    node.event_pub = Publisher()
    node.append_event_log = lambda *args, **kwargs: None

    orb = module.SourceData(module.ORB)
    msg = Obj()
    msg.header = Obj()
    msg.header.stamp = Obj()
    msg.header.stamp.to_sec = lambda: 12.0
    orb.latest_msg = msg
    orb.latest_T = np.eye(4)
    orb.latest_T[:3, 3] = [200.0, -50.0, 0.0]
    orb.health = {"healthy": True, "reasons": []}
    node.sources = {module.ORB: orb, module.FAST: module.SourceData(module.FAST)}

    assert node.source_output_consistent(module.ORB)
    rebased = node.transformed_source_pose(module.ORB)[1]
    assert np.allclose(rebased, node.last_output_T)
    print("ORB loop-closure fusion reanchor test passed")


def test_weights_decay_without_renormalizing_when_all_sources_unusable():
    module = load_fusion_node()
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.fusion_weights = {module.FAST: 1.0, module.ORB: 0.0}
    node.target_fusion_weights = dict(node.fusion_weights)
    node.last_weight_update_wall = 0.0
    node.weight_rise_time = 6.0
    node.weight_fall_time = 1.0
    node.sources = {module.FAST: module.SourceData(module.FAST), module.ORB: module.SourceData(module.ORB)}
    node.source_to_output = {module.FAST: np.eye(4), module.ORB: np.eye(4)}
    node.source_scale = {module.FAST: 1.0, module.ORB: 1.0}
    node.last_output_T = None
    node.event_pub = Publisher()
    node.append_event_log = lambda *args, **kwargs: None

    node.update_fusion_weights({module.FAST: 0.0, module.ORB: 0.0}, 1.0)
    assert node.fusion_weights[module.FAST] == 0.0
    assert node.fusion_weights[module.ORB] == 0.0
    print("all-unusable weight decay test passed")


def test_weighted_timer_does_not_publish_legacy_fallback():
    module = load_fusion_node()
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.lock = DummyLock()
    node.weighted_fusion_enabled = True
    node.mode = "fusion1"
    node.state = "PRIMARY_FAST_LIVO2_OK"
    node.weighted_active_label = module.FAILED
    node.active_source = module.FAST
    node.metric_source = module.FAST
    node.stop_navigation_on_failure = True
    node.last_output_T = np.eye(4)
    node.nav_ok_pub = Publisher()
    node.active_pub = Publisher()
    node.status_pub = Publisher()
    node.evaluate_state_machine = lambda now: None
    node.weighted_fused_pose = lambda now: None
    node.transformed_active_pose = lambda now: ("legacy_msg", np.eye(4))
    node.publish_metric_output = lambda msg, T: None
    node.publish_tf_for_pose = lambda T, stamp: None
    node.status_payload = lambda: {"active_source": "weighted", "valid": False}

    fast = module.SourceData(module.FAST)
    fast.latest_msg = None
    fast.latest_T = None
    fast.health = {"healthy": True, "reasons": []}
    node.sources = {module.FAST: fast, module.ORB: module.SourceData(module.ORB)}

    published = []
    node.publish_output = lambda *args, **kwargs: published.append((args, kwargs))

    node.timer_cb(None)
    assert published == []
    assert node.active_pub.published[-1].data == "weighted"
    assert node.nav_ok_pub.published[-1].data is False
    print("weighted timer legacy fallback guard test passed")


def test_bare_discontinuity_on_active_source_does_not_reanchor_to_jumped_pose():
    """No real sensor outage occurred -- a spontaneous pose corruption on the
    already-active source must not be folded into a fresh anchor. Regression
    for the reported ~1000m jump-then-corrupt-forever bug: previously any
    discontinuity/unrealistic-kinematics reason was treated as a legitimate
    'sensor just came back, rebase me' restart even with no outage history."""
    module = load_fusion_node()
    node = module.LocalizationFusion.__new__(module.LocalizationFusion)
    node.lock = DummyLock()
    node.metric_source = module.FAST
    node.enable_tertiary = True
    node.tertiary_source = module.LVISAM
    node.weighted_sources = [module.FAST, module.LVISAM, module.ORB]
    node.lidar_recovery_override = 8.0
    node.active_source = module.FAST
    node.last_output_T = np.eye(4)
    node.last_output_T[:3, 3] = [5.0, 4.0, 0.0]
    node.last_output_source_stamp = {module.FAST: None}
    node.source_to_output = {module.FAST: np.eye(4), module.LVISAM: np.eye(4), module.ORB: np.eye(4)}
    node.source_scale = {module.FAST: 1.0, module.LVISAM: 1.0, module.ORB: 1.0}
    node.force_reanchor = {module.FAST: False, module.LVISAM: False, module.ORB: False}
    node.recovery_override_until = {module.FAST: 0.0, module.LVISAM: 0.0, module.ORB: 0.0}
    node.switch_anchor_T = None
    node.switch_start_wall = None
    node.blend_duration = 1.0
    node.orb_metric_scale = 1.0
    node.cross_fast_from_orb = np.eye(4)
    node.orb_camera_to_base = np.eye(4)
    node.event_pub = Publisher()
    node.append_event_log = lambda *args, **kwargs: None

    fast = module.SourceData(module.FAST)
    fast.health = {"healthy": True, "reasons": []}
    node.sources = {module.FAST: fast, module.LVISAM: module.SourceData(module.LVISAM), module.ORB: module.SourceData(module.ORB)}

    # No sensor was ever reported unavailable for this source: never seed
    # sensor_outage_active. Now a spontaneous ~1000m corrupted pose appears
    # with no *_unavailable reason at all -- a genuine estimator fault.
    status = {
        "healthy": False,
        "reasons": ["position_discontinuity", "unrealistic_velocity"],
        "sensor_available": {"lidar": True, "imu": True, "camera": True},
    }
    node.health_cb(module.FAST, String(data=json.dumps(status)))

    msg = Obj()
    msg.header = Obj()
    msg.header.stamp = Obj()
    msg.header.stamp.to_sec = lambda: 30.0
    fast.latest_msg = msg
    fast.latest_stamp = 30.0
    fast.latest_T = np.eye(4)
    fast.latest_T[:3, 3] = [1005.0, 904.0, 0.0]

    _msg, output = node.transformed_active_pose(100.0)
    # Must NOT be silently rebased to last_output_T -- the corrupted jump has
    # to remain visible in the output so the ordinary failure_hold_sec
    # failover (driven by health.healthy) rejects this source, instead of
    # the fusion layer adopting the corrupted pose as its new baseline.
    assert not np.allclose(output, node.last_output_T)
    assert np.allclose(output[:3, 3], [1005.0, 904.0, 0.0])
    print("bare discontinuity active-source no-reanchor test passed")


def main():
    test_fusion1()
    test_fusion2()
    test_metric_recovery_switch_preserves_continuity()
    test_weighted_fusion_blends_healthy_metric_and_orb()
    test_weighted_fusion_uses_lvisam_when_fast_recovery_is_bad()
    test_recovered_lidar_source_is_rebased_to_current_fused_pose()
    test_recovered_inactive_metric_pose_is_rebased_before_path_publish()
    test_active_metric_recovery_is_rebased_before_publish()
    test_metric_restart_health_reanchors_without_force_admitting_source()
    test_camera_recovery_reanchors_without_force_admitting_fast()
    test_available_sensors_do_not_force_fast_target_with_bad_health_reason()
    test_orb_jump_is_reanchored_to_current_fused_pose()
    test_weights_decay_without_renormalizing_when_all_sources_unusable()
    test_weighted_timer_does_not_publish_legacy_fallback()
    test_bare_discontinuity_on_active_source_does_not_reanchor_to_jumped_pose()
    print("fusion recovery state-machine tests passed")


if __name__ == "__main__":
    main()
