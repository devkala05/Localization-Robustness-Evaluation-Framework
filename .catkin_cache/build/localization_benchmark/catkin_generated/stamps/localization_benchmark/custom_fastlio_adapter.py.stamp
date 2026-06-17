#!/usr/bin/env python3
import copy
import ast
import math
import os
import random
import struct
import threading
import time

import rospy
import sensor_msgs.point_cloud2 as pc2
import yaml
from sensor_msgs.msg import CameraInfo, Image, Imu, PointCloud2, PointField
from std_msgs.msg import Header

from custom_localization_msgs.msg import CustomImage, CustomImu, CustomPointCloud

try:
    from livox_ros_driver.msg import CustomMsg as LivoxCustomMsg, CustomPoint as LivoxCustomPoint
except Exception:  # optional: only R3LIVE/FAST-LIVO need this output
    LivoxCustomMsg = None
    LivoxCustomPoint = None

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


def image_with_header(image, header):
    """Return a shallow Image copy with a new header.

    sensor_msgs/Image.data is a bytes/array payload; assigning it by reference is
    fine here because we never mutate the payload after perturbations are applied.
    This helper lets ORB-SLAM3 publish the same physical camera image on multiple
    topics with different ROS frame IDs without re-encoding the image.
    """
    out = Image()
    out.header = header
    out.height = image.height
    out.width = image.width
    out.encoding = image.encoding
    out.is_bigendian = image.is_bigendian
    out.step = image.step
    out.data = image.data
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
        self.camera_models = {
            "right": self._camera_model_from_params("right", [264.2125, 0.0, 341.635, 0.0, 264.155, 183.993, 0.0, 0.0, 1.0], [-0.0423469, 0.0115525, 0.0, 0.0, 0.0]),
            "left": self._camera_model_from_params("left", [264.9425, 0.0, 334.3975, 0.0, 264.79, 183.162, 0.0, 0.0, 1.0], [-0.0442856, 0.0133574, 0.0, 0.0, 0.0]),
        }
        # FAST-LIVO2 native Velodyne parser expects per-point time in microseconds.
        # UrbanNav /velodyne_points stores the FLOAT32 time field in seconds.
        # Keep default 1.0 for FAST-LIO2; set 1000000.0 for FAST-LIVO2 via algorithms.yaml.
        self.point_time_scale = float(rospy.get_param("~point_time_scale", 1.0))
        # Some native R3LIVE/FAST-LIO-family builds subscribe to PointCloud2 as
        # pcl::PointXYZINormal. UrbanNav Velodyne bags have x/y/z/intensity/ring/time
        # only, which makes those nodes spam "Failed to find match for field
        # normal_x/normal_y/normal_z/curvature" and produce no odometry. Keep this
        # disabled for normal FAST-LIO2/LVI-SAM runs and enable it only for R3LIVE.
        self.add_normal_fields = bool(rospy.get_param("~add_normal_fields", False))
        self.curvature_from_time = bool(rospy.get_param("~curvature_from_time", True))
        self.drop_nan_points = bool(rospy.get_param("~drop_nan_points", True))
        self.ring_count = int(rospy.get_param("~ring_count", 0) or 0)
        self._point_time_checked = False
        self._point_time_offset = None
        self._point_time_struct = None
        self._point_time_convert = False
        self._nan_filter_logged = False
        self._ring_synthesis_logged = False

        self.native_lidar_topic = rospy.get_param("~native_lidar_topic", "/cloud_registered_raw")
        self.lidar_pub = rospy.Publisher(
            self.native_lidar_topic,
            PointCloud2,
            queue_size=50,
        )
        self.publish_livox_custom_msg = rospy.get_param("~publish_livox_custom_msg", False)
        self.native_lidar_custom_topic = rospy.get_param("~native_lidar_custom_topic", "/livox/lidar_custom")
        if self.publish_livox_custom_msg and LivoxCustomMsg is None:
            rospy.logerr("[CustomFastLioAdapter] publish_livox_custom_msg=true but livox_ros_driver/CustomMsg is not importable")
            self.publish_livox_custom_msg = False
        self.livox_custom_pub = rospy.Publisher(
            self.native_lidar_custom_topic,
            LivoxCustomMsg if LivoxCustomMsg is not None else PointCloud2,
            queue_size=50,
        ) if self.publish_livox_custom_msg else None
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
        self.publish_left_camera = rospy.get_param("~publish_left_camera", False)
        self.left_camera_frame_id = rospy.get_param("~left_camera_frame_id", "camera_left")
        self.stereo_swap_lr = rospy.get_param("~stereo_swap_lr", False)
        mono_camera_topic = rospy.get_param("~native_mono_camera_topic", "")
        self.mono_camera_pub = rospy.Publisher(mono_camera_topic, Image, queue_size=20) if mono_camera_topic else None
        self.left_camera_pub = rospy.Publisher(
            rospy.get_param("~native_left_camera_topic", "/camera/left/image_raw"),
            Image,
            queue_size=20,
        )
        self.left_camera_info_pub = rospy.Publisher(
            rospy.get_param("~native_left_camera_info_topic", "/camera/left/camera_info"),
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
        rospy.Subscriber(
            rospy.get_param("~custom_left_camera_topic", "/mycar/camera/left/custom_image"),
            CustomImage,
            self.left_camera_cb,
            queue_size=20,
        )

        rospy.loginfo(
            "[CustomFastLioAdapter] lidar pointcloud=%s livox_custom=%s enabled=%s add_normal_fields=%s",
            self.native_lidar_topic,
            self.native_lidar_custom_topic,
            self.publish_livox_custom_msg,
            self.add_normal_fields,
        )

        rospy.loginfo(
            "[CustomFastLioAdapter] camera stereo_swap_lr=%s right->%s left->%s mono=%s",
            self.stereo_swap_lr,
            rospy.get_param("~native_left_camera_topic", "/camera/left/image_raw") if self.stereo_swap_lr else rospy.get_param("~native_camera_topic", "/camera/right/image_raw"),
            rospy.get_param("~native_camera_topic", "/camera/right/image_raw") if self.stereo_swap_lr else rospy.get_param("~native_left_camera_topic", "/camera/left/image_raw"),
            mono_camera_topic or "disabled",
        )

    def _parse_float_list_param(self, name, default):
        value = rospy.get_param(name, "")
        if value in ("", None):
            return list(default)
        if isinstance(value, (list, tuple)):
            return [float(v) for v in value]
        try:
            parsed = ast.literal_eval(str(value))
            if isinstance(parsed, (list, tuple)):
                return [float(v) for v in parsed]
        except Exception:
            pass
        try:
            return [float(v) for v in str(value).replace(",", " ").split()]
        except Exception:
            rospy.logwarn("[CustomFastLioAdapter] invalid %s=%r; using default", name, value)
            return list(default)

    def _camera_model_from_params(self, side, default_k, default_d):
        k = self._parse_float_list_param("~camera_{}_k".format(side), default_k)
        d = self._parse_float_list_param("~camera_{}_d".format(side), default_d)
        if len(k) != 9:
            rospy.logwarn("[CustomFastLioAdapter] camera_%s_k must have 9 values; using default", side)
            k = list(default_k)
        if len(d) < 5:
            d = list(d) + [0.0] * (5 - len(d))
        return {"K": k, "D": d[:5]}

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
            self.publish_lidar_outputs(out)
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
        self.publish_lidar_outputs(out)

    def publish_lidar_outputs(self, cloud):
        """Publish the standard PointCloud2 output and, when requested, a Livox CustomMsg clone.

        FAST-LIO2/FAST-LIO consume PointCloud2, but upstream R3LIVE and the original
        FAST-LIVO commonly subscribe to livox_ros_driver/CustomMsg. Publishing both
        avoids putting two different ROS message types on the same topic: RViz still
        sees PointCloud2 on /livox/lidar, while R3LIVE/FAST-LIVO subscribe to
        /livox/lidar_custom.
        """
        out = self.drop_nan_points_if_needed(cloud)
        out = self.add_ring_field_if_needed(out)
        out = self.scale_point_time_if_needed(out)
        if self.add_normal_fields:
            out = self.pointcloud2_to_xyzinormal_cloud(out)
        self.lidar_pub.publish(out)
        if self.publish_livox_custom_msg and self.livox_custom_pub is not None:
            self.livox_custom_pub.publish(self.pointcloud2_to_livox_custom(out))

    def drop_nan_points_if_needed(self, cloud):
        if not self.drop_nan_points or cloud.is_dense:
            return cloud

        field_names = [field.name for field in cloud.fields]
        if not all(name in field_names for name in ("x", "y", "z")):
            rospy.logwarn_throttle(5.0, "[CustomFastLioAdapter] cannot drop NaN points; cloud has no x/y/z fields")
            return cloud

        point_count = int(cloud.width) * int(cloud.height)
        points = list(pc2.read_points(cloud, field_names=field_names, skip_nans=True))
        if not points:
            rospy.logwarn_throttle(5.0, "[CustomFastLioAdapter] dropping non-dense PointCloud2 produced an empty cloud")
            return cloud

        out = pc2.create_cloud(cloud.header, cloud.fields, points)
        out.is_dense = True
        if not self._nan_filter_logged or len(points) != point_count:
            dropped = max(0, point_count - len(points))
            rospy.loginfo(
                "[CustomFastLioAdapter] filtered non-dense PointCloud2: kept=%d dropped=%d",
                len(points),
                dropped,
            )
            self._nan_filter_logged = True
        return out

    def add_ring_field_if_needed(self, cloud):
        field_names = [field.name for field in cloud.fields]
        if "ring" in field_names or self.ring_count <= 0:
            return cloud
        if not all(name in field_names for name in ("x", "y", "z")):
            rospy.logwarn_throttle(5.0, "[CustomFastLioAdapter] cannot synthesize ring; cloud has no x/y/z fields")
            return cloud

        read_fields = [name for name in ("x", "y", "z", "intensity", "time") if name in field_names]
        idx = {name: i for i, name in enumerate(read_fields)}
        points = []
        for pt in pc2.read_points(cloud, field_names=read_fields, skip_nans=True):
            x = float(pt[idx["x"]])
            y = float(pt[idx["y"]])
            z = float(pt[idx["z"]])
            intensity = float(pt[idx["intensity"]]) if "intensity" in idx else 0.0
            rel_time = float(pt[idx["time"]]) if "time" in idx else 0.0
            ring = self.estimate_ring_from_xyz(x, y, z)
            points.append((x, y, z, intensity, ring, rel_time))

        if not points:
            rospy.logwarn_throttle(5.0, "[CustomFastLioAdapter] ring synthesis produced an empty cloud")
            return cloud

        fields = [
            PointField("x", 0, PointField.FLOAT32, 1),
            PointField("y", 4, PointField.FLOAT32, 1),
            PointField("z", 8, PointField.FLOAT32, 1),
            PointField("intensity", 12, PointField.FLOAT32, 1),
            PointField("ring", 16, PointField.UINT16, 1),
            PointField("time", 20, PointField.FLOAT32, 1),
        ]
        out = pc2.create_cloud(cloud.header, fields, points)
        out.is_dense = True
        if not self._ring_synthesis_logged:
            rospy.loginfo(
                "[CustomFastLioAdapter] synthesized Velodyne ring field for %d-scan cloud points=%d",
                self.ring_count,
                len(points),
            )
            self._ring_synthesis_logged = True
        return out

    def estimate_ring_from_xyz(self, x, y, z):
        xy = math.hypot(x, y)
        if xy <= 1e-6:
            return 0
        vertical_deg = math.degrees(math.atan2(z, xy))
        if self.ring_count == 16:
            min_deg, max_deg = -15.0, 15.0
        else:
            min_deg, max_deg = -30.0, 10.0
        ratio = (vertical_deg - min_deg) / max(1e-6, max_deg - min_deg)
        return int(max(0, min(self.ring_count - 1, round(ratio * (self.ring_count - 1)))))

    def pointcloud2_to_xyzinormal_cloud(self, cloud):
        """Return a PCL-layout PointXYZINormal PointCloud2 for native R3LIVE.

        R3LIVE's r3live_mapping subscribes to sensor_msgs/PointCloud2, but its
        LiDAR parser reads the message as PCL PointXYZINormal.  The previous
        bridge added normal_x/normal_y/normal_z/curvature fields but packed them
        in a compact 38-byte custom layout and kept extra time/ring fields.  That
        layout is legal ROS PointCloud2, but it is not the memory layout used by
        PCL PointXYZINormal, so R3LIVE printed:

            Get pointcloud data from ros messages fail!!!

        Build the cloud in the canonical 48-byte PCL PointXYZINormal layout:

            x,y,z,pad, normal_x,normal_y,normal_z,pad, intensity,curvature,pad,pad

        The ROS PointField list is intentionally ordered as:
            x,y,z,intensity,normal_x,normal_y,normal_z,curvature
        because upstream R3LIVE rejects PointCloud2 messages unless field[3] is
        intensity and field[4] is normal_x.

        Curvature carries the relative point time because R3LIVE/FAST-LIO code
        sorts points by point.curvature for scan undistortion.  We intentionally
        do not add separate `time` or `ring` fields on the R3LIVE topic because
        the upstream parser is stricter than RViz/PCL utilities.
        """
        field_names = [f.name for f in cloud.fields]
        read_fields = [n for n in ("x", "y", "z", "intensity", "time") if n in field_names]
        if not all(k in read_fields for k in ("x", "y", "z")):
            rospy.logwarn_throttle(5.0, "[CustomFastLioAdapter] add_normal_fields requested but x/y/z missing")
            return cloud

        idx = {name: i for i, name in enumerate(read_fields)}
        raw = bytearray()
        count = 0
        pack = struct.Struct("<12f" if not cloud.is_bigendian else ">12f")
        for pt in pc2.read_points(cloud, field_names=read_fields, skip_nans=True):
            x = float(pt[idx["x"]])
            y = float(pt[idx["y"]])
            z = float(pt[idx["z"]])
            intensity = float(pt[idx["intensity"]]) if "intensity" in idx else 0.0
            rel_time = float(pt[idx["time"]]) if "time" in idx else 0.0
            curvature = rel_time if self.curvature_from_time else 0.0
            raw.extend(pack.pack(
                x, y, z, 1.0,          # PCL_ADD_POINT4D padding
                0.0, 0.0, 0.0, 0.0,    # PCL_ADD_NORMAL4D padding
                intensity, curvature, 0.0, 0.0,
            ))
            count += 1

        out = PointCloud2()
        out.header = cloud.header
        out.height = 1
        out.width = count
        # R3LIVE does an extra brittle check before pcl::fromROSMsg():
        # it requires exactly 8 fields and specifically expects
        # fields[3] == "intensity" and fields[4] == "normal_x".
        # Keep PCL PointXYZINormal byte offsets, but order the fields the way
        # upstream R3LIVE checks them.
        out.fields = [
            PointField("x", 0, PointField.FLOAT32, 1),
            PointField("y", 4, PointField.FLOAT32, 1),
            PointField("z", 8, PointField.FLOAT32, 1),
            PointField("intensity", 32, PointField.FLOAT32, 1),
            PointField("normal_x", 16, PointField.FLOAT32, 1),
            PointField("normal_y", 20, PointField.FLOAT32, 1),
            PointField("normal_z", 24, PointField.FLOAT32, 1),
            PointField("curvature", 36, PointField.FLOAT32, 1),
        ]
        out.is_bigendian = cloud.is_bigendian
        out.point_step = 48
        out.row_step = out.point_step * out.width
        out.data = bytes(raw)
        out.is_dense = True
        return out

    def pointcloud2_to_livox_custom(self, cloud):
        msg = LivoxCustomMsg()
        msg.header = patched_header(cloud.header, "velodyne")
        # livox_ros_driver CustomMsg uses nanosecond timebase and uint32 ns offsets.
        msg.timebase = int(cloud.header.stamp.to_nsec())
        msg.lidar_id = 1
        msg.rsvd = [0, 0, 0]

        field_names = [f.name for f in cloud.fields]
        read_fields = [n for n in ("x", "y", "z", "intensity", "ring", "time") if n in field_names]
        idx = {name: i for i, name in enumerate(read_fields)}
        points = []
        for p in pc2.read_points(cloud, field_names=read_fields, skip_nans=True):
            pt = LivoxCustomPoint()
            pt.x = float(p[idx["x"]])
            pt.y = float(p[idx["y"]])
            pt.z = float(p[idx["z"]])
            intensity = float(p[idx["intensity"]]) if "intensity" in idx else 0.0
            pt.reflectivity = int(max(0, min(255, round(intensity))))
            pt.tag = 0
            pt.line = int(max(0, min(255, int(p[idx["ring"]])))) if "ring" in idx else 0
            if "time" in idx:
                # UrbanNav Velodyne time is relative seconds inside scan. Livox CustomPoint
                # offset_time is uint32 nanoseconds relative to CustomMsg.timebase.
                pt.offset_time = int(max(0, min(4294967295, round(float(p[idx["time"]]) * 1.0e9))))
            else:
                pt.offset_time = 0
            points.append(pt)
        msg.points = points
        msg.point_num = len(points)
        return msg

    def scale_point_time_if_needed(self, cloud):
        """Scale Velodyne per-point relative time exactly once when required.

        UrbanNav stores the PointCloud2 FLOAT32 `time` field in seconds. FAST-LIVO2,
        FAST-LIVO, and R3LIVE Velodyne readers expect microseconds, so their registry
        entries set point_time_scale=1e6. This function samples the incoming field first and
        only scales when it still looks seconds-like (<=1.0). If another bridge has
        already converted to microseconds, the values are larger and are forwarded
        unchanged to avoid nanosecond-level double scaling.
        """
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
                self._point_time_convert = False
            else:
                data = cloud.data
                point_count = cloud.width * cloud.height
                samples = []
                if point_count > 0:
                    step = max(1, point_count // 32)
                    for idx in range(0, point_count, step):
                        off = idx * cloud.point_step + self._point_time_offset
                        if off + 4 > len(data):
                            break
                        samples.append(abs(self._point_time_struct.unpack_from(data, off)[0]))
                        if len(samples) >= 32:
                            break
                max_sample = max(samples) if samples else 0.0
                self._point_time_convert = max_sample <= 1.0
                if self._point_time_convert:
                    rospy.loginfo(
                        "[CustomFastLioAdapter] Converting Velodyne point time seconds -> target units by scale %.3g (max sample %.6g)",
                        self.point_time_scale,
                        max_sample,
                    )
                else:
                    rospy.loginfo(
                        "[CustomFastLioAdapter] Point time already appears converted (max sample %.6g); not applying scale %.3g",
                        max_sample,
                        self.point_time_scale,
                    )
        if self._point_time_offset is None or not self._point_time_convert:
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
        # Physical RIGHT camera. In ORB-SLAM3 stereo mode the UrbanNav/ZED2
        # pair must be swapped so ORB receives positive disparity:
        #   physical right -> /camera/left/image_raw
        #   physical left  -> /camera/right/image_raw
        # The mono alias must still remain the physical right camera.
        if self.stereo_swap_lr:
            self._camera_common_cb(
                msg=msg,
                sensor_name="camera_right",
                publish_enabled=self.publish_left_camera,
                frame_id=self.left_camera_frame_id,
                image_pub=self.left_camera_pub,
                info_pub=self.left_camera_info_pub,
                intrinsics="right",
                publish_mono=True,
                mono_frame_id=self.camera_frame_id,
            )
        else:
            self._camera_common_cb(
                msg=msg,
                sensor_name="camera_right",
                publish_enabled=self.publish_camera,
                frame_id=self.camera_frame_id,
                image_pub=self.camera_pub,
                info_pub=self.camera_info_pub,
                intrinsics="right",
                publish_mono=True,
                mono_frame_id=self.camera_frame_id,
            )

    def left_camera_cb(self, msg):
        # Physical LEFT camera. Swap only the stereo outputs; perturbations for
        # camera_right are intentionally reused as fallback so per_*.yaml camera
        # scenarios affect both images.
        if self.stereo_swap_lr:
            self._camera_common_cb(
                msg=msg,
                sensor_name="camera_left",
                publish_enabled=self.publish_camera,
                frame_id=self.camera_frame_id,
                image_pub=self.camera_pub,
                info_pub=self.camera_info_pub,
                intrinsics="left",
                fallback_sensor_name="camera_right",
            )
        else:
            self._camera_common_cb(
                msg=msg,
                sensor_name="camera_left",
                publish_enabled=self.publish_left_camera,
                frame_id=self.left_camera_frame_id,
                image_pub=self.left_camera_pub,
                info_pub=self.left_camera_info_pub,
                intrinsics="left",
                fallback_sensor_name="camera_right",
            )

    def _camera_common_cb(self, msg, sensor_name, publish_enabled, frame_id, image_pub, info_pub, intrinsics, fallback_sensor_name=None, publish_mono=False, mono_frame_id=None):
        if not publish_enabled:
            return
        stamp = msg.header.stamp.to_sec()
        active = self.config.active_for(sensor_name, stamp)
        if not active and fallback_sensor_name:
            # The existing perturbation files name the camera stream camera_right.
            # For stereo ORB-SLAM3, apply the same windows to the left stream too.
            active = self.config.active_for(fallback_sensor_name, stamp)
        if not active:
            out = image_with_header(msg.image, patched_header(msg.header, frame_id))
            image_pub.publish(out)
            if publish_mono and self.mono_camera_pub is not None:
                mono_header = patched_header(msg.header, mono_frame_id or frame_id)
                self.mono_camera_pub.publish(image_with_header(out, mono_header))
            self.publish_cam_info(out.header, out.width, out.height, info_pub, intrinsics)
            return

        out = copy.deepcopy(msg.image)
        out.header = patched_header(msg.header, frame_id)
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
        image_pub.publish(out)
        if publish_mono and self.mono_camera_pub is not None:
            mono_header = patched_header(msg.header, mono_frame_id or frame_id)
            self.mono_camera_pub.publish(image_with_header(out, mono_header))
        self.publish_cam_info(out.header, out.width, out.height, info_pub, intrinsics)

    def publish_cam_info(self, header, width, height, pub=None, intrinsics="right"):
        if not self.publish_camera_info:
            return
        if pub is None:
            pub = self.camera_info_pub
        info = CameraInfo()
        info.header = header
        info.width = width or 672
        info.height = height or 376
        info.distortion_model = "plumb_bob"
        model = self.camera_models.get(intrinsics, self.camera_models["right"])
        info.D = model["D"]
        info.K = model["K"]
        info.R = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        info.P = [info.K[0], 0.0, info.K[2], 0.0, 0.0, info.K[4], info.K[5], 0.0, 0.0, 0.0, 1.0, 0.0]
        pub.publish(info)

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
