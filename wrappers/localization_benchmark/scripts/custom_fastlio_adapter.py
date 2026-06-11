#!/usr/bin/env python3
import copy
import os
import random
import struct
import threading
import time

import rospy
import sensor_msgs.point_cloud2 as pc2
import yaml
from sensor_msgs.msg import CameraInfo, Image, Imu, PointCloud2
from std_msgs.msg import Header

from custom_localization_msgs.msg import CustomImage, CustomImu, CustomPointCloud

try:
    import cv2
    import numpy as np
    from cv_bridge import CvBridge
except ImportError:
    cv2 = None
    np = None
    CvBridge = None


def patched_header(header, frame_id):
    out = Header()
    out.seq = header.seq
    out.stamp = header.stamp
    out.frame_id = frame_id
    return out


class PerturbationConfig:
    def __init__(self, path, run_id):
        self.path = path
        self.run_id = str(run_id)
        self.mtime = None
        self.last_reload_check = 0.0
        self.reload_interval = 1.0
        self.perturbations = []
        self.lock = threading.Lock()
        self.load(force=True)

    def load(self, force=False):
        now = time.monotonic()
        if not force and now - self.last_reload_check < self.reload_interval:
            return
        self.last_reload_check = now
        try:
            mtime = os.path.getmtime(self.path)
        except OSError:
            if force:
                rospy.logwarn("[PerturbationConfig] Missing config: %s", self.path)
            return
        if not force and self.mtime == mtime:
            return
        with open(self.path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        if "perturbations" in data:
            run_cfg = data
        else:
            run_cfg = (data.get("runs") or {}).get(self.run_id, {})
        with self.lock:
            self.mtime = mtime
            self.perturbations = run_cfg.get("perturbations") or []
        rospy.loginfo(
            "[PerturbationConfig] Loaded run=%s name=%s perturbations=%d",
            self.run_id,
            run_cfg.get("name", "unknown"),
            len(self.perturbations),
        )

    def active_for(self, sensor, stamp):
        self.load()
        with self.lock:
            return [
                p for p in self.perturbations
                if p.get("sensor") == sensor
                and float(p.get("start", -1.0e30)) <= stamp <= float(p.get("end", 1.0e30))
            ]


class CustomFastLioAdapter:
    def __init__(self):
        self.run_id = rospy.get_param("~run_id", "1")
        cfg_path = rospy.get_param(
            "~perturbation_config",
            "/root/catkin_ws/src/localization_benchmark/config/perturbations/per_0.yaml",
        )
        self.config = PerturbationConfig(cfg_path, self.run_id)
        self.bridge = CvBridge() if CvBridge else None
        self.rngs = {}
        self.publish_camera = rospy.get_param("~publish_camera", True)
        self.publish_camera_info = rospy.get_param("~publish_camera_info", True)
        self.camera_frame_id = rospy.get_param("~camera_frame_id", "camera_right")
        # FAST-LIVO2 native Velodyne parser expects per-point time in microseconds.
        # UrbanNav /velodyne_points stores the FLOAT32 time field in seconds.
        # Keep default 1.0 for FAST-LIO2; set 1000000.0 for FAST-LIVO2 via algorithms.yaml.
        self.point_time_scale = float(rospy.get_param("~point_time_scale", 1.0))
        self._point_time_checked = False
        self._point_time_offset = None
        self._point_time_struct = None

        self.lidar_pub = rospy.Publisher(
            rospy.get_param("~native_lidar_topic", "/cloud_registered_raw"),
            PointCloud2,
            queue_size=50,
        )
        self.imu_pub = rospy.Publisher(
            rospy.get_param("~native_imu_topic", "/livox/imu"),
            Imu,
            queue_size=200,
        )
        self.camera_pub = rospy.Publisher(
            rospy.get_param("~native_camera_topic", "/camera/right/image_raw"),
            Image,
            queue_size=20,
        )
        self.camera_info_pub = rospy.Publisher(
            rospy.get_param("~native_camera_info_topic", "/camera/right/camera_info"),
            CameraInfo,
            queue_size=20,
        )

        rospy.Subscriber(
            rospy.get_param("~custom_lidar_topic", "/mycar/lidar/custom_points"),
            CustomPointCloud,
            self.lidar_cb,
            queue_size=50,
        )
        rospy.Subscriber(
            rospy.get_param("~custom_imu_topic", "/mycar/imu/custom_imu"),
            CustomImu,
            self.imu_cb,
            queue_size=200,
        )
        rospy.Subscriber(
            rospy.get_param("~custom_camera_topic", "/mycar/camera/right/custom_image"),
            CustomImage,
            self.camera_cb,
            queue_size=20,
        )

    def rng(self, perturbation):
        name = perturbation.get("name", perturbation.get("type", "unnamed"))
        if name not in self.rngs:
            self.rngs[name] = random.Random(int(perturbation.get("seed", 1)))
        return self.rngs[name]

    def lidar_cb(self, msg):
        stamp = msg.header.stamp.to_sec()
        active = self.config.active_for("lidar", stamp)
        if not active:
            out = msg.cloud
            out.header = patched_header(msg.header, "velodyne")
            self.lidar_pub.publish(self.scale_point_time_if_needed(out))
            return

        out = copy.deepcopy(msg.cloud)
        out.header = patched_header(msg.header, "velodyne")
        label = []
        for perturbation in active:
            ptype = perturbation.get("type")
            if ptype == "sensor_off":
                return
            if ptype == "scan_dropout" and self.rng(perturbation).random() < float(perturbation.get("drop_rate", 0.0)):
                return
            if ptype == "point_dropout":
                out = self.apply_point_dropout(out, perturbation)
                label.append(perturbation.get("name", ptype))
            if ptype in ("range_noise", "rain"):
                out = self.apply_lidar_xyz_noise(out, perturbation)
                label.append(perturbation.get("name", ptype))
        self.lidar_pub.publish(self.scale_point_time_if_needed(out))

    def scale_point_time_if_needed(self, cloud):
        if abs(self.point_time_scale - 1.0) < 1e-12:
            return cloud
        if not self._point_time_checked:
            self._point_time_checked = True
            for field in cloud.fields:
                if field.name == "time" and field.datatype == 7:  # PointField.FLOAT32
                    self._point_time_offset = field.offset
                    self._point_time_struct = struct.Struct(">f" if cloud.is_bigendian else "<f")
                    break
            if self._point_time_offset is None:
                rospy.logwarn("[CustomFastLioAdapter] point_time_scale=%.3g requested but no FLOAT32 'time' field found", self.point_time_scale)
            else:
                rospy.loginfo("[CustomFastLioAdapter] Scaling Velodyne point time field by %.3g", self.point_time_scale)
        if self._point_time_offset is None:
            return cloud
        out = copy.deepcopy(cloud)
        data = bytearray(out.data)
        point_count = out.width * out.height
        for idx in range(point_count):
            off = idx * out.point_step + self._point_time_offset
            if off + 4 > len(data):
                break
            t = self._point_time_struct.unpack_from(data, off)[0]
            self._point_time_struct.pack_into(data, off, t * self.point_time_scale)
        out.data = bytes(data)
        return out

    def apply_point_dropout(self, cloud, perturbation):
        drop_rate = max(0.0, min(1.0, float(perturbation.get("drop_rate", 0.0))))
        if drop_rate <= 0.0:
            return cloud
        rng = self.rng(perturbation)
        points = [
            p for p in pc2.read_points(cloud, field_names=None, skip_nans=False)
            if rng.random() >= drop_rate
        ]
        out = pc2.create_cloud(cloud.header, cloud.fields, points)
        out.is_dense = cloud.is_dense
        return out

    def apply_lidar_xyz_noise(self, cloud, perturbation):
        stddev = float(perturbation.get("xyz_stddev", perturbation.get("stddev", 0.03)))
        drop_rate = max(0.0, min(1.0, float(perturbation.get("drop_rate", 0.0))))
        if stddev <= 0.0 and drop_rate <= 0.0:
            return cloud
        rng = self.rng(perturbation)
        field_names = [field.name for field in cloud.fields]
        points = []
        for point in pc2.read_points(cloud, field_names=None, skip_nans=False):
            if drop_rate > 0.0 and rng.random() < drop_rate:
                continue
            values = list(point)
            for axis in ("x", "y", "z"):
                if axis in field_names:
                    values[field_names.index(axis)] += rng.gauss(0.0, stddev)
            points.append(tuple(values))
        out = pc2.create_cloud(cloud.header, cloud.fields, points)
        out.is_dense = cloud.is_dense
        return out

    def imu_cb(self, msg):
        stamp = msg.header.stamp.to_sec()
        active = self.config.active_for("imu", stamp)
        if not active:
            out = msg.imu
            out.header = patched_header(msg.header, "body")
            self.imu_pub.publish(out)
            return

        out = copy.deepcopy(msg.imu)
        out.header = patched_header(msg.header, "body")
        for perturbation in active:
            ptype = perturbation.get("type")
            if ptype == "sensor_off":
                return
            if ptype == "dropout" and self.rng(perturbation).random() < float(perturbation.get("drop_rate", 0.0)):
                return
            if ptype == "bias":
                self.apply_imu_bias(out, perturbation)
            if ptype == "gaussian_noise":
                self.apply_imu_noise(out, perturbation)
        self.imu_pub.publish(out)

    def apply_imu_bias(self, imu, perturbation):
        gyro = perturbation.get("angular_velocity_bias", [0.0, 0.0, 0.0])
        accel = perturbation.get("linear_acceleration_bias", [0.0, 0.0, 0.0])
        imu.angular_velocity.x += float(gyro[0])
        imu.angular_velocity.y += float(gyro[1])
        imu.angular_velocity.z += float(gyro[2])
        imu.linear_acceleration.x += float(accel[0])
        imu.linear_acceleration.y += float(accel[1])
        imu.linear_acceleration.z += float(accel[2])

    def apply_imu_noise(self, imu, perturbation):
        rng = self.rng(perturbation)
        gyro = perturbation.get("angular_velocity_stddev", [0.0, 0.0, 0.0])
        accel = perturbation.get("linear_acceleration_stddev", [0.0, 0.0, 0.0])
        imu.angular_velocity.x += rng.gauss(0.0, float(gyro[0]))
        imu.angular_velocity.y += rng.gauss(0.0, float(gyro[1]))
        imu.angular_velocity.z += rng.gauss(0.0, float(gyro[2]))
        imu.linear_acceleration.x += rng.gauss(0.0, float(accel[0]))
        imu.linear_acceleration.y += rng.gauss(0.0, float(accel[1]))
        imu.linear_acceleration.z += rng.gauss(0.0, float(accel[2]))

    def camera_cb(self, msg):
        if not self.publish_camera:
            return
        stamp = msg.header.stamp.to_sec()
        active = self.config.active_for("camera_right", stamp)
        if not active:
            out = msg.image
            out.header = patched_header(msg.header, self.camera_frame_id)
            self.camera_pub.publish(out)
            self.publish_cam_info(out.header, out.width, out.height)
            return

        out = copy.deepcopy(msg.image)
        out.header = patched_header(msg.header, self.camera_frame_id)
        for perturbation in active:
            ptype = perturbation.get("type")
            if ptype == "sensor_off":
                return
            if ptype == "frame_dropout" and self.rng(perturbation).random() < float(perturbation.get("drop_rate", 0.0)):
                return
            if ptype == "low_light":
                out = self.apply_low_light(out, perturbation)
            if ptype == "rain":
                out = self.apply_camera_rain(out, perturbation)
            if ptype == "motion_blur":
                out = self.apply_motion_blur(out, perturbation)
        self.camera_pub.publish(out)
        self.publish_cam_info(out.header, out.width, out.height)

    def publish_cam_info(self, header, width, height):
        if not self.publish_camera_info:
            return
        info = CameraInfo()
        info.header = header
        info.width = width or 672
        info.height = height or 376
        info.distortion_model = "plumb_bob"
        info.D = [-0.0423469, 0.0115525, 0.0, 0.0, 0.0]
        fx, fy, cx, cy = 264.2125, 264.155, 341.635, 183.993
        info.K = [fx, 0.0, cx, 0.0, fy, cy, 0.0, 0.0, 1.0]
        info.R = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        info.P = [fx, 0.0, cx, 0.0, 0.0, fy, cy, 0.0, 0.0, 0.0, 1.0, 0.0]
        self.camera_info_pub.publish(info)

    def apply_low_light(self, image, perturbation):
        if not self.bridge or np is None:
            rospy.logwarn_throttle(10.0, "[CustomFastLioAdapter] cv_bridge unavailable; camera perturbation skipped")
            return image
        cv_img = self.bridge.imgmsg_to_cv2(image, desired_encoding="passthrough")
        alpha = float(perturbation.get("alpha", 0.5))
        out = cv_img.astype(np.float32) * alpha
        noise_stddev = float(perturbation.get("noise_stddev", 0.0))
        if noise_stddev > 0.0:
            rng = np.random.default_rng(int(perturbation.get("seed", 1)))
            out += rng.normal(0.0, noise_stddev, out.shape)
        out = np.clip(out, 0, 255).astype(cv_img.dtype)
        perturbed = self.bridge.cv2_to_imgmsg(out, encoding=image.encoding)
        perturbed.header = image.header
        return perturbed

    def apply_camera_rain(self, image, perturbation):
        if not self.bridge or np is None or cv2 is None:
            rospy.logwarn_throttle(10.0, "[CustomFastLioAdapter] cv_bridge/cv2 unavailable; rain perturbation skipped")
            return image
        cv_img = self.bridge.imgmsg_to_cv2(image, desired_encoding="passthrough")
        out = cv_img.copy()
        rng = np.random.default_rng(int(perturbation.get("seed", 1)))
        streaks = int(perturbation.get("streaks", 120))
        length = int(perturbation.get("length", 18))
        brightness = int(perturbation.get("brightness", 180))
        height, width = out.shape[:2]
        for _ in range(streaks):
            x = int(rng.integers(0, max(width, 1)))
            y = int(rng.integers(0, max(height, 1)))
            x2 = min(width - 1, x + int(length * 0.3))
            y2 = min(height - 1, y + length)
            color = brightness if out.ndim == 2 else (brightness, brightness, brightness)
            cv2.line(out, (x, y), (x2, y2), color, 1)
        alpha = float(perturbation.get("alpha", 0.35))
        blended = cv2.addWeighted(out, alpha, cv_img, 1.0 - alpha, 0)
        perturbed = self.bridge.cv2_to_imgmsg(blended, encoding=image.encoding)
        perturbed.header = image.header
        return perturbed

    def apply_motion_blur(self, image, perturbation):
        if not self.bridge or np is None or cv2 is None:
            rospy.logwarn_throttle(10.0, "[CustomFastLioAdapter] cv_bridge/cv2 unavailable; motion blur skipped")
            return image
        cv_img = self.bridge.imgmsg_to_cv2(image, desired_encoding="passthrough")
        size = max(3, int(perturbation.get("kernel_size", 9)))
        if size % 2 == 0:
            size += 1
        kernel = np.zeros((size, size), dtype=np.float32)
        kernel[size // 2, :] = 1.0 / size
        blurred = cv2.filter2D(cv_img, -1, kernel)
        perturbed = self.bridge.cv2_to_imgmsg(blurred, encoding=image.encoding)
        perturbed.header = image.header
        return perturbed


def main():
    rospy.init_node("custom_fastlio_adapter")
    CustomFastLioAdapter()
    rospy.spin()


if __name__ == "__main__":
    main()
