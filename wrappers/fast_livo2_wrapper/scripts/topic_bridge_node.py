#!/usr/bin/env python3
"""
topic_bridge_node.py
====================
Black-box wrapper: bridges UrbanNav rosbag sensor topics → FAST-LIVO2.

FAST-LIVO2 is a tightly-coupled LiDAR-IMU-Visual odometry system
(github: hku-mars/FAST-LIVO2). This node treats it as an opaque
binary — zero modifications to its source code.

Topic Mapping  (rosbag → FAST-LIVO2)
─────────────────────────────────────────────────────────────────────────
  SOURCE (UrbanNav rosbag)                   TARGET (FAST-LIVO2 config)
  ────────────────────────────────────────   ────────────────────────────
  /velodyne_points        (PointCloud2)   →  /livox/lidar
  /imu/data               (Imu)           →  /livox/imu
  /zed2/camera/right/image_raw (Image)    →  /camera/right/image_raw

Frame-ID patching
─────────────────────────────────────────────────────────────────────────
  Input frame_id            →  FAST-LIVO2 frame_id
  ──────────────────────        ──────────────────
  velodyne / laser_link     →  velodyne        (centre LiDAR)
  imu_link / xsens / *      →  body            (IMU = body frame)
  camera_right / zed2_*     →  camera_right    (ZED2 right camera)

Timestamps are NEVER modified — FAST-LIVO2 relies on precise hardware
timestamps for LiDAR motion-distortion correction and IMU integration.

Sensor geometry/intensity/ring fields, IMU measurements, image pixels, and
message timestamps are forwarded without filtering, interpolation, or
synthetic data generation. The Velodyne per-point ``time`` field is normalized
from UrbanNav seconds to FAST-LIVO2's expected microseconds when detected.

Forbidden forwarding:
  GPS / GNSS / RTK, ground truth, wheel odometry, external maps.

Diagnostics: logs per-stream message rates every 5 seconds.
"""

import threading
import struct
import rospy
from sensor_msgs.msg import PointCloud2, PointField, Imu, Image
from std_msgs.msg import Header

# ─── Default topic names ───────────────────────────────────────────────────────
# Override via ROS params or launch file arguments.

# Input (UrbanNav rosbag topics)
DEFAULT_LIDAR_IN  = "/velodyne_points"
DEFAULT_IMU_IN    = "/imu/data"
DEFAULT_CAM_IN    = "/zed2/camera/right/image_raw"

# Output (FAST-LIVO2 expected topics — defined in fast_livo2_urbannav.yaml)
DEFAULT_LIDAR_OUT = "/livox/lidar"
DEFAULT_IMU_OUT   = "/livox/imu"
DEFAULT_CAM_OUT   = "/camera/right/image_raw"

# Frame IDs that FAST-LIVO2 expects (must match config YAML + TF tree)
DEFAULT_LIDAR_FRAME = "velodyne"
DEFAULT_IMU_FRAME   = "body"
DEFAULT_CAM_FRAME   = "camera_right"

QUEUE_SIZE = 100


# ─── Utility ──────────────────────────────────────────────────────────────────

def _make_header(original: Header, new_frame_id: str) -> Header:
    """Return a new Header preserving the original timestamp and sequence
    number but with a different frame_id.

    CRITICAL: Timestamps are never modified. FAST-LIVO2 relies on precise,
    monotone hardware timestamps for:
      - IMU pre-integration between LiDAR scans
      - LiDAR motion-distortion correction using the per-point time field
      - Visual-inertial temporal calibration
    """
    h = Header()
    h.seq      = original.seq
    h.stamp    = original.stamp   # hardware timestamp — preserved exactly
    h.frame_id = new_frame_id
    return h


# ─── Per-stream bridge classes ─────────────────────────────────────────────────

class LidarBridge:
    """
    Subscribes to /velodyne_points (Velodyne VLP-16 PointCloud2) and
    republishes on /livox/lidar — the topic FAST-LIVO2 subscribes to.

    The Velodyne VLP-16 produces fields: x, y, z, intensity, ring, time.
    FAST-LIVO2 (preprocess.lidar_type=2, Velodyne) uses:
      - x, y, z        — 3D position
      - ring           — scan line index for scan-line segmentation
      - time           — per-point relative timestamp for motion distortion
    Geometry/intensity/ring fields are forwarded unchanged. Only header.frame_id
    and, when needed, the units of the per-point time field are patched to match
    FAST-LIVO2's native Velodyne parser.
    """

    def __init__(self, topic_in: str, topic_out: str, frame_id: str):
        self._frame_id = frame_id
        self._pub      = rospy.Publisher(topic_out, PointCloud2, queue_size=QUEUE_SIZE)
        self._sub      = rospy.Subscriber(topic_in,  PointCloud2, self._cb, queue_size=QUEUE_SIZE)
        self._lock     = threading.Lock()
        self._time_field_offset = None
        self._time_struct = None
        self._convert_time_sec_to_usec = None
        self.count     = 0
        rospy.loginfo("[LidarBridge] %s  →  %s  (frame: %s)", topic_in, topic_out, frame_id)

    def _prepare_time_conversion(self, msg: PointCloud2):
        """Detect UrbanNav's seconds-based Velodyne time field.

        Native FAST-LIVO2's Velodyne parser divides point.time by 1000 to get
        milliseconds, so it expects the incoming time field in microseconds.
        UrbanNav stores seconds in /velodyne_points. Convert only that field.
        """
        for field in msg.fields:
            if field.name == "time" and field.datatype == PointField.FLOAT32:
                self._time_field_offset = field.offset
                self._time_struct = struct.Struct(">f" if msg.is_bigendian else "<f")
                break

        if self._time_field_offset is None or msg.point_step <= self._time_field_offset:
            self._convert_time_sec_to_usec = False
            rospy.logwarn("[LidarBridge] No FLOAT32 time field found; forwarding point times unchanged.")
            return

        point_count = msg.width * msg.height
        sample_indices = [0, max(0, point_count // 2), max(0, point_count - 1)]
        values = []
        for idx in sample_indices:
            off = idx * msg.point_step + self._time_field_offset
            if off + 4 <= len(msg.data):
                values.append(abs(self._time_struct.unpack_from(msg.data, off)[0]))

        max_sample = max(values) if values else 0.0
        self._convert_time_sec_to_usec = max_sample <= 1.0
        if self._convert_time_sec_to_usec:
            rospy.loginfo("[LidarBridge] Converting Velodyne point time seconds → microseconds for FAST-LIVO2.")
        else:
            rospy.loginfo("[LidarBridge] Point time field already looks FAST-LIVO2-compatible; forwarding unchanged.")

    def _normalize_point_time(self, msg: PointCloud2):
        if self._convert_time_sec_to_usec is None:
            self._prepare_time_conversion(msg)
        if not self._convert_time_sec_to_usec:
            return msg.data

        data = bytearray(msg.data)
        point_count = msg.width * msg.height
        for idx in range(point_count):
            off = idx * msg.point_step + self._time_field_offset
            if off + 4 > len(data):
                break
            t_sec = self._time_struct.unpack_from(data, off)[0]
            self._time_struct.pack_into(data, off, t_sec * 1.0e6)
        return bytes(data)

    def _cb(self, msg: PointCloud2):
        with self._lock:
            out              = PointCloud2()
            out.header       = _make_header(msg.header, self._frame_id)
            out.height       = msg.height
            out.width        = msg.width
            out.fields       = msg.fields       # all Velodyne fields (x,y,z,intensity,ring,time)
            out.is_bigendian = msg.is_bigendian
            out.point_step   = msg.point_step
            out.row_step     = msg.row_step
            out.data         = self._normalize_point_time(msg)
            out.is_dense     = msg.is_dense
            self._pub.publish(out)
            self.count += 1
            if self.count % 50 == 0:
                rospy.logdebug("[LidarBridge] forwarded %d clouds  t=%.3f",
                               self.count, msg.header.stamp.to_sec())


class ImuBridge:
    """
    Bridges /imu/data (Xsens MTi-G-710) → /livox/imu.

    FAST-LIVO2 uses angular_velocity and linear_acceleration for IMU
    pre-integration in its ESIKF state estimator. The orientation quaternion
    and all covariance matrices are forwarded unchanged.

    The Xsens MTi-G-710 outputs at 200 Hz with hardware-stamped messages;
    the IMU noise parameters in the YAML (acc_cov, gyr_cov, b_acc_cov,
    b_gyr_cov) are calibrated to these specific sensor characteristics.

    No unit conversion is performed — FAST-LIVO2 expects SI units:
      angular_velocity:     rad/s
      linear_acceleration:  m/s²
    (Xsens MTi-G-710 outputs natively in SI units.)
    """

    def __init__(self, topic_in: str, topic_out: str, frame_id: str):
        self._frame_id = frame_id
        self._pub      = rospy.Publisher(topic_out, Imu, queue_size=QUEUE_SIZE)
        self._sub      = rospy.Subscriber(topic_in,  Imu, self._cb, queue_size=QUEUE_SIZE)
        self._lock     = threading.Lock()
        self.count     = 0
        rospy.loginfo("[ImuBridge] %s  →  %s  (frame: %s)", topic_in, topic_out, frame_id)

    def _cb(self, msg: Imu):
        with self._lock:
            out                                = Imu()
            out.header                         = _make_header(msg.header, self._frame_id)
            # Measurements — forwarded verbatim, no unit conversion
            out.orientation                    = msg.orientation
            out.orientation_covariance         = msg.orientation_covariance
            out.angular_velocity               = msg.angular_velocity
            out.angular_velocity_covariance    = msg.angular_velocity_covariance
            out.linear_acceleration            = msg.linear_acceleration
            out.linear_acceleration_covariance = msg.linear_acceleration_covariance
            self._pub.publish(out)
            self.count += 1
            if self.count % 200 == 0:
                rospy.logdebug("[ImuBridge] forwarded %d msgs  t=%.3f",
                               self.count, msg.header.stamp.to_sec())


class CameraBridge:
    """
    Bridges /zed2/camera/right/image_raw → /camera/right/image_raw.

    FAST-LIVO2 uses the right camera image for visual feature tracking and
    LiDAR-camera extrinsic calibration refinement. The image encoding,
    dimensions, and pixel data are forwarded unchanged; only frame_id is
    patched so RViz can display the image on the correct TF frame.

    ZED2 right camera characteristics:
      Resolution:  672 × 376 px
      Encoding:    bgr8 or 8UC1 (grayscale)
      Frame rate:  ~10 Hz in UrbanNav bag
    """

    def __init__(self, topic_in: str, topic_out: str, frame_id: str):
        self._frame_id = frame_id
        self._pub      = rospy.Publisher(topic_out, Image, queue_size=30)
        self._sub      = rospy.Subscriber(topic_in,  Image, self._cb, queue_size=30)
        self.count     = 0
        rospy.loginfo("[CameraBridge] %s  →  %s  (frame: %s)", topic_in, topic_out, frame_id)

    def _cb(self, msg: Image):
        out              = Image()
        out.header       = _make_header(msg.header, self._frame_id)
        out.height       = msg.height
        out.width        = msg.width
        out.encoding     = msg.encoding     # raw encoding preserved (bgr8/8UC1/etc.)
        out.is_bigendian = msg.is_bigendian
        out.step         = msg.step
        out.data         = msg.data         # pixel bytes verbatim
        self._pub.publish(out)
        self.count += 1
        if self.count % 30 == 0:
            rospy.logdebug("[CameraBridge] forwarded %d images  t=%.3f",
                           self.count, msg.header.stamp.to_sec())


# ─── Diagnostics ──────────────────────────────────────────────────────────────

class DiagnosticsTimer:
    """Logs per-stream message rates every ``period`` seconds."""

    def __init__(self, streams: dict, period: float = 5.0):
        self._streams     = streams
        self._last_counts = {k: 0 for k in streams}
        self._period      = period
        self._timer       = rospy.Timer(rospy.Duration(period), self._report)

    def _report(self, _event):
        lines = ["[TopicBridge Diagnostics]"]
        for name, stream in self._streams.items():
            curr   = stream.count
            delta  = curr - self._last_counts[name]
            hz     = delta / self._period
            self._last_counts[name] = curr
            status = "OK" if hz > 0 else "NO DATA"
            lines.append(
                f"  {name:<20s}: total={curr:6d}  rate={hz:6.1f} Hz  [{status}]"
            )
        rospy.loginfo("\n".join(lines))


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    rospy.init_node("topic_bridge_node", anonymous=False, log_level=rospy.INFO)

    # ── Read parameters ────────────────────────────────────────────────────────
    lidar_in    = rospy.get_param("~lidar_topic_in",   DEFAULT_LIDAR_IN)
    imu_in      = rospy.get_param("~imu_topic_in",     DEFAULT_IMU_IN)
    cam_in      = rospy.get_param("~cam_topic_in",     DEFAULT_CAM_IN)

    lidar_out   = rospy.get_param("~lidar_topic_out",  DEFAULT_LIDAR_OUT)
    imu_out     = rospy.get_param("~imu_topic_out",    DEFAULT_IMU_OUT)
    cam_out     = rospy.get_param("~cam_topic_out",    DEFAULT_CAM_OUT)

    lidar_frame = rospy.get_param("~lidar_frame_id",   DEFAULT_LIDAR_FRAME)
    imu_frame   = rospy.get_param("~imu_frame_id",     DEFAULT_IMU_FRAME)
    cam_frame   = rospy.get_param("~cam_frame_id",     DEFAULT_CAM_FRAME)

    # ── Create bridges ─────────────────────────────────────────────────────────
    lidar_bridge  = LidarBridge(lidar_in,  lidar_out,  lidar_frame)
    imu_bridge    = ImuBridge(imu_in,      imu_out,    imu_frame)
    camera_bridge = CameraBridge(cam_in,   cam_out,    cam_frame)

    # ── Start diagnostics ──────────────────────────────────────────────────────
    DiagnosticsTimer({
        "LiDAR":  lidar_bridge,
        "IMU":    imu_bridge,
        "Camera": camera_bridge,
    })

    rospy.loginfo(
        "\n"
        "══════════════════════════════════════════════════════════════\n"
        "  FAST-LIVO2 Topic Bridge  ·  ACTIVE\n"
        "══════════════════════════════════════════════════════════════\n"
        "  Stream     Input topic                   → Output topic\n"
        "  ─────────  ─────────────────────────────   ────────────────\n"
        "  LiDAR      %-35s → %s\n"
        "  IMU        %-35s → %s\n"
        "  Camera     %-35s → %s\n"
        "══════════════════════════════════════════════════════════════",
        lidar_in, lidar_out,
        imu_in,   imu_out,
        cam_in,   cam_out,
    )

    rospy.spin()


if __name__ == "__main__":
    main()
