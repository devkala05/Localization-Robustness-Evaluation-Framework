#!/usr/bin/env python3
"""E2O-only sensor adapter for FAST-LIVO2, ORB-SLAM3, and LVI-SAM.

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
from sensor_msgs.msg import CameraInfo, Image, Imu, PointCloud2, PointField


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
        cfg = rospy.get_param("/e2o/adapter", {})
        topics = dict(cfg.get("topics", {}))
        topics["lidar"] = rospy.get_param("~source_lidar_topic", topics.get("lidar", "/lidar103/velodyne_points"))
        topics["imu"] = rospy.get_param("~source_imu_topic", topics.get("imu", "/mavros/imu/data"))
        topics["camera"] = rospy.get_param("~source_camera_topic", topics.get("camera", "/camera/color/image_raw"))
        topics["depth"] = rospy.get_param("~source_depth_topic", topics.get("depth", "/camera/depth/image_rect_raw"))
        outputs = cfg.get("outputs", {})
        camera = cfg.get("camera", {})
        orb_rgbd = cfg.get("orb_rgbd", {})
        lidar = cfg.get("lidar", {})
        frames = cfg.get("frames", {})

        self.lidar_frame = str(frames.get("lidar", "velodyne103"))
        self.imu_frame = str(frames.get("imu", "base_link"))
        self.camera_frame = str(frames.get("camera_optical", "camera_color_optical_frame"))
        self.depth_frame = str(frames.get("depth_optical", "camera_depth_optical_frame"))
        self.point_time_scale = float(lidar.get("point_time_scale", 1.0e6))
        self.auto_detect_time_units = bool(lidar.get("auto_detect_time_units", True))
        self.require_ring = bool(lidar.get("require_ring", True))

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

        rospy.Subscriber(str(topics.get("lidar", "/lidar103/velodyne_points")), PointCloud2,
                         lambda msg: self.route("lidar", msg), queue_size=20)
        rospy.Subscriber(str(topics.get("imu", "/mavros/imu/data")), Imu,
                         lambda msg: self.route("imu", msg), queue_size=200)
        rospy.Subscriber(str(topics.get("camera", "/camera/color/image_raw")), Image,
                         lambda msg: self.route("camera", msg), queue_size=20)
        rospy.Subscriber(str(topics.get("depth", "/camera/depth/image_rect_raw")), Image,
                         lambda msg: self.route("depth", msg), queue_size=20)
        rospy.Timer(rospy.Duration(0.01), self.timer_cb)
        rospy.loginfo("[E2OAdapter] raw topics -> lidar=%s imu=%s camera=%s orb_rgb=%s orb_depth=%s",
                      self.lidar_pub.resolved_name, self.imu_pub.resolved_name,
                      self.camera_pub.resolved_name, self.orb_camera_pub.resolved_name,
                      self.orb_depth_pub.resolved_name)

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
        if math.isclose(self.point_time_scale, 1.0):
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
        dst_view *= self.point_time_scale
        out.data = bytes(raw)
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
        rospy.loginfo_once("[E2OAdapter] normalized negative LVI-SAM point times to scan start")
        return out

    def publish_lidar(self, msg: PointCloud2) -> None:
        self.publish_lvisam_lidar(msg)
        out = self._scale_point_time(msg)
        out.header.frame_id = self.lidar_frame
        if self.require_ring and self._field(out, "ring") is None:
            rospy.logerr_throttle(5.0, "[E2OAdapter] lidar ring field missing; FAST-LIVO2 scan-line processing may be invalid")
        self.lidar_pub.publish(out)

    def publish_lvisam_lidar(self, msg: PointCloud2) -> None:
        out = self._normalize_lvisam_point_time(msg)
        out.header.frame_id = self.lidar_frame
        if self.require_ring and self._field(out, "ring") is None:
            rospy.logerr_throttle(5.0, "[E2OAdapter] lidar ring field missing; LVI-SAM N_SCAN projection may be invalid")
        if self._field(out, "time") is None:
            rospy.logwarn_throttle(5.0, "[E2OAdapter] lidar has no per-point 'time' field for LVI-SAM")
        self.lvisam_lidar_pub.publish(out)

    def publish_imu(self, msg: Imu) -> None:
        out = copy.deepcopy(msg)
        out.header.frame_id = self.imu_frame
        self.imu_pub.publish(out)
        self.lvisam_imu_pub.publish(out)

    def _normalize_image_time(self, msg: Image) -> Image:
        out = copy.deepcopy(msg)
        if self.camera_timestamp_mode == "callback":
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
        orb_rgb = self.make_orb_rgb(out)
        if orb_rgb is not None:
            orb_stamp = orb_rgb.header.stamp.to_sec()
            if self._admit_at_rate(self.last_orb_camera_stamp, orb_stamp, self.orb_rgbd_max_rate):
                self.last_orb_camera_stamp = orb_stamp
                self.orb_camera_pub.publish(orb_rgb)
        self.lvisam_camera_pub.publish(out)
        lvisam_info = self.make_camera_info(out)
        self.lvisam_camera_info_pub.publish(lvisam_info)
        stamp = out.header.stamp.to_sec()
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
        target_size = self.latest_depth_size
        if target_size is None:
            if self.orb_rgbd_width > 0 and self.orb_rgbd_height > 0:
                target_size = (self.orb_rgbd_width, self.orb_rgbd_height)
            else:
                rospy.logwarn_throttle(5.0, "[E2OAdapter] waiting for depth image before publishing ORB RGB-D color")
                return None
        target_width, target_height = target_size
        if int(image.width) == target_width and int(image.height) == target_height:
            return image
        try:
            cv_image = self.bridge.imgmsg_to_cv2(image, desired_encoding="passthrough")
            resized = cv2.resize(cv_image, (target_width, target_height), interpolation=cv2.INTER_LINEAR)
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
        info.K = self.camera_k
        info.R = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        info.P = [self.camera_k[0], 0.0, self.camera_k[2], 0.0,
                  0.0, self.camera_k[4], self.camera_k[5], 0.0,
                  0.0, 0.0, 1.0, 0.0]
        return info


def main() -> None:
    rospy.init_node("e2o_sensor_adapter")
    E2OSensorAdapter()
    rospy.spin()


if __name__ == "__main__":
    main()
