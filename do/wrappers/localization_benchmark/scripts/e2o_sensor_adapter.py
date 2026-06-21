#!/usr/bin/env python3
"""E2O-only sensor adapter for FAST-LIVO2 and ORB-SLAM3.

It republishes the original bag streams to the native topics expected by the
estimators, converts the Velodyne per-point ``time`` field from seconds to
microseconds when configured, publishes CameraInfo, and exposes deterministic
fault modes through ``/e2o_faults/<sensor>/*`` ROS parameters.

No estimator implementation is changed by this node.
"""
import collections
import copy
import math
import struct
import threading
import time
from typing import Deque, Dict, Optional, Tuple

import numpy as np
import rospy
from sensor_msgs.msg import CameraInfo, Image, Imu, PointCloud2, PointField


class StreamFaultGate:
    """Runtime-configurable pass/drop/freeze/delay gate for one sensor stream."""

    def __init__(self, name: str, publish_callback):
        self.name = name
        self.publish_callback = publish_callback
        self.frozen = None
        self.delay_queue: Deque[Tuple[float, object]] = collections.deque()

    @property
    def prefix(self) -> str:
        return f"/e2o_faults/{self.name}"

    def mode(self) -> str:
        return str(rospy.get_param(f"{self.prefix}/mode", "pass")).strip().lower()

    def handle(self, msg) -> None:
        mode = self.mode()
        if mode == "drop":
            return
        if mode == "freeze":
            if self.frozen is None:
                self.frozen = copy.deepcopy(msg)
            self.publish_callback(copy.deepcopy(self.frozen))
            return
        if mode == "delay":
            delay = max(0.0, float(rospy.get_param(f"{self.prefix}/delay_sec", 1.0)))
            self.delay_queue.append((time.monotonic() + delay, copy.deepcopy(msg)))
            return
        if mode != "pass":
            rospy.logwarn_throttle(2.0, "[E2OAdapter] unknown %s mode=%s; passing", self.name, mode)
        self.frozen = copy.deepcopy(msg)
        self.publish_callback(msg)

    def flush(self, now: float) -> None:
        while self.delay_queue and self.delay_queue[0][0] <= now:
            _, msg = self.delay_queue.popleft()
            self.publish_callback(msg)


class E2OSensorAdapter:
    def __init__(self) -> None:
        cfg = rospy.get_param("/e2o/adapter", {})
        topics = dict(cfg.get("topics", {}))
        topics["lidar"] = rospy.get_param("~source_lidar_topic", topics.get("lidar", "/lidar103/velodyne_points"))
        topics["imu"] = rospy.get_param("~source_imu_topic", topics.get("imu", "/mavros/imu/data"))
        topics["camera"] = rospy.get_param("~source_camera_topic", topics.get("camera", "/camera/color/image_raw"))
        outputs = cfg.get("outputs", {})
        camera = cfg.get("camera", {})
        lidar = cfg.get("lidar", {})
        frames = cfg.get("frames", {})

        self.lidar_frame = str(frames.get("lidar", "velodyne103"))
        self.imu_frame = str(frames.get("imu", "base_link"))
        self.camera_frame = str(frames.get("camera_optical", "camera_color_optical_frame"))
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

        self.lidar_pub = rospy.Publisher(str(outputs.get("lidar", "/livox/lidar")), PointCloud2, queue_size=20)
        self.imu_pub = rospy.Publisher(str(outputs.get("imu", "/livox/imu")), Imu, queue_size=200)
        self.camera_pub = rospy.Publisher(str(outputs.get("camera", "/camera/right/image_raw")), Image, queue_size=20)
        self.orb_camera_pub = rospy.Publisher(str(outputs.get("orb_camera", "/camera/image_raw")), Image, queue_size=20)
        self.camera_info_pub = rospy.Publisher(str(outputs.get("camera_info", "/camera/right/camera_info")), CameraInfo, queue_size=20)

        self.lock = threading.RLock()
        self.gates: Dict[str, StreamFaultGate] = {
            "lidar": StreamFaultGate("lidar", self.publish_lidar),
            "imu": StreamFaultGate("imu", self.publish_imu),
            "camera": StreamFaultGate("camera", self.publish_camera),
        }

        rospy.Subscriber(str(topics.get("lidar", "/lidar103/velodyne_points")), PointCloud2,
                         lambda msg: self.route("lidar", msg), queue_size=20)
        rospy.Subscriber(str(topics.get("imu", "/mavros/imu/data")), Imu,
                         lambda msg: self.route("imu", msg), queue_size=200)
        rospy.Subscriber(str(topics.get("camera", "/camera/color/image_raw")), Image,
                         lambda msg: self.route("camera", msg), queue_size=20)
        rospy.Timer(rospy.Duration(0.01), self.timer_cb)
        rospy.loginfo("[E2OAdapter] raw topics -> lidar=%s imu=%s camera=%s",
                      self.lidar_pub.resolved_name, self.imu_pub.resolved_name,
                      self.camera_pub.resolved_name)

    @staticmethod
    def _flatten(value, expected: int, name: str):
        array = np.asarray(value, dtype=float).reshape(-1)
        if array.size != expected or not np.all(np.isfinite(array)):
            raise rospy.ROSInitException(f"{name} must contain {expected} finite values")
        return array.tolist()

    def route(self, sensor: str, msg) -> None:
        with self.lock:
            self.gates[sensor].handle(msg)

    def timer_cb(self, _event) -> None:
        with self.lock:
            now = time.monotonic()
            for gate in self.gates.values():
                gate.flush(now)

    @staticmethod
    def _field(msg: PointCloud2, name: str) -> Optional[PointField]:
        return next((field for field in msg.fields if field.name == name), None)

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

        out = copy.deepcopy(msg)
        raw = bytearray(out.data)
        endian = ">" if out.is_bigendian else "<"
        fmt = endian + ("f" if field.datatype == PointField.FLOAT32 else "d")
        width = struct.calcsize(fmt)
        samples = []
        limit = min(max(1, out.width * out.height), 64)
        for index in range(limit):
            row, col = divmod(index, max(1, out.width))
            offset = row * out.row_step + col * out.point_step + field.offset
            if offset + width <= len(raw):
                value = struct.unpack_from(fmt, raw, offset)[0]
                if math.isfinite(value):
                    samples.append(abs(value))
        if self.auto_detect_time_units and samples and max(samples) > 1.0e3:
            # Already appears to be microseconds/nanoseconds. Avoid multiplying twice.
            return out

        for row in range(max(1, out.height)):
            base = row * out.row_step + field.offset
            for col in range(out.width):
                offset = base + col * out.point_step
                if offset + width > len(raw):
                    break
                value = struct.unpack_from(fmt, raw, offset)[0]
                struct.pack_into(fmt, raw, offset, value * self.point_time_scale)
        out.data = bytes(raw)
        return out

    def publish_lidar(self, msg: PointCloud2) -> None:
        out = self._scale_point_time(msg)
        out.header.frame_id = self.lidar_frame
        if self.require_ring and self._field(out, "ring") is None:
            rospy.logerr_throttle(5.0, "[E2OAdapter] lidar ring field missing; FAST-LIVO2 scan-line processing may be invalid")
        self.lidar_pub.publish(out)

    def publish_imu(self, msg: Imu) -> None:
        out = copy.deepcopy(msg)
        out.header.frame_id = self.imu_frame
        self.imu_pub.publish(out)

    def publish_camera(self, msg: Image) -> None:
        out = copy.deepcopy(msg)
        if self.camera_timestamp_mode == "callback":
            out.header.stamp = rospy.Time.now()
        elif self.camera_timestamp_mode == "rebase":
            if self.camera_time_offset is None:
                self.camera_time_offset = rospy.Time.now() - out.header.stamp
                rospy.loginfo("[E2OAdapter] camera clock rebased by %.6f s",
                              self.camera_time_offset.to_sec())
            out.header.stamp = out.header.stamp + self.camera_time_offset
        out.header.frame_id = self.camera_frame
        self.orb_camera_pub.publish(out)
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
        info = CameraInfo()
        info.header = out.header
        info.width = out.width or self.camera_width
        info.height = out.height or self.camera_height
        info.distortion_model = self.camera_model
        info.D = self.camera_d
        info.K = self.camera_k
        info.R = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        info.P = [self.camera_k[0], 0.0, self.camera_k[2], 0.0,
                  0.0, self.camera_k[4], self.camera_k[5], 0.0,
                  0.0, 0.0, 1.0, 0.0]
        self.camera_info_pub.publish(info)


def main() -> None:
    rospy.init_node("e2o_sensor_adapter")
    E2OSensorAdapter()
    rospy.spin()


if __name__ == "__main__":
    main()
