#!/usr/bin/env python3
"""Stream a Boreas-RT sequence as ROS 1 messages without generating a bag."""
from __future__ import annotations

import csv
import heapq
import math
import os
import time
from pathlib import Path
from typing import Iterator, Tuple

import cv2
import numpy as np
import rospy
from tf.transformations import quaternion_from_matrix
from cv_bridge import CvBridge
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import Image, Imu, PointCloud2, PointField
from std_msgs.msg import Header, String


Event = Tuple[float, str, object]


def timestamped_files(path: Path, suffix: str, kind: str) -> Iterator[Event]:
    for item in sorted(path.glob(f"*{suffix}")):
        try:
            stamp = int(item.stem) / 1.0e6
        except ValueError:
            continue
        yield stamp, kind, item


def imu_rows(path: Path) -> Iterator[Event]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            stamp = int(row["time"]) / 1.0e9
            values = tuple(float(row[name]) for name in ("wx", "wy", "wz", "ax", "ay", "az"))
            if all(math.isfinite(value) for value in values):
                yield stamp, "imu", values


class BoreasPlayer:
    def __init__(self) -> None:
        self.root = Path(rospy.get_param("~sequence_root")).resolve()
        self.rate = float(rospy.get_param("~rate", 1.0))
        self.start_offset = max(0.0, float(rospy.get_param("~start_offset", 0.0)))
        self.duration = float(rospy.get_param("~duration", 0.0))
        self.enabled = {
            "lidar": bool(rospy.get_param("~enable_lidar", True)),
            "imu": bool(rospy.get_param("~enable_imu", True)),
            "camera": bool(rospy.get_param("~enable_camera", True)),
        }
        if self.rate <= 0.0:
            raise rospy.ROSInitException("rate must be positive")
        required = (
            self.root / "lidar",
            self.root / "camera",
            self.root / "imu" / "dmu_imu_infilled.csv",
            self.root / "calib",
            self.root / "applanix" / "gps_post_process.csv",
        )
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise rospy.ROSInitException("missing Boreas inputs: " + ", ".join(missing))

        self.clock_pub = rospy.Publisher("/clock", Clock, queue_size=20)
        self.lidar_pub = rospy.Publisher("/dataset/lidar", PointCloud2, queue_size=3)
        self.imu_pub = rospy.Publisher("/dataset/imu", Imu, queue_size=400)
        self.camera_pub = rospy.Publisher("/dataset/camera", Image, queue_size=3)
        self.status_pub = rospy.Publisher("/benchmark/player_status", String, queue_size=2, latch=True)
        self.bridge = CvBridge()
        self.counts = {"lidar": 0, "imu": 0, "camera": 0}
        # Boreas DMU axes are x-forward/y-right/z-down.  The supplied
        # T_applanix_dmu calibration gives their fixed orientation in the
        # vehicle's x-forward/y-left/z-up Applanix frame.  Use that measured
        # mounting attitude for roll/pitch initialization; its yaw merely
        # defines the estimator's arbitrary local heading and is not GT.
        dmu_to_vehicle = np.loadtxt(str(self.root / "calib" / "T_applanix_dmu.txt"))
        if dmu_to_vehicle.shape != (4, 4) or not np.all(np.isfinite(dmu_to_vehicle)):
            raise rospy.ROSInitException("invalid calib/T_applanix_dmu.txt")
        rotation = dmu_to_vehicle[:3, :3]
        u, _, vh = np.linalg.svd(rotation)
        dmu_to_vehicle[:3, :3] = u @ vh
        self.dmu_orientation = np.asarray(quaternion_from_matrix(dmu_to_vehicle), dtype=float)
        self.dmu_orientation_stamp = None

    @staticmethod
    def lidar_message(path: Path, stamp: float) -> PointCloud2:
        points = np.fromfile(str(path), dtype=np.float32)
        if points.size % 6:
            raise ValueError(f"invalid Boreas lidar shape in {path}")
        points = points.reshape((-1, 6))
        valid = np.all(np.isfinite(points[:, :4]), axis=1)
        points = points[valid]
        dtype = np.dtype({
            "names": ("x", "y", "z", "intensity", "ring", "time"),
            "formats": ("<f4", "<f4", "<f4", "<f4", "<u2", "<f4"),
            "offsets": (0, 4, 8, 12, 16, 18),
            "itemsize": 22,
        })
        packed = np.empty(points.shape[0], dtype=dtype)
        for index, name in enumerate(("x", "y", "z", "intensity")):
            packed[name] = points[:, index]
        packed["ring"] = np.clip(points[:, 4], 0, 127).astype(np.uint16)
        packed["time"] = points[:, 5]
        msg = PointCloud2()
        msg.header = Header(stamp=rospy.Time.from_sec(stamp), frame_id="lidar")
        msg.height = 1
        msg.width = packed.shape[0]
        msg.fields = [
            PointField("x", 0, PointField.FLOAT32, 1),
            PointField("y", 4, PointField.FLOAT32, 1),
            PointField("z", 8, PointField.FLOAT32, 1),
            PointField("intensity", 12, PointField.FLOAT32, 1),
            PointField("ring", 16, PointField.UINT16, 1),
            PointField("time", 18, PointField.FLOAT32, 1),
        ]
        msg.is_bigendian = False
        msg.point_step = packed.dtype.itemsize
        msg.row_step = msg.point_step * msg.width
        msg.data = packed.tobytes()
        msg.is_dense = bool(np.all(valid))
        return msg

    def camera_message(self, path: Path, stamp: float) -> Image:
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"failed to decode {path}")
        msg = self.bridge.cv2_to_imgmsg(image, encoding="bgr8")
        msg.header.stamp = rospy.Time.from_sec(stamp)
        msg.header.frame_id = "camera"
        return msg

    def imu_message(self, values, stamp: float) -> Imu:
        wx, wy, wz, ax, ay, az = values
        angular = np.asarray([wx, wy, wz], dtype=float)
        if self.dmu_orientation_stamp is not None:
            dt = stamp - self.dmu_orientation_stamp
            angular_norm = float(np.linalg.norm(angular))
            if 0.0 < dt < 0.1 and angular_norm > 1.0e-12:
                angle = angular_norm * dt
                delta = np.asarray([
                    *(angular / angular_norm * math.sin(angle / 2.0)),
                    math.cos(angle / 2.0),
                ])
                self.dmu_orientation = self._quat_multiply(self.dmu_orientation, delta)
            self.dmu_orientation /= np.linalg.norm(self.dmu_orientation)
        self.dmu_orientation_stamp = stamp
        msg = Imu()
        msg.header.stamp = rospy.Time.from_sec(stamp)
        msg.header.frame_id = "dmu"
        (msg.orientation.x, msg.orientation.y, msg.orientation.z,
         msg.orientation.w) = self.dmu_orientation
        msg.orientation_covariance[0] = 0.01
        msg.orientation_covariance[4] = 0.01
        msg.orientation_covariance[8] = 1.0
        msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z = wx, wy, wz
        msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z = ax, ay, az
        return msg

    @staticmethod
    def _quat_multiply(left, right):
        lx, ly, lz, lw = left
        rx, ry, rz, rw = right
        return np.asarray([
            lw * rx + lx * rw + ly * rz - lz * ry,
            lw * ry - lx * rz + ly * rw + lz * rx,
            lw * rz + lx * ry - ly * rx + lz * rw,
            lw * rw - lx * rx - ly * ry - lz * rz,
        ])


    def publish(self, kind: str, payload, stamp: float) -> None:
        clock = Clock(clock=rospy.Time.from_sec(stamp))
        self.clock_pub.publish(clock)
        if kind == "lidar":
            self.lidar_pub.publish(self.lidar_message(payload, stamp))
        elif kind == "camera":
            self.camera_pub.publish(self.camera_message(payload, stamp))
        else:
            self.imu_pub.publish(self.imu_message(payload, stamp))
        self.counts[kind] += 1

    def run(self) -> None:
        available_sources = {
            "lidar": iter(timestamped_files(self.root / "lidar", ".bin", "lidar")),
            "camera": iter(timestamped_files(self.root / "camera", ".png", "camera")),
            "imu": iter(imu_rows(self.root / "imu" / "dmu_imu_infilled.csv")),
        }
        sources = [source for kind, source in available_sources.items() if self.enabled[kind]]
        if not sources:
            raise rospy.ROSException("at least one Boreas sensor stream must be enabled")
        heap = []
        for index, source in enumerate(sources):
            try:
                stamp, kind, payload = next(source)
                heapq.heappush(heap, (stamp, index, kind, payload))
            except StopIteration:
                pass
        if len(heap) != len(sources):
            raise rospy.ROSException("one or more Boreas streams are empty")
        raw_start = min(item[0] for item in heap)
        play_start = raw_start + self.start_offset
        play_end = play_start + self.duration if self.duration > 0.0 else math.inf
        wall_start = None
        first_stamp = None
        self.status_pub.publish(String(data="starting"))
        while heap and not rospy.is_shutdown():
            stamp, index, kind, payload = heapq.heappop(heap)
            try:
                next_stamp, next_kind, next_payload = next(sources[index])
                heapq.heappush(heap, (next_stamp, index, next_kind, next_payload))
            except StopIteration:
                pass
            if stamp < play_start:
                continue
            if stamp > play_end:
                break
            if first_stamp is None:
                first_stamp = stamp
                wall_start = time.monotonic()
            target = wall_start + (stamp - first_stamp) / self.rate
            while not rospy.is_shutdown():
                remaining = target - time.monotonic()
                if remaining <= 0.0:
                    break
                time.sleep(min(remaining, 0.02))
            self.publish(kind, payload, stamp)
        self.status_pub.publish(String(data="completed"))
        rospy.loginfo("[BoreasPlayer] completed counts=%s", self.counts)


def main() -> None:
    rospy.init_node("boreas_player")
    BoreasPlayer().run()


if __name__ == "__main__":
    main()
