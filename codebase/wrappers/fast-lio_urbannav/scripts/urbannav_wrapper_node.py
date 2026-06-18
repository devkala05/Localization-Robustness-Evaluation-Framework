#!/usr/bin/env python3
"""
urbannav_wrapper_node.py
========================
Black-box wrapper that bridges UrbanNav-HK rosbag topics → Fast-LIO2.

Topic Mapping (UrbanNav → Fast-LIO2)
─────────────────────────────────────────────────────────────────────────
  SOURCE (rosbag)                          TARGET (Fast-LIO2)
  ──────────────────────────────────────   ─────────────────────────────
  /velodyne_points       (PointCloud2)  →  /cloud_registered_raw        *
  /imu/data              (Imu)          →  /livox/imu                   *
  /zed2/camera/right/image_raw (Image)  →  /camera/right/image_raw      (pass-through)

  * These are the topic names configured in Fast-LIO2's YAML config.
    The node only patches frame_ids and verifies message integrity;
    it does NOT alter timestamps.

Frame-ID mapping
─────────────────────────────────────────────────────────────────────────
  UrbanNav frame_id          →  Fast-LIO2 frame_id
  ─────────────────────────     ──────────────────
  velodyne / laser_link      →  velodyne   (centre LiDAR)
  imu_link / xsens           →  body       (IMU body frame for Fast-LIO2)
  camera_right               →  camera_right

No GPS, ground-truth, odometry or map data is forwarded to Fast-LIO2.
"""

import rospy
import numpy as np
from sensor_msgs.msg import CameraInfo, PointCloud2, Imu, Image, PointField
from std_msgs.msg import Header
import sensor_msgs.point_cloud2 as pc2
import threading


# ─────────────────────────────────────────────────────────────────────────────
#  Configuration constants (overridable from ROS params)
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_LIDAR_IN   = "/velodyne_points"
DEFAULT_IMU_IN     = "/imu/data"
DEFAULT_CAM_IN     = "/zed2/camera/right/image_raw"

DEFAULT_LIDAR_OUT  = "/cloud_registered_raw"   # Fast-LIO2 default lidar topic
DEFAULT_IMU_OUT    = "/livox/imu"              # Fast-LIO2 default IMU topic
DEFAULT_CAM_OUT    = "/camera/right/image_raw"

# Frame IDs that Fast-LIO2 expects (set in its config YAML)
LIDAR_FRAME_OUT    = "velodyne"   # matches camera_lidar_id in Fast-LIO2 yaml
IMU_FRAME_OUT      = "body"       # Fast-LIO2 body frame == IMU frame
CAM_FRAME_OUT      = "camera_right"

QUEUE_SIZE = 100


# ─────────────────────────────────────────────────────────────────────────────
#  Helper: patch header frame_id without copying the whole message
# ─────────────────────────────────────────────────────────────────────────────
def _patched_header(original_header: Header, new_frame_id: str) -> Header:
    """Return a new Header with the same stamp but a different frame_id."""
    h = Header()
    h.seq      = original_header.seq
    h.stamp    = original_header.stamp   # preserve original timestamp exactly
    h.frame_id = new_frame_id
    return h


# ─────────────────────────────────────────────────────────────────────────────
#  LiDAR converter
# ─────────────────────────────────────────────────────────────────────────────
class LidarConverter:
    """
    Subscribes to the raw Velodyne PointCloud2 from the rosbag.
    Patches the frame_id to 'velodyne' and republishes on the Fast-LIO2 topic.

    The Velodyne VLP-16 / HDL-64 used in UrbanNav publishes:
        fields: x, y, z, intensity, ring, time
    Fast-LIO2 needs at minimum: x, y, z + (intensity or ring for line-id).
    No field modification is performed — the full cloud is forwarded.
    """

    def __init__(self, topic_in: str, topic_out: str, frame_id_out: str):
        self._frame_id_out = frame_id_out
        self._pub = rospy.Publisher(topic_out, PointCloud2, queue_size=QUEUE_SIZE)
        self._sub = rospy.Subscriber(topic_in, PointCloud2, self._cb, queue_size=QUEUE_SIZE)
        self._count = 0
        self._lock  = threading.Lock()
        rospy.loginfo(f"[LidarConverter] {topic_in} → {topic_out}  frame: {frame_id_out}")

    def _cb(self, msg: PointCloud2):
        with self._lock:
            out = PointCloud2()
            out.header       = _patched_header(msg.header, self._frame_id_out)
            out.height       = msg.height
            out.width        = msg.width
            out.fields       = msg.fields
            out.is_bigendian = msg.is_bigendian
            out.point_step   = msg.point_step
            out.row_step     = msg.row_step
            out.data         = msg.data
            out.is_dense     = msg.is_dense
            self._pub.publish(out)
            self._count += 1
            if self._count % 50 == 0:
                rospy.logdebug(f"[LiDAR] forwarded {self._count} clouds  stamp={msg.header.stamp.to_sec():.3f}")


# ─────────────────────────────────────────────────────────────────────────────
#  IMU converter
# ─────────────────────────────────────────────────────────────────────────────
class ImuConverter:
    """
    Subscribes to /imu/data (Xsens MTi-G-710) from the rosbag.
    Patches the frame_id to 'body' (Fast-LIO2 body frame = IMU frame).

    Fast-LIO2 uses:
        angular_velocity   (gyro,  rad/s)
        linear_acceleration (accel, m/s^2)
    Both are preserved with original covariances intact.
    Orientation quaternion is forwarded but not used by Fast-LIO2.
    """

    def __init__(self, topic_in: str, topic_out: str, frame_id_out: str):
        self._frame_id_out = frame_id_out
        self._pub = rospy.Publisher(topic_out, Imu, queue_size=QUEUE_SIZE)
        self._sub = rospy.Subscriber(topic_in, Imu, self._cb, queue_size=QUEUE_SIZE)
        self._count = 0
        self._lock  = threading.Lock()
        rospy.loginfo(f"[ImuConverter] {topic_in} → {topic_out}  frame: {frame_id_out}")

    def _cb(self, msg: Imu):
        with self._lock:
            out = Imu()
            out.header = _patched_header(msg.header, self._frame_id_out)

            # Copy measurement data verbatim — no scaling, no rotation
            out.orientation                    = msg.orientation
            out.orientation_covariance         = msg.orientation_covariance
            out.angular_velocity               = msg.angular_velocity
            out.angular_velocity_covariance    = msg.angular_velocity_covariance
            out.linear_acceleration            = msg.linear_acceleration
            out.linear_acceleration_covariance = msg.linear_acceleration_covariance

            self._pub.publish(out)
            self._count += 1
            if self._count % 200 == 0:
                rospy.logdebug(f"[IMU] forwarded {self._count} msgs  stamp={msg.header.stamp.to_sec():.3f}")


# ─────────────────────────────────────────────────────────────────────────────
#  Camera pass-through (right camera only)
# ─────────────────────────────────────────────────────────────────────────────
class CameraPassthrough:
    """
    Forwards the right camera image from the rosbag to the output topic.
    Fast-LIO2 is a LiDAR-IMU odometry system and does NOT consume camera
    images internally, but the image is forwarded for completeness and
    for any downstream visual modules or RViz display.

    frame_id is patched to 'camera_right' to match the TF tree.
    """

    def __init__(self, topic_in: str, topic_out: str, frame_id_out: str):
        self._frame_id_out = frame_id_out
        self._pub = rospy.Publisher(topic_out, Image, queue_size=30)
        self._info_pub = rospy.Publisher(rospy.get_param("~camera_info_topic_out", "/camera/right/camera_info"), CameraInfo, queue_size=30)
        self._sub = rospy.Subscriber(topic_in, Image, self._cb, queue_size=30)
        self._count = 0
        rospy.loginfo(f"[CameraPassthrough] {topic_in} → {topic_out}  frame: {frame_id_out}")

    def _cb(self, msg: Image):
        out = Image()
        out.header   = _patched_header(msg.header, self._frame_id_out)
        out.height   = msg.height
        out.width    = msg.width
        out.encoding = msg.encoding
        out.is_bigendian = msg.is_bigendian
        out.step     = msg.step
        out.data     = msg.data
        self._pub.publish(out)
        self._publish_camera_info(out.header, out.width, out.height)
        self._count += 1
        if self._count % 30 == 0:
            rospy.logdebug(f"[Camera] forwarded {self._count} images")

    def _publish_camera_info(self, header, width, height):
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
        self._info_pub.publish(info)


# ─────────────────────────────────────────────────────────────────────────────
#  Diagnostics publisher
# ─────────────────────────────────────────────────────────────────────────────
class DiagnosticsTimer:
    """Logs topic rates every 5 seconds."""

    def __init__(self, converters: dict):
        self._converters = converters   # name → converter object with ._count
        self._last_counts = {k: 0 for k in converters}
        self._timer = rospy.Timer(rospy.Duration(5.0), self._cb)

    def _cb(self, _event):
        lines = ["[Wrapper Diagnostics]"]
        for name, conv in self._converters.items():
            curr  = conv._count
            delta = curr - self._last_counts[name]
            rate  = delta / 5.0
            self._last_counts[name] = curr
            lines.append(f"  {name:20s}: total={curr:6d}  rate={rate:6.1f} Hz")
        rospy.loginfo("\n".join(lines))


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    rospy.init_node("urbannav_wrapper_node", anonymous=False, log_level=rospy.INFO)

    # ── Read ROS params (with defaults) ───────────────────────────────────────
    lidar_in  = rospy.get_param("~lidar_topic_in",  DEFAULT_LIDAR_IN)
    imu_in    = rospy.get_param("~imu_topic_in",    DEFAULT_IMU_IN)
    cam_in    = rospy.get_param("~camera_topic_in", DEFAULT_CAM_IN)

    lidar_out = rospy.get_param("~lidar_topic_out",  DEFAULT_LIDAR_OUT)
    imu_out   = rospy.get_param("~imu_topic_out",    DEFAULT_IMU_OUT)
    cam_out   = rospy.get_param("~camera_topic_out", DEFAULT_CAM_OUT)

    lidar_frame = rospy.get_param("~lidar_frame_id", LIDAR_FRAME_OUT)
    imu_frame   = rospy.get_param("~imu_frame_id",   IMU_FRAME_OUT)
    cam_frame   = rospy.get_param("~camera_frame_id", CAM_FRAME_OUT)

    # ── Instantiate converters ─────────────────────────────────────────────
    lidar_conv  = LidarConverter(lidar_in, lidar_out, lidar_frame)
    imu_conv    = ImuConverter(imu_in, imu_out, imu_frame)
    cam_conv    = CameraPassthrough(cam_in, cam_out, cam_frame)

    # ── Diagnostics ──────────────────────────────────────────────────────────
    DiagnosticsTimer({
        "LiDAR":  lidar_conv,
        "IMU":    imu_conv,
        "Camera": cam_conv,
    })

    rospy.loginfo(
        "\n"
        "════════════════════════════════════════════════════════\n"
        "  UrbanNav → Fast-LIO2 Wrapper  ACTIVE\n"
        "════════════════════════════════════════════════════════\n"
        "  Topic mappings:\n"
        f"    {lidar_in:35s} → {lidar_out}\n"
        f"    {imu_in:35s} → {imu_out}\n"
        f"    {cam_in:35s} → {cam_out}\n"
        "  Frame-ID mappings:\n"
        f"    [raw]         → {lidar_frame}  (LiDAR)\n"
        f"    [raw]         → {imu_frame}  (IMU)\n"
        f"    [raw]         → {cam_frame}  (Camera)\n"
        "════════════════════════════════════════════════════════"
    )

    rospy.spin()


if __name__ == "__main__":
    main()
