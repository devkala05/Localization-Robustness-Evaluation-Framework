#!/usr/bin/env python3
"""Dataset-configured sensor adapter for localization estimators.

It republishes the original bag streams to the native topics expected by the
estimators, converts the Velodyne per-point ``time`` field from seconds to
microseconds for FAST-LIVO2 when configured, preserves LVI-SAM point timing in
seconds, publishes CameraInfo, and exposes deterministic fault modes through
``/e2o_faults/<sensor>/*`` ROS parameters.

No estimator implementation is changed by this node.
"""
import collections
import copy
import math
import threading
import time
from typing import Deque, Dict, Optional, Tuple

import numpy as np
import cv2
import rospy
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import CameraInfo, CompressedImage, Image, Imu, PointCloud2, PointField


class StreamFaultGate:
    """Runtime-configurable pass/drop/freeze/delay gate for one sensor stream.

    Mode/delay parameters are cached and refreshed on a slow periodic timer
    instead of being re-queried from the ROS parameter server on every
    message. rospy.get_param() is an XML-RPC round trip to the master; at
    combined native sensor rates (LiDAR + IMU + camera + depth can exceed
    100 Hz together) doing that round trip per message serializes real-time
    sensor delivery behind network calls. A 5 Hz refresh is far more than
    enough for a runtime fault-injection toggle used by test operators, and
    is not part of the real-time data path.

    Bookkeeping (mode transitions, frozen snapshot, delay queue) is guarded
    by a lock scoped to THIS gate only, so one sensor stream's processing
    never blocks another's — each sensor is an independent pipeline.
    """

    MODE_REFRESH_PERIOD_SEC = 0.2

    def __init__(self, name: str, publish_callback):
        self.name = name
        self.publish_callback = publish_callback
        self.frozen = None
        self.delay_queue: Deque[Tuple[float, object]] = collections.deque()
        self.last_mode = "pass"
        self.lock = threading.Lock()
        self._cached_mode = "pass"
        self._cached_delay_sec = 1.0
        self._last_mode_refresh = 0.0

    @property
    def prefix(self) -> str:
        return f"/e2o_faults/{self.name}"

    def refresh_mode(self, now: float) -> None:
        if now - self._last_mode_refresh < self.MODE_REFRESH_PERIOD_SEC:
            return
        self._last_mode_refresh = now
        mode = str(rospy.get_param(f"{self.prefix}/mode", "pass")).strip().lower()
        delay_sec = max(0.0, float(rospy.get_param(f"{self.prefix}/delay_sec", 1.0)))
        with self.lock:
            self._cached_mode = mode
            self._cached_delay_sec = delay_sec

    def handle(self, msg) -> None:
        # Heavy work (the actual publish_callback, which does per-message
        # numpy/cv2 processing) always runs OUTSIDE the lock so it can never
        # block a concurrent flush()/mode transition, and so this gate's own
        # bookkeeping stays cheap and fast.
        with self.lock:
            mode = self._cached_mode
            if mode != self.last_mode:
                if mode != "delay":
                    self.delay_queue.clear()
                if mode == "pass":
                    self.frozen = None
                self.last_mode = mode
            if mode == "drop":
                return
            if mode == "freeze":
                if self.frozen is None:
                    self.frozen = copy.deepcopy(msg)
                frozen_copy = copy.deepcopy(self.frozen)
            elif mode == "delay":
                self.delay_queue.append((time.monotonic() + self._cached_delay_sec, copy.deepcopy(msg)))
                return
            else:
                if mode != "pass":
                    rospy.logwarn_throttle(2.0, "[E2OAdapter] unknown %s mode=%s; passing", self.name, mode)
                frozen_copy = None
        # NOTE: no unconditional "self.frozen = copy.deepcopy(msg)" on the
        # pass-through path here (unlike the previous implementation). That
        # deep-copied every single message — including full LiDAR scans and
        # raw camera/depth frames — purely as a defensive snapshot for a
        # fault mode that, in normal (non-faulted) real-time operation, is
        # never entered. It doubled the per-message memcpy/CPU cost of the
        # entire real-time data path for no functional benefit: a frozen
        # snapshot is only ever needed once "freeze" mode is actually
        # requested, at which point it is captured lazily above.
        self.publish_callback(frozen_copy if mode == "freeze" else msg)

    def flush(self, now: float) -> None:
        to_publish = []
        with self.lock:
            while self.delay_queue and self.delay_queue[0][0] <= now:
                _, msg = self.delay_queue.popleft()
                to_publish.append(msg)
        for msg in to_publish:
            self.publish_callback(msg)


class E2OSensorAdapter:
    def __init__(self) -> None:
        config_namespace = str(rospy.get_param("~config_namespace", "/e2o")).rstrip("/")
        cfg = rospy.get_param(f"{config_namespace}/adapter", {})
        topics = dict(cfg.get("topics", {}))
        topics["lidar"] = rospy.get_param("~source_lidar_topic", topics.get("lidar", "/lidar103/velodyne_points"))
        topics["imu"] = rospy.get_param("~source_imu_topic", topics.get("imu", "/mavros/imu/data"))
        topics["camera"] = rospy.get_param("~source_camera_topic", topics.get("camera", "/camera/color/image_raw"))
        topics["depth"] = rospy.get_param("~source_depth_topic", topics.get("depth", "/camera/depth/image_rect_raw"))
        outputs = cfg.get("outputs", {})
        camera = cfg.get("camera", {})
        orb_rgbd = cfg.get("orb_rgbd", {})
        self.orb_mode = str(
            rospy.get_param("~orb_mode", cfg.get("orb_mode", "rgbd"))
        ).strip().lower()
        if self.orb_mode not in ("rgbd-inertial", "rgbd", "mono-inertial", "mono"):
            raise rospy.ROSInitException(
                "adapter.orb_mode must be rgbd-inertial, rgbd, mono-inertial, or mono"
            )
        self.enable_lidar = bool(rospy.get_param("~enable_lidar", True))
        self.enable_imu = bool(rospy.get_param("~enable_imu", True))
        self.enable_camera = bool(rospy.get_param("~enable_camera", True))
        self.enable_fastlivo = bool(rospy.get_param("~enable_fastlivo", True))
        self.enable_orb = bool(rospy.get_param("~enable_orb", True))
        self.enable_lvisam = bool(rospy.get_param("~enable_lvisam", True))
        self.enable_raw = bool(rospy.get_param("~enable_raw", True))
        lidar = cfg.get("lidar", {})
        frames = cfg.get("frames", {})

        self.lidar_frame = str(frames.get("lidar", "velodyne103"))
        self.imu_frame = str(frames.get("imu", "base_link"))
        self.camera_frame = str(frames.get("camera_optical", "camera_color_optical_frame"))
        self.depth_frame = str(frames.get("depth_optical", "camera_depth_optical_frame"))
        self.point_time_scale = float(lidar.get("point_time_scale", 1.0e6))
        self.auto_detect_time_units = bool(lidar.get("auto_detect_time_units", True))
        self.normalize_negative_point_time = bool(lidar.get("normalize_negative_point_time", False))
        self.normalize_raw_negative_point_time = bool(
            rospy.get_param(
                "~normalize_raw_negative_point_time",
                self.normalize_negative_point_time,
            )
        )
        self.require_ring = bool(lidar.get("require_ring", True))
        self.synthesize_organized_fields = bool(lidar.get("synthesize_organized_fields", False))
        self.organized_scan_lines = int(lidar.get("organized_scan_lines", 0))
        self.organized_scan_rate_hz = float(lidar.get("organized_scan_rate_hz", 0.0))
        if self.synthesize_organized_fields and (
                self.organized_scan_lines <= 0 or self.organized_scan_rate_hz <= 0.0):
            raise rospy.ROSInitException(
                "organized LiDAR conversion requires positive organized_scan_lines and organized_scan_rate_hz"
            )
        imu_config = cfg.get("imu", {})
        self.imu_orientation_mode = str(imu_config.get("orientation_mode", "preserve")).lower()
        if self.imu_orientation_mode not in ("preserve", "six_axis"):
            raise rospy.ROSInitException("adapter.imu.orientation_mode must be preserve or six_axis")
        self.imu_attitude_gain = float(imu_config.get("attitude_correction_gain", 0.01))
        self.imu_attitude_q = None
        self.imu_attitude_stamp = None

        self.camera_width = int(camera.get("width", 1280))
        self.camera_height = int(camera.get("height", 720))
        legacy_restamp = bool(camera.get("restamp", False))
        self.camera_timestamp_mode = str(
            camera.get("timestamp_mode", "callback" if legacy_restamp else "preserve")
        ).strip().lower()
        if self.camera_timestamp_mode not in ("preserve", "rebase", "callback"):
            raise rospy.ROSInitException(
                "camera.timestamp_mode must be preserve, rebase, or callback"
            )
        self.camera_time_offset = None
        self.camera_k = self._flatten(camera.get("K", []), 9, "camera.K")
        self.camera_d = [float(v) for v in camera.get("D", [])]
        self.camera_model = str(camera.get("distortion_model", "plumb_bob"))
        self.fast_camera_max_rate = float(camera.get("fast_max_rate_hz", 0.0))
        self.last_fast_camera_stamp = None
        self.orb_rgbd_width = int(orb_rgbd.get("width", 0))
        self.orb_rgbd_height = int(orb_rgbd.get("height", 0))
        self.orb_rgbd_max_rate = float(orb_rgbd.get("max_rate_hz", 0.0))
        self.orb_intensity_target_mean = float(
            orb_rgbd.get("intensity_target_mean", 0.0)
        )
        self.orb_intensity_target_std = float(
            orb_rgbd.get("intensity_target_std", 0.0)
        )
        self.orb_max_saturated_fraction = max(
            0.0, float(orb_rgbd.get("max_saturated_fraction", 0.0))
        )
        self.orb_normalize_intensity = (
            self.orb_intensity_target_mean > 0.0
            and self.orb_intensity_target_std > 0.0
        )
        self.orb_clahe_clip_limit = max(
            0.0, float(orb_rgbd.get("clahe_clip_limit", 0.0))
        )
        self.orb_clahe = (
            cv2.createCLAHE(clipLimit=self.orb_clahe_clip_limit,
                            tileGridSize=(8, 8))
            if self.orb_clahe_clip_limit > 0.0 else None
        )
        self.orb_project_lidar_depth = bool(
            orb_rgbd.get("project_lidar_depth", False)
        ) and self.orb_mode in ("rgbd", "rgbd-inertial")
        self.orb_lidar_to_camera = np.asarray(
            orb_rgbd.get("lidar_to_camera", np.eye(4)), dtype=float
        ).reshape(-1)
        if self.orb_project_lidar_depth:
            if self.orb_lidar_to_camera.size != 16 or not np.all(
                    np.isfinite(self.orb_lidar_to_camera)):
                raise rospy.ROSInitException(
                    "adapter.orb_rgbd.lidar_to_camera must contain 16 finite values"
                )
            self.orb_lidar_to_camera = self.orb_lidar_to_camera.reshape(4, 4)
        self.orb_depth_min_m = float(orb_rgbd.get("depth_min_m", 1.0))
        self.orb_depth_max_m = float(orb_rgbd.get("depth_max_m", 80.0))
        self.orb_depth_splat_px = max(0, int(orb_rgbd.get("depth_splat_px", 1)))
        self.orb_depth_time_slice_sec = max(
            0.0, float(orb_rgbd.get("depth_time_slice_sec", 0.0))
        )
        self.orb_depth_merge_window_sec = max(
            0.0, float(orb_rgbd.get("depth_merge_window_sec", 0.0))
        )
        self.orb_depth_pairing_wait_sec = max(
            self.orb_depth_merge_window_sec,
            float(orb_rgbd.get(
                "depth_pairing_wait_sec",
                self.orb_depth_merge_window_sec,
            )),
        )
        self.orb_depth_sweep_count = max(
            1, int(orb_rgbd.get("depth_sweep_count", 1))
        )
        self.orb_depth_deskew_pose_topic = str(
            orb_rgbd.get("depth_deskew_pose_topic", "")
        ).strip()
        self.orb_depth_deskew_bin_sec = max(
            1.0e-4, float(orb_rgbd.get("depth_deskew_bin_sec", 0.005))
        )
        self.orb_depth_deskew_max_pose_age_sec = max(
            0.0, float(orb_rgbd.get("depth_deskew_max_pose_age_sec", 0.3))
        )
        self.orb_depth_deskew_max_speed_mps = max(
            0.0, float(orb_rgbd.get("depth_deskew_max_speed_mps", 60.0))
        )
        self.orb_depth_deskew_max_angular_speed_rps = max(
            0.0, float(
                orb_rgbd.get("depth_deskew_max_angular_speed_rps", 3.0)
            )
        )
        self.orb_depth_lock = threading.Lock()
        self.latest_lidar_depth: Optional[np.ndarray] = None
        self.latest_lidar_depth_stamp = rospy.Time(0)
        self.orb_depth_history = collections.deque(maxlen=32)
        self.orb_sweep_history = collections.deque(maxlen=32)
        self.orb_pending_rgb = collections.deque()
        self.orb_motion_lock = threading.Lock()
        self.orb_previous_pose = None
        self.orb_latest_motion = None
        self.last_orb_camera_stamp: Optional[float] = None
        self.last_orb_depth_stamp: Optional[float] = None
        self.bridge = CvBridge()
        self.latest_depth_size: Optional[Tuple[int, int]] = None

        self.lidar_pub = rospy.Publisher(str(outputs.get("lidar", "/livox/lidar")), PointCloud2, queue_size=20)
        self.imu_pub = rospy.Publisher(str(outputs.get("imu", "/livox/imu")), Imu, queue_size=200)
        self.camera_pub = rospy.Publisher(str(outputs.get("camera", "/camera/right/image_raw")), Image, queue_size=20)
        self.orb_camera_pub = rospy.Publisher(str(outputs.get("orb_camera", "/camera/rgb/image_raw")), Image, queue_size=20)
        self.orb_depth_pub = rospy.Publisher(str(outputs.get("orb_depth", "/camera/depth_registered/image_raw")), Image, queue_size=20)
        self.camera_info_pub = rospy.Publisher(str(outputs.get("camera_info", "/camera/right/camera_info")), CameraInfo, queue_size=20)
        self.lvisam_lidar_pub = rospy.Publisher(str(outputs.get("lvisam_lidar", "/lvisam/points_raw")), PointCloud2, queue_size=20)
        self.lvisam_imu_pub = rospy.Publisher(str(outputs.get("lvisam_imu", "/lvisam/imu_raw")), Imu, queue_size=200)
        self.lvisam_camera_pub = rospy.Publisher(str(outputs.get("lvisam_camera", "/lvisam/camera/image_raw")), Image, queue_size=20)
        self.lvisam_camera_info_pub = rospy.Publisher(str(outputs.get("lvisam_camera_info", "/lvisam/camera/camera_info")), CameraInfo, queue_size=20)
        self.raw_lidar_pub = rospy.Publisher(str(outputs.get("raw_lidar", "/benchmark/points_raw")), PointCloud2, queue_size=20)
        self.raw_imu_pub = rospy.Publisher(str(outputs.get("raw_imu", "/benchmark/imu_raw")), Imu, queue_size=200)
        self.raw_camera_pub = rospy.Publisher(str(outputs.get("raw_camera", "/benchmark/camera/image_raw")), Image, queue_size=20)
        self.raw_camera_info_pub = rospy.Publisher(str(outputs.get("raw_camera_info", "/benchmark/camera/camera_info")), CameraInfo, queue_size=20)

        # No adapter-wide lock: each StreamFaultGate below guards its own
        # bookkeeping, so lidar/imu/camera/depth processing runs as four
        # independent pipelines instead of being serialized behind one
        # global critical section (see StreamFaultGate docstring).
        self.gates: Dict[str, StreamFaultGate] = {
            "lidar": StreamFaultGate("lidar", self.publish_lidar),
            "imu": StreamFaultGate("imu", self.publish_imu),
            "camera": StreamFaultGate("camera", self.publish_camera),
            "depth": StreamFaultGate("depth", self.publish_depth),
        }

        if self.enable_lidar:
            rospy.Subscriber(str(topics.get("lidar", "/lidar103/velodyne_points")), PointCloud2,
                             lambda msg: self.route("lidar", msg), queue_size=20)
        if self.enable_imu:
            rospy.Subscriber(str(topics.get("imu", "/mavros/imu/data")), Imu,
                             lambda msg: self.route("imu", msg), queue_size=200)
        source_camera_topic = str(topics.get("camera", "/camera/color/image_raw"))
        source_camera_type = str(cfg.get("source_camera_type", "image")).strip().lower()
        if self.enable_camera and source_camera_type == "compressed_image":
            rospy.Subscriber(source_camera_topic, CompressedImage,
                             self.compressed_camera_cb, queue_size=20)
        elif self.enable_camera and source_camera_type == "image":
            rospy.Subscriber(source_camera_topic, Image,
                             lambda msg: self.route("camera", msg), queue_size=20)
        elif self.enable_camera:
            raise rospy.ROSInitException(
                "adapter.source_camera_type must be image or compressed_image"
            )
        source_depth_topic = str(topics.get("depth", ""))
        if self.enable_camera and self.enable_orb and source_depth_topic:
            rospy.Subscriber(source_depth_topic, Image,
                             lambda msg: self.route("depth", msg), queue_size=20)
        if (self.enable_orb and self.orb_project_lidar_depth
                and self.orb_depth_deskew_pose_topic):
            rospy.Subscriber(
                self.orb_depth_deskew_pose_topic,
                PoseStamped,
                self._update_orb_motion,
                queue_size=20,
            )
        rospy.Timer(rospy.Duration(0.01), self.timer_cb)
        rospy.loginfo("[E2OAdapter] raw topics -> lidar=%s imu=%s camera=%s orb_rgb=%s orb_depth=%s",
                      self.lidar_pub.resolved_name, self.imu_pub.resolved_name,
                      self.camera_pub.resolved_name, self.orb_camera_pub.resolved_name,
                      self.orb_depth_pub.resolved_name)

    def compressed_camera_cb(self, msg: CompressedImage) -> None:
        # Some public bags (UrbanLoco in particular) leave the image header
        # stamp at zero and carry the timestamp only in the rosbag record.
        # Capture simulated bag time immediately on callback entry.  Stamping
        # after JPEG decoding displaced images by tens of milliseconds and
        # violated the camera/IMU synchronization contract.
        callback_stamp = rospy.Time.now()
        try:
            cv_image = self.bridge.compressed_imgmsg_to_cv2(msg, desired_encoding="bgr8")
            image = self.bridge.cv2_to_imgmsg(cv_image, encoding="bgr8")
            image.header = msg.header
            if self.camera_timestamp_mode == "callback":
                image.header.stamp = callback_stamp
        except (CvBridgeError, cv2.error) as exc:
            rospy.logerr_throttle(2.0, "[SensorAdapter] compressed image decode failed: %s", exc)
            return
        self.route("camera", image)

    @staticmethod
    def _flatten(value, expected: int, name: str):
        array = np.asarray(value, dtype=float).reshape(-1)
        if array.size != expected or not np.all(np.isfinite(array)):
            raise rospy.ROSInitException(f"{name} must contain {expected} finite values")
        return array.tolist()

    def route(self, sensor: str, msg) -> None:
        self.gates[sensor].handle(msg)

    def timer_cb(self, _event) -> None:
        now = time.monotonic()
        for gate in self.gates.values():
            gate.refresh_mode(now)
            gate.flush(now)

    @staticmethod
    def _field(msg: PointCloud2, name: str) -> Optional[PointField]:
        return next((field for field in msg.fields if field.name == name), None)

    @staticmethod
    def _strided_field_view(byte_array: np.ndarray, msg: PointCloud2, field: PointField, dtype):
        """Zero-copy (height, width) view of one PointCloud2 field over a uint8 buffer.

        Replaces a per-point struct.unpack/pack Python loop with a single strided
        numpy view so scaling/shifting is one vectorized op instead of O(n) Python
        calls. At bag rate 1 a 16-line scan has tens of thousands of points per
        message; the per-point loop could not keep up with real sensor rate.
        """
        itemsize = np.dtype(dtype).itemsize
        if msg.width <= 0 or msg.height <= 0:
            return None
        needed = field.offset + msg.row_step * (msg.height - 1) + msg.point_step * (msg.width - 1) + itemsize
        if byte_array.size < needed:
            return None
        return np.ndarray(
            shape=(msg.height, msg.width),
            dtype=dtype,
            buffer=byte_array,
            offset=field.offset,
            strides=(msg.row_step, msg.point_step),
        )

    def _scale_point_time(self, msg: PointCloud2) -> PointCloud2:
        if math.isclose(self.point_time_scale, 1.0) and not self.normalize_negative_point_time:
            return msg
        field = self._field(msg, "time")
        if field is None:
            rospy.logwarn_throttle(5.0, "[E2OAdapter] lidar has no per-point 'time' field")
            return msg
        if field.datatype not in (PointField.FLOAT32, PointField.FLOAT64):
            rospy.logwarn_throttle(5.0, "[E2OAdapter] unsupported time datatype=%d", field.datatype)
            return msg
        if not msg.data or msg.point_step <= field.offset:
            return msg

        dtype = np.float32 if field.datatype == PointField.FLOAT32 else np.float64
        src = np.frombuffer(msg.data, dtype=np.uint8)
        src_view = self._strided_field_view(src, msg, field, dtype)
        if src_view is None:
            return msg

        finite = np.isfinite(src_view)
        if self.auto_detect_time_units and finite.any():
            flat = src_view[finite]
            limit = min(flat.size, 4096)
            # Spread the sample across the whole cloud (not just the first
            # scan line) so unit auto-detection sees every ring, not only ring 0.
            sample_idx = np.linspace(0, flat.size - 1, num=limit, dtype=np.int64)
            if np.max(np.abs(flat[sample_idx])) > 1.0e3:
                # Already appears to be microseconds/nanoseconds. Avoid multiplying twice.
                return msg

        out = copy.deepcopy(msg)
        raw = bytearray(out.data)
        dst = np.frombuffer(raw, dtype=np.uint8)
        dst_view = self._strided_field_view(dst, out, field, dtype)
        if self.normalize_negative_point_time:
            finite_dst = np.isfinite(dst_view)
            min_time = float(np.min(dst_view[finite_dst])) if finite_dst.any() else 0.0
            if min_time < -1.0e-6:
                dst_view[finite_dst] -= min_time
                out.header.stamp = out.header.stamp + rospy.Duration.from_sec(min_time)
                rospy.loginfo_once("[E2OAdapter] normalized negative FAST-LIVO2 point times to scan start")
        dst_view *= self.point_time_scale
        out.data = bytes(raw)
        return out

    def _augment_organized_lidar_fields(self, msg: PointCloud2) -> PointCloud2:
        """Add ring/time fields from an explicitly configured organized scan.

        UrbanLoco's RS-LiDAR-32 messages are 32-row organized clouds but carry
        only x/y/z/intensity. Rows are laser channels and columns are acquisition
        order across one documented 10 Hz revolution. The conversion is enabled
        only for that dataset; native fields always take precedence.
        """
        if not self.synthesize_organized_fields:
            return msg
        if self._field(msg, "ring") is not None and self._field(msg, "time") is not None:
            return msg
        required = [self._field(msg, name) for name in ("x", "y", "z", "intensity")]
        if any(field is None or field.datatype != PointField.FLOAT32 for field in required):
            rospy.logerr_throttle(
                5.0, "[E2OAdapter] organized lidar conversion requires float32 x/y/z/intensity"
            )
            return msg
        if msg.is_bigendian or msg.height != self.organized_scan_lines or msg.width <= 1:
            rospy.logerr_throttle(
                5.0,
                "[E2OAdapter] organized lidar shape/endian mismatch: got %dx%d bigendian=%s expected lines=%d",
                msg.height, msg.width, msg.is_bigendian, self.organized_scan_lines,
            )
            return msg

        out = PointCloud2()
        out.header = copy.deepcopy(msg.header)
        out.height = msg.height
        out.width = msg.width
        out.fields = [
            PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name="intensity", offset=12, datatype=PointField.FLOAT32, count=1),
            PointField(name="time", offset=16, datatype=PointField.FLOAT32, count=1),
            PointField(name="ring", offset=20, datatype=PointField.UINT16, count=1),
        ]
        out.is_bigendian = False
        out.point_step = 24
        out.row_step = out.point_step * out.width
        out.is_dense = msg.is_dense
        raw = bytearray(out.row_step * out.height)
        source = np.frombuffer(msg.data, dtype=np.uint8)
        destination = np.frombuffer(raw, dtype=np.uint8)
        for source_field, destination_field in zip(required, out.fields[:4]):
            source_view = self._strided_field_view(source, msg, source_field, np.float32)
            destination_view = self._strided_field_view(
                destination, out, destination_field, np.float32
            )
            if source_view is None or destination_view is None:
                rospy.logerr_throttle(5.0, "[E2OAdapter] malformed organized lidar buffer")
                return msg
            destination_view[:] = source_view
        time_view = self._strided_field_view(destination, out, out.fields[4], np.float32)
        ring_view = self._strided_field_view(destination, out, out.fields[5], np.uint16)
        time_view[:] = (
            np.arange(out.width, dtype=np.float32)[None, :]
            / np.float32(out.width - 1)
            / np.float32(self.organized_scan_rate_hz)
        )
        ring_view[:] = np.arange(out.height, dtype=np.uint16)[:, None]
        out.data = bytes(raw)
        rospy.loginfo_once(
            "[E2OAdapter] derived ring/time from %dx%d organized scan at %.3f Hz",
            out.height, out.width, self.organized_scan_rate_hz,
        )
        return out

    def _normalize_lvisam_point_time(self, msg: PointCloud2) -> PointCloud2:
        field = self._field(msg, "time")
        if field is None or field.datatype not in (PointField.FLOAT32, PointField.FLOAT64):
            return msg
        if not msg.data or msg.point_step <= field.offset:
            return msg

        dtype = np.float32 if field.datatype == PointField.FLOAT32 else np.float64
        src = np.frombuffer(msg.data, dtype=np.uint8)
        src_view = self._strided_field_view(src, msg, field, dtype)
        if src_view is None:
            return msg

        finite = np.isfinite(src_view)
        if not finite.any():
            return msg
        min_time = float(np.min(src_view[finite]))
        if min_time >= -1.0e-6:
            return msg

        out = copy.deepcopy(msg)
        raw = bytearray(out.data)
        dst = np.frombuffer(raw, dtype=np.uint8)
        dst_view = self._strided_field_view(dst, out, field, dtype)
        finite_dst = np.isfinite(dst_view)
        dst_view[finite_dst] -= min_time
        out.data = bytes(raw)
        out.header.stamp = out.header.stamp + rospy.Duration.from_sec(min_time)
        rospy.loginfo_once("[E2OAdapter] normalized negative point times to scan start")
        return out

    def _remove_nonfinite_lvisam_points(self, msg: PointCloud2) -> PointCloud2:
        """Compact an explicitly non-dense cloud for LVI-SAM image projection."""
        if msg.is_dense:
            return msg
        xyz_fields = [self._field(msg, name) for name in ("x", "y", "z")]
        if any(field is None or field.datatype != PointField.FLOAT32 for field in xyz_fields):
            rospy.logerr_throttle(5.0, "[E2OAdapter] cannot filter non-dense lidar without float32 x/y/z")
            return msg
        source = np.frombuffer(msg.data, dtype=np.uint8)
        xyz = [self._strided_field_view(source, msg, field, np.float32) for field in xyz_fields]
        if any(view is None for view in xyz):
            rospy.logerr_throttle(5.0, "[E2OAdapter] malformed non-dense lidar buffer")
            return msg
        finite = np.isfinite(xyz[0]) & np.isfinite(xyz[1]) & np.isfinite(xyz[2])
        if finite.all():
            out = copy.deepcopy(msg)
            out.is_dense = True
            return out
        point_bytes = np.ndarray(
            shape=(msg.height, msg.width, msg.point_step),
            dtype=np.uint8,
            buffer=source,
            strides=(msg.row_step, msg.point_step, 1),
        )
        compact = point_bytes[finite]
        out = copy.deepcopy(msg)
        out.height = 1
        out.width = int(compact.shape[0])
        out.row_step = out.width * out.point_step
        out.data = compact.tobytes()
        out.is_dense = True
        rospy.loginfo_once(
            "[E2OAdapter] removed %d non-finite lidar points for LVI-SAM",
            int(finite.size - finite.sum()),
        )
        return out

    def publish_lidar(self, msg: PointCloud2) -> None:
        msg = self._augment_organized_lidar_fields(msg)
        if self.enable_orb and self.orb_project_lidar_depth:
            self._update_orb_lidar_depth(msg)
        if self.enable_lvisam:
            self.publish_lvisam_lidar(msg)
        if self.enable_raw:
            # Some estimators (FAST-LIO2) require offsets from scan start,
            # while RTAB-Map natively supports signed offsets around the
            # message stamp. Keep this branch selectable instead of silently
            # changing the timestamp convention for every raw-cloud consumer.
            raw = (self._normalize_lvisam_point_time(msg)
                   if self.normalize_raw_negative_point_time else copy.deepcopy(msg))
            raw.header.frame_id = self.lidar_frame
            self.raw_lidar_pub.publish(raw)
        if self.enable_fastlivo:
            out = self._scale_point_time(msg)
            out.header.frame_id = self.lidar_frame
            if self.require_ring and self._field(out, "ring") is None:
                rospy.logerr_throttle(5.0, "[E2OAdapter] lidar ring field missing; FAST-LIVO2 scan-line processing may be invalid")
            self.lidar_pub.publish(out)

    @staticmethod
    def _quaternion_matrix_xyzw(values) -> np.ndarray:
        x, y, z, w = np.asarray(values, dtype=float)
        norm = float(np.linalg.norm([x, y, z, w]))
        if not math.isfinite(norm) or norm <= 1.0e-12:
            raise ValueError("invalid quaternion")
        x, y, z, w = x / norm, y / norm, z / norm, w / norm
        return np.asarray([
            [1.0 - 2.0*(y*y + z*z), 2.0*(x*y - z*w), 2.0*(x*z + y*w)],
            [2.0*(x*y + z*w), 1.0 - 2.0*(x*x + z*z), 2.0*(y*z - x*w)],
            [2.0*(x*z - y*w), 2.0*(y*z + x*w), 1.0 - 2.0*(x*x + y*y)],
        ], dtype=float)

    def _update_orb_motion(self, msg: PoseStamped) -> None:
        """Estimate a causal camera-frame twist from consecutive ORB poses."""
        stamp = msg.header.stamp.to_sec()
        position = np.asarray([
            msg.pose.position.x,
            msg.pose.position.y,
            msg.pose.position.z,
        ], dtype=float)
        quaternion = np.asarray([
            msg.pose.orientation.x,
            msg.pose.orientation.y,
            msg.pose.orientation.z,
            msg.pose.orientation.w,
        ], dtype=float)
        if not math.isfinite(stamp) or not np.all(np.isfinite(position)):
            return
        try:
            rotation = self._quaternion_matrix_xyzw(quaternion)
        except ValueError:
            return
        with self.orb_motion_lock:
            previous = self.orb_previous_pose
            self.orb_previous_pose = (stamp, position, rotation)
            if previous is None:
                return
            previous_stamp, previous_position, previous_rotation = previous
            dt = stamp - previous_stamp
            if dt <= 1.0e-3 or dt > 0.5:
                return
            linear_world = (position - previous_position) / dt
            linear_camera = rotation.T @ linear_world
            camera_from_previous = rotation.T @ previous_rotation
            angular_camera = cv2.Rodrigues(camera_from_previous)[0].reshape(3) / dt
            speed = float(np.linalg.norm(linear_camera))
            angular_speed = float(np.linalg.norm(angular_camera))
            if (
                not np.all(np.isfinite(linear_camera))
                or not np.all(np.isfinite(angular_camera))
                or speed > self.orb_depth_deskew_max_speed_mps
                or angular_speed > self.orb_depth_deskew_max_angular_speed_rps
            ):
                return
            self.orb_latest_motion = (
                stamp,
                linear_camera.astype(np.float64),
                angular_camera.astype(np.float64),
            )

    def _deskew_orb_camera_points(
            self, xyz_camera: np.ndarray, acquisition_stamps: np.ndarray,
            camera_stamp: float) -> np.ndarray:
        """Transform lidar returns to one camera time using prior ORB motion."""
        with self.orb_motion_lock:
            motion = self.orb_latest_motion
        if motion is None:
            return xyz_camera
        motion_stamp, linear_camera, angular_camera = motion
        pose_age = camera_stamp - motion_stamp
        if (
            pose_age < 0.0
            or pose_age > self.orb_depth_deskew_max_pose_age_sec
        ):
            return xyz_camera
        deltas = camera_stamp - acquisition_stamps
        bins = np.rint(deltas / self.orb_depth_deskew_bin_sec).astype(np.int32)
        output = xyz_camera.copy()
        for bin_id in np.unique(bins):
            selected = bins == bin_id
            delta = float(bin_id) * self.orb_depth_deskew_bin_sec
            rotation = cv2.Rodrigues(angular_camera * delta)[0]
            output[selected] = (
                output[selected] @ rotation.T
                - linear_camera.reshape(1, 3) * delta
            )
        return output

    def _project_orb_camera_points(
            self, xyz_camera: np.ndarray, width: int,
            height: int) -> Tuple[np.ndarray, np.ndarray]:
        depth = xyz_camera[:, 2]
        valid = (
            np.isfinite(depth)
            & (depth >= self.orb_depth_min_m)
            & (depth <= self.orb_depth_max_m)
        )
        xyz_camera = xyz_camera[valid]
        depth = depth[valid]
        if not len(depth):
            return np.empty((0, 2), dtype=np.int32), np.empty(0, dtype=np.float32)
        scale_x = width / float(self.camera_width)
        scale_y = height / float(self.camera_height)
        camera_matrix = np.asarray(
            self.camera_k, dtype=np.float64
        ).reshape(3, 3).copy()
        camera_matrix[0, :] *= scale_x
        camera_matrix[1, :] *= scale_y
        pixels, _ = cv2.projectPoints(
            xyz_camera.reshape(-1, 1, 3).astype(np.float64),
            np.zeros(3, dtype=np.float64),
            np.zeros(3, dtype=np.float64),
            camera_matrix,
            np.asarray(self.camera_d, dtype=np.float64),
        )
        pixels = np.rint(pixels.reshape(-1, 2)).astype(np.int32)
        inside = (
            (pixels[:, 0] >= 0) & (pixels[:, 0] < width)
            & (pixels[:, 1] >= 0) & (pixels[:, 1] < height)
        )
        return pixels[inside], depth[inside].astype(np.float32)

    def _update_orb_lidar_depth(self, msg: PointCloud2) -> None:
        """Project calibrated LiDAR returns into ORB-SLAM3's RGB-D image."""
        if msg.is_bigendian or not msg.data:
            rospy.logerr_throttle(
                5.0, "[E2OAdapter] LiDAR depth projection requires little-endian points"
            )
            return
        fields = [self._field(msg, name) for name in ("x", "y", "z")]
        if any(field is None or field.datatype != PointField.FLOAT32 for field in fields):
            rospy.logerr_throttle(
                5.0, "[E2OAdapter] LiDAR depth projection requires float32 x/y/z"
            )
            return
        source = np.frombuffer(msg.data, dtype=np.uint8)
        xyz_views = [
            self._strided_field_view(source, msg, field, np.float32)
            for field in fields
        ]
        if any(view is None for view in xyz_views):
            rospy.logerr_throttle(5.0, "[E2OAdapter] malformed LiDAR cloud for depth projection")
            return
        xyz_lidar = np.column_stack([view.reshape(-1) for view in xyz_views])
        time_field = self._field(msg, "time")
        point_offsets = np.zeros(xyz_lidar.shape[0], dtype=np.float64)
        if time_field is not None and time_field.datatype in (
                PointField.FLOAT32, PointField.FLOAT64):
            time_dtype = (
                np.float32 if time_field.datatype == PointField.FLOAT32 else np.float64
            )
            time_view = self._strided_field_view(source, msg, time_field, time_dtype)
            if time_view is not None:
                point_offsets = time_view.reshape(-1).astype(np.float64)
        finite = np.all(np.isfinite(xyz_lidar), axis=1)
        finite &= np.isfinite(point_offsets)
        if not finite.any():
            return
        rotation = self.orb_lidar_to_camera[:3, :3]
        translation = self.orb_lidar_to_camera[:3, 3]
        xyz_camera = xyz_lidar[finite] @ rotation.T + translation
        point_offsets = point_offsets[finite]
        depth = xyz_camera[:, 2]
        valid = (
            np.isfinite(depth)
            & (depth >= self.orb_depth_min_m)
            & (depth <= self.orb_depth_max_m)
        )
        if not valid.any():
            return
        xyz_camera = xyz_camera[valid]
        depth = depth[valid]
        point_offsets = point_offsets[valid]

        width = self.orb_rgbd_width or self.camera_width
        height = self.orb_rgbd_height or self.camera_height
        scale_x = width / float(self.camera_width)
        scale_y = height / float(self.camera_height)
        camera_matrix = np.asarray(self.camera_k, dtype=np.float64).reshape(3, 3).copy()
        camera_matrix[0, :] *= scale_x
        camera_matrix[1, :] *= scale_y
        pixels, _ = cv2.projectPoints(
            xyz_camera.reshape(-1, 1, 3).astype(np.float64),
            np.zeros(3, dtype=np.float64),
            np.zeros(3, dtype=np.float64),
            camera_matrix,
            np.asarray(self.camera_d, dtype=np.float64),
        )
        pixels = np.rint(pixels.reshape(-1, 2)).astype(np.int32)
        inside = (
            (pixels[:, 0] >= 0) & (pixels[:, 0] < width)
            & (pixels[:, 1] >= 0) & (pixels[:, 1] < height)
        )
        if not inside.any():
            return
        xyz_camera = xyz_camera[inside]
        pixels = pixels[inside]
        depth = depth[inside].astype(np.float32)
        point_offsets = point_offsets[inside]
        if (
            self.orb_depth_time_slice_sec <= 0.0
            and self.orb_depth_deskew_pose_topic
        ):
            scan_stamp = msg.header.stamp.to_sec()
            # Boreas stamps every LiDAR file at the scan midpoint and stores
            # signed per-return acquisition offsets around that timestamp.
            # The median offset depends on which returns survive the camera
            # frustum/depth filters, so adding it here makes the nominal scan
            # time drift with scene content and can select the wrong sweep for
            # an RGB frame.  Keep the documented midpoint as the pairing time;
            # the individual offsets below are used only for causal deskew.
            sweep_stamp = scan_stamp
            acquisition_stamps = scan_stamp + point_offsets
            with self.orb_depth_lock:
                self.orb_sweep_history.append((
                    sweep_stamp,
                    xyz_camera.copy(),
                    acquisition_stamps.copy(),
                ))
                self.latest_lidar_depth_stamp = rospy.Time.from_sec(sweep_stamp)
            self._flush_orb_rgbd(sweep_stamp)
            rospy.loginfo_once(
                "[E2OAdapter] projecting causal motion-deskewed complete "
                "LiDAR sweeps into %dx%d ORB RGB-D depth",
                width, height,
            )
            return
        if self.orb_depth_time_slice_sec > 0.0 and time_field is not None:
            slice_ids = np.rint(
                point_offsets / self.orb_depth_time_slice_sec
            ).astype(np.int32)
        else:
            slice_ids = np.zeros(len(depth), dtype=np.int32)

        slices = []
        for slice_id in np.unique(slice_ids):
            selected = slice_ids == slice_id
            depth_image = self._make_orb_depth_image(
                pixels[selected], depth[selected], width, height
            )
            if self.orb_depth_time_slice_sec > 0.0:
                slice_stamp = msg.header.stamp.to_sec() + float(
                    np.median(point_offsets[selected])
                )
            else:
                # A complete Boreas sweep is already stamped at its midpoint.
                slice_stamp = msg.header.stamp.to_sec()
            slices.append((slice_stamp, depth_image))
        if not slices:
            return
        with self.orb_depth_lock:
            for slice_stamp, depth_image in slices:
                self.orb_depth_history.append((slice_stamp, depth_image))
            self.latest_lidar_depth = slices[-1][1]
            self.latest_lidar_depth_stamp = rospy.Time.from_sec(slices[-1][0])
        self._flush_orb_rgbd(slices[-1][0])
        rospy.loginfo_once(
            "[E2OAdapter] projecting calibrated LiDAR into %dx%d ORB RGB-D "
            "depth with %.3f s acquisition-time slices (0 = complete "
            "camera-visible sweep at its median acquisition time)",
            width, height, self.orb_depth_time_slice_sec,
        )

    def _make_orb_depth_image(self, pixels, depth, width, height):
        depth_image = np.full((height, width), np.inf, dtype=np.float32)
        radius = self.orb_depth_splat_px
        # Local Voronoi rasterization reproduces nearest-measured-pixel
        # splatting without running a full-frame distance transform for every
        # acquisition-time slice. Resolve equal-distance collisions by camera
        # depth, but never let a nearer foreground return overwrite a pixel
        # whose closest measured support is spatially nearer.
        best_distance = np.full(width * height, np.iinfo(np.uint16).max,
                                dtype=np.uint16)
        flat_depth = depth_image.reshape(-1)
        offsets_by_distance = collections.defaultdict(list)
        for dv in range(-radius, radius + 1):
            for du in range(-radius, radius + 1):
                offsets_by_distance[du * du + dv * dv].append((du, dv))
        for distance_squared in sorted(offsets_by_distance):
            targets = []
            values = []
            for du, dv in offsets_by_distance[distance_squared]:
                shifted_x = pixels[:, 0] + du
                shifted_y = pixels[:, 1] + dv
                valid = (
                    (shifted_x >= 0) & (shifted_x < width)
                    & (shifted_y >= 0) & (shifted_y < height)
                )
                if valid.any():
                    targets.append(shifted_y[valid] * width + shifted_x[valid])
                    values.append(depth[valid])
            if not targets:
                continue
            targets = np.concatenate(targets)
            values = np.concatenate(values)
            unique_targets = np.unique(targets)
            nearer = unique_targets[
                best_distance[unique_targets] > distance_squared
            ]
            best_distance[nearer] = distance_squared
            flat_depth[nearer] = np.inf
            supported = best_distance[targets] == distance_squared
            np.minimum.at(flat_depth, targets[supported], values[supported])
        depth_image[~np.isfinite(depth_image)] = 0.0
        return depth_image

    def publish_lvisam_lidar(self, msg: PointCloud2) -> None:
        out = self._remove_nonfinite_lvisam_points(msg)
        out = self._normalize_lvisam_point_time(out)
        out.header.frame_id = self.lidar_frame
        if self.require_ring and self._field(out, "ring") is None:
            rospy.logerr_throttle(5.0, "[E2OAdapter] lidar ring field missing; LVI-SAM N_SCAN projection may be invalid")
        if self._field(out, "time") is None:
            rospy.logwarn_throttle(5.0, "[E2OAdapter] lidar has no per-point 'time' field for LVI-SAM")
        self.lvisam_lidar_pub.publish(out)

    def publish_imu(self, msg: Imu) -> None:
        out = copy.deepcopy(msg)
        out.header.frame_id = self.imu_frame
        if self.imu_orientation_mode == "six_axis":
            self._synthesize_six_axis_orientation(out)
        if self.enable_fastlivo or self.enable_orb:
            self.imu_pub.publish(out)
        if self.enable_lvisam:
            self.lvisam_imu_pub.publish(out)
        if self.enable_raw:
            self.raw_imu_pub.publish(out)

    @staticmethod
    def _quat_multiply(left, right):
        lx, ly, lz, lw = left; rx, ry, rz, rw = right
        return np.asarray([
            lw*rx + lx*rw + ly*rz - lz*ry,
            lw*ry - lx*rz + ly*rw + lz*rx,
            lw*rz + lx*ry - ly*rx + lz*rw,
            lw*rw - lx*rx - ly*ry - lz*rz,
        ], dtype=float)

    @staticmethod
    def _quat_rotate(q, vector):
        x, y, z, w = q
        rotation = np.array([
            [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
            [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
            [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)],
        ])
        return rotation @ vector

    @staticmethod
    def _quat_between(source, target):
        source = source / np.linalg.norm(source); target = target / np.linalg.norm(target)
        dot = float(np.dot(source, target))
        if dot < -0.999999:
            axis = np.cross(source, [1.0, 0.0, 0.0])
            if np.linalg.norm(axis) < 1e-6:
                axis = np.cross(source, [0.0, 1.0, 0.0])
            axis /= np.linalg.norm(axis)
            return np.asarray([*axis, 0.0])
        cross = np.cross(source, target)
        q = np.asarray([*cross, 1.0 + dot])
        return q / np.linalg.norm(q)

    def _synthesize_six_axis_orientation(self, msg: Imu) -> None:
        """Complementary gyro/gravity attitude; no GNSS or reference pose is used."""
        acceleration = np.asarray([msg.linear_acceleration.x, msg.linear_acceleration.y,
                                   msg.linear_acceleration.z], dtype=float)
        norm = float(np.linalg.norm(acceleration))
        stamp = msg.header.stamp.to_sec()
        if not np.all(np.isfinite(acceleration)) or norm < 1e-6:
            return
        if self.imu_attitude_q is None:
            self.imu_attitude_q = self._quat_between(acceleration / norm, np.array([0.0, 0.0, 1.0]))
        elif self.imu_attitude_stamp is not None:
            dt = stamp - self.imu_attitude_stamp
            angular = np.asarray([msg.angular_velocity.x, msg.angular_velocity.y,
                                  msg.angular_velocity.z], dtype=float)
            angle = float(np.linalg.norm(angular) * dt)
            if 0.0 < dt < 0.1 and np.all(np.isfinite(angular)) and angle > 1e-12:
                axis = angular / np.linalg.norm(angular)
                delta = np.asarray([*(axis * math.sin(angle/2.0)), math.cos(angle/2.0)])
                self.imu_attitude_q = self._quat_multiply(self.imu_attitude_q, delta)
            world_acceleration = self._quat_rotate(self.imu_attitude_q, acceleration / norm)
            correction = self._quat_between(world_acceleration, np.array([0.0, 0.0, 1.0]))
            correction[:3] *= self.imu_attitude_gain
            correction[3] = 1.0 - self.imu_attitude_gain + self.imu_attitude_gain * correction[3]
            correction /= np.linalg.norm(correction)
            self.imu_attitude_q = self._quat_multiply(correction, self.imu_attitude_q)
            self.imu_attitude_q /= np.linalg.norm(self.imu_attitude_q)
        self.imu_attitude_stamp = stamp
        msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w = self.imu_attitude_q
        msg.orientation_covariance = [0.0] * 9
        msg.orientation_covariance[0] = msg.orientation_covariance[4] = 0.05
        msg.orientation_covariance[8] = 1.0  # yaw is gyro-integrated and has no absolute reference

    def _normalize_image_time(self, msg: Image) -> Image:
        out = copy.deepcopy(msg)
        if self.camera_timestamp_mode == "callback":
            # Compressed inputs are stamped at callback entry, before their
            # potentially expensive decode. Raw zero-stamped inputs arrive
            # here directly and are stamped now.
            if out.header.stamp == rospy.Time(0):
                out.header.stamp = rospy.Time.now()
        elif self.camera_timestamp_mode == "rebase":
            if self.camera_time_offset is None:
                self.camera_time_offset = rospy.Time.now() - out.header.stamp
                rospy.loginfo("[E2OAdapter] image clock rebased by %.6f s",
                              self.camera_time_offset.to_sec())
            out.header.stamp = out.header.stamp + self.camera_time_offset
        return out

    @staticmethod
    def _admit_at_rate(last_stamp: Optional[float], stamp: float, max_rate_hz: float) -> bool:
        if max_rate_hz <= 0.0 or last_stamp is None:
            return True
        if stamp <= last_stamp:
            return False
        return stamp - last_stamp >= 1.0 / max_rate_hz - 1.0e-4

    def publish_depth(self, msg: Image) -> None:
        out = self._normalize_image_time(msg)
        out.header.frame_id = self.depth_frame
        width = int(out.width or self.orb_rgbd_width)
        height = int(out.height or self.orb_rgbd_height)
        if width > 0 and height > 0:
            self.latest_depth_size = (width, height)
        stamp = out.header.stamp.to_sec()
        if self._admit_at_rate(self.last_orb_depth_stamp, stamp, self.orb_rgbd_max_rate):
            self.last_orb_depth_stamp = stamp
            self.orb_depth_pub.publish(out)

    def publish_camera(self, msg: Image) -> None:
        out = self._normalize_image_time(msg)
        out.header.frame_id = self.camera_frame
        orb_rgb = None
        if self.enable_orb and self.orb_mode in ("mono", "mono-inertial"):
            target = None
            if self.orb_rgbd_width > 0 and self.orb_rgbd_height > 0:
                target = (self.orb_rgbd_width, self.orb_rgbd_height)
            orb_rgb = self.resize_orb_image(out, target)
        elif self.enable_orb:
            orb_rgb = self.make_orb_rgb(out)
        if orb_rgb is not None:
            orb_stamp = orb_rgb.header.stamp.to_sec()
            if self._admit_at_rate(self.last_orb_camera_stamp, orb_stamp, self.orb_rgbd_max_rate):
                self.last_orb_camera_stamp = orb_stamp
                if self.orb_project_lidar_depth:
                    with self.orb_depth_lock:
                        self.orb_pending_rgb.append(orb_rgb)
                    self._flush_orb_rgbd()
                else:
                    self.orb_camera_pub.publish(orb_rgb)
        info = None
        if self.enable_lvisam:
            self.lvisam_camera_pub.publish(out)
            info = self.make_camera_info(out)
            self.lvisam_camera_info_pub.publish(info)
        if self.enable_raw:
            info = info or self.make_camera_info(out)
            self.raw_camera_pub.publish(out)
            self.raw_camera_info_pub.publish(info)
        stamp = out.header.stamp.to_sec()
        if not self.enable_fastlivo:
            return
        if self.fast_camera_max_rate <= 0.0:
            publish_fast = True
        elif self.last_fast_camera_stamp is None:
            publish_fast = True
        elif stamp <= self.last_fast_camera_stamp:
            publish_fast = False
        elif stamp - self.last_fast_camera_stamp >= 1.0 / self.fast_camera_max_rate - 1.0e-4:
            publish_fast = True
        else:
            publish_fast = False
        if not publish_fast:
            return
        self.last_fast_camera_stamp = stamp
        self.camera_pub.publish(out)
        self.camera_info_pub.publish(self.make_camera_info(out))

    def make_orb_rgb(self, image: Image) -> Optional[Image]:
        target_size = (
            (self.orb_rgbd_width, self.orb_rgbd_height)
            if self.orb_project_lidar_depth
            and self.orb_rgbd_width > 0 and self.orb_rgbd_height > 0
            else self.latest_depth_size
        )
        if target_size is None:
            if self.orb_rgbd_width > 0 and self.orb_rgbd_height > 0:
                target_size = (self.orb_rgbd_width, self.orb_rgbd_height)
            else:
                rospy.logwarn_throttle(5.0, "[E2OAdapter] waiting for depth image before publishing ORB RGB-D color")
                return None
        return self.resize_orb_image(image, target_size)

    def _flush_orb_rgbd(self, latest_lidar_stamp: Optional[float] = None) -> None:
        """Publish RGB-D after the complete camera-facing lidar sweep arrives."""
        ready = []
        with self.orb_depth_lock:
            use_raw_sweeps = bool(self.orb_sweep_history)
            history = (
                self.orb_sweep_history if use_raw_sweeps
                else self.orb_depth_history
            )
            if not history:
                return
            if latest_lidar_stamp is None:
                latest_lidar_stamp = history[-1][0]
            while self.orb_pending_rgb:
                rgb = self.orb_pending_rgb[0]
                camera_stamp = rgb.header.stamp.to_sec()
                # Camera-visible returns span several time slices and may cross
                # a lidar scan-file boundary. Wait for the forward side of the
                # merge window instead of publishing a partial frustum.
                if camera_stamp + self.orb_depth_pairing_wait_sec > latest_lidar_stamp:
                    break
                self.orb_pending_rgb.popleft()
                nearest_items = sorted(
                    history, key=lambda item: abs(item[0] - camera_stamp)
                )[:self.orb_depth_sweep_count]
                nearest = nearest_items[0]
                if use_raw_sweeps:
                    depth_stamp = nearest[0]
                    xyz_camera = np.concatenate(
                        [item[1] for item in nearest_items], axis=0
                    )
                    acquisition_stamps = np.concatenate(
                        [item[2] for item in nearest_items], axis=0
                    )
                    ready.append((
                        rgb, None, depth_stamp,
                        xyz_camera.copy(), acquisition_stamps.copy(),
                    ))
                else:
                    depth_stamp, depth = nearest
                    contributors = [
                        item_depth
                        for item_stamp, item_depth in self.orb_depth_history
                        if abs(item_stamp - camera_stamp)
                        <= self.orb_depth_merge_window_sec
                    ]
                    if contributors:
                        depth = np.minimum.reduce(contributors)
                    ready.append((rgb, depth.copy(), depth_stamp, None, None))
        for rgb, depth, source_stamp, xyz_camera, acquisition_stamps in ready:
            if depth is None:
                camera_stamp = rgb.header.stamp.to_sec()
                xyz_camera = self._deskew_orb_camera_points(
                    xyz_camera, acquisition_stamps, camera_stamp
                )
                pixels, depth_values = self._project_orb_camera_points(
                    xyz_camera, rgb.width, rgb.height
                )
                if not len(depth_values):
                    continue
                depth = self._make_orb_depth_image(
                    pixels, depth_values, rgb.width, rgb.height
                )
            depth_msg = self.bridge.cv2_to_imgmsg(depth, encoding="32FC1")
            depth_msg.header = copy.deepcopy(rgb.header)
            depth_msg.header.frame_id = self.camera_frame
            self.orb_depth_pub.publish(depth_msg)
            self.orb_camera_pub.publish(rgb)
            self.camera_info_pub.publish(self.make_camera_info(rgb))
            rospy.logdebug(
                "[E2OAdapter] ORB RGB-D LiDAR/camera dt=%.6f s",
                source_stamp - rgb.header.stamp.to_sec(),
            )

    def resize_orb_image(self, image: Image,
                         target_size: Optional[Tuple[int, int]]) -> Optional[Image]:
        """Resize only the ORB feed, preserving full-resolution evidence streams."""
        if target_size is None:
            return image
        target_width, target_height = target_size
        if (int(image.width) == target_width and int(image.height) == target_height
                and self.orb_clahe is None
                and not self.orb_normalize_intensity):
            return image
        try:
            cv_image = self.bridge.imgmsg_to_cv2(image, desired_encoding="passthrough")
            if int(image.width) == target_width and int(image.height) == target_height:
                resized = cv_image
            else:
                resized = cv2.resize(
                    cv_image, (target_width, target_height),
                    interpolation=cv2.INTER_LINEAR
                )
            if self.orb_clahe is not None or self.orb_normalize_intensity:
                if resized.ndim == 3:
                    resized = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            if self.orb_max_saturated_fraction > 0.0:
                saturation_fraction = float(
                    np.count_nonzero(resized >= 251)
                ) / float(resized.size)
                if saturation_fraction > self.orb_max_saturated_fraction:
                    rospy.logwarn_throttle(
                        1.0,
                        "[E2OAdapter] skipping ORB image with %.1f%% saturated pixels",
                        100.0 * saturation_fraction,
                    )
                    return None
            if self.orb_normalize_intensity:
                mean, standard_deviation = cv2.meanStdDev(resized)
                scale = self.orb_intensity_target_std / max(
                    float(standard_deviation[0, 0]), 1.0
                )
                # Bound the linear exposure correction so it cannot amplify
                # sensor noise or flatten normal frames. Unlike local CLAHE,
                # this preserves the spatial intensity ordering used by ORB.
                scale = min(2.0, max(0.5, scale))
                offset = self.orb_intensity_target_mean - scale * float(mean[0, 0])
                resized = np.clip(
                    resized.astype(np.float32) * scale + offset, 0.0, 255.0
                ).astype(np.uint8)
            if self.orb_clahe is not None:
                resized = self.orb_clahe.apply(resized)
            if self.orb_clahe is not None or self.orb_normalize_intensity:
                out = self.bridge.cv2_to_imgmsg(resized, encoding="mono8")
            else:
                out = self.bridge.cv2_to_imgmsg(resized, encoding=image.encoding)
        except (CvBridgeError, cv2.error) as exc:
            rospy.logerr_throttle(2.0, "[E2OAdapter] failed to resize ORB RGB image: %s", exc)
            return None
        out.header = image.header
        return out

    def make_camera_info(self, image: Image) -> CameraInfo:
        info = CameraInfo()
        info.header = image.header
        info.width = image.width or self.camera_width
        info.height = image.height or self.camera_height
        info.distortion_model = self.camera_model
        info.D = self.camera_d
        scale_x = info.width / float(self.camera_width)
        scale_y = info.height / float(self.camera_height)
        camera_k = list(self.camera_k)
        camera_k[0] *= scale_x
        camera_k[2] *= scale_x
        camera_k[4] *= scale_y
        camera_k[5] *= scale_y
        info.K = camera_k
        info.R = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        info.P = [camera_k[0], 0.0, camera_k[2], 0.0,
                  0.0, camera_k[4], camera_k[5], 0.0,
                  0.0, 0.0, 1.0, 0.0]
        return info


def main() -> None:
    rospy.init_node("e2o_sensor_adapter")
    E2OSensorAdapter()
    rospy.spin()


if __name__ == "__main__":
    main()
