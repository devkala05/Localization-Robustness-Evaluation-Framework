#!/usr/bin/env python3
"""
orbslam3_wrapper_node.py
========================
Black-box wrapper: UrbanNav-HK rosbag camera topics → ORB-SLAM3.

Topic Mapping (UrbanNav → ORB-SLAM3)
─────────────────────────────────────────────────────────────────────────
  SOURCE (rosbag)                          TARGET (ORB-SLAM3 ROS node)
  ──────────────────────────────────────   ──────────────────────────────
  /zed2/camera/left/image_raw  (Image)  →  /camera/left/image_raw
  /zed2/camera/right/image_raw (Image)  →  /camera/right/image_raw
  /zed2/camera/right/image_raw (Image)  →  /camera/image_raw

  The ORB-SLAM3 Mono ROS node subscribes to /camera/image_raw by default.
  The ORB-SLAM3 Stereo ROS node subscribes to /camera/left/image_raw and
  /camera/right/image_raw by default.
  This wrapper:
    1. Patches frame_id to camera_left/camera_right (matches our TF tree)
    2. Preserves timestamps exactly (critical for ORB-SLAM3 tracking)
    3. Optionally swaps the stereo pair for datasets whose bag topic order
       gives negative disparity in ORB-SLAM3's left/right convention
    4. Logs per-message diagnostics every 5 seconds

What is NOT forwarded to ORB-SLAM3:
  LiDAR, IMU, GPS, odometry, ground-truth.

Frame-ID mapping
─────────────────────────────────────────────────────────────────────────
  UrbanNav raw frame_id    →  ORB-SLAM3 frame_id
  ──────────────────────      ──────────────────
  zed2_left_camera_frame   →  camera_left
  zed2_right_camera_frame  →  camera_right

ORB-SLAM3 output topics (published by the ORB-SLAM3 ROS node itself):
  /orb_slam3/camera_pose     — geometry_msgs/PoseStamped
  /orb_slam3/body_odom       — nav_msgs/Odometry  (if available)
  /orb_slam3/tracked_mappoints — sensor_msgs/PointCloud2
  /orb_slam3/tracking_image  — sensor_msgs/Image  (debug overlay)
  /tf                        — odom → camera_right (dynamic, ORB-SLAM3)
"""

import threading
import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import Header


# ─────────────────────────────────────────────────────────────────────────────
#  Configuration (overridable via ROS params)
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_LEFT_IN   = "/zed2/camera/left/image_raw"
DEFAULT_RIGHT_IN  = "/zed2/camera/right/image_raw"
DEFAULT_LEFT_OUT  = "/camera/left/image_raw"
DEFAULT_RIGHT_OUT = "/camera/right/image_raw"
DEFAULT_MONO_OUT  = "/camera/image_raw"
DEFAULT_LEFT_FRAME_ID = "camera_left"
DEFAULT_RIGHT_FRAME_ID = "camera_right"

QUEUE_SIZE = 50


# ─────────────────────────────────────────────────────────────────────────────
#  Helper
# ─────────────────────────────────────────────────────────────────────────────
def _patched_header(src: Header, new_frame_id: str) -> Header:
    """Return a new Header with the same stamp but a different frame_id."""
    h = Header()
    h.seq      = src.seq
    h.stamp    = src.stamp     # preserve original timestamp exactly
    h.frame_id = new_frame_id
    return h


# ─────────────────────────────────────────────────────────────────────────────
#  Camera converter
# ─────────────────────────────────────────────────────────────────────────────
class CameraConverter:
    """
    Subscribes to an UrbanNav image topic, patches frame_id, and republishes
    on the topic expected by ORB-SLAM3.

    ZED2 right camera properties (from zed2_intrinsics.yaml):
      Width:  672 px
      Height: 376 px
      Model:  PINHOLE
      fx: 264.2125   fy: 264.155
      cx: 341.635    cy: 183.993
      k1: -0.0423469  k2: 0.0115525

    ORB-SLAM3 expects raw 8-bit or colour images.
    No image modification is performed — pixel data forwarded verbatim.
    """

    def __init__(self, topic_in: str, topic_out: str, frame_id_out: str):
        self._frame_id_out = frame_id_out
        self._pub   = rospy.Publisher(topic_out, Image, queue_size=QUEUE_SIZE)
        self._sub   = rospy.Subscriber(topic_in, Image, self._cb,
                                       queue_size=QUEUE_SIZE)
        self._count = 0
        self._lock  = threading.Lock()
        rospy.loginfo(
            f"[CameraConverter] {topic_in} → {topic_out}  "
            f"frame_id: {frame_id_out}"
        )

    def _cb(self, msg: Image):
        with self._lock:
            out = Image()
            out.header       = _patched_header(msg.header, self._frame_id_out)
            out.height       = msg.height
            out.width        = msg.width
            out.encoding     = msg.encoding
            out.is_bigendian = msg.is_bigendian
            out.step         = msg.step
            out.data         = msg.data
            self._pub.publish(out)
            self._count += 1
            if self._count % 30 == 0:
                rospy.logdebug(
                    f"[{self._frame_id_out}] forwarded {self._count} frames  "
                    f"stamp={msg.header.stamp.to_sec():.3f}  "
                    f"size={msg.width}×{msg.height}  enc={msg.encoding}"
                )


# ─────────────────────────────────────────────────────────────────────────────
#  Diagnostics
# ─────────────────────────────────────────────────────────────────────────────
class DiagnosticsTimer:
    """Logs topic rates every 5 seconds (mirrors fast_lio_urbannav convention)."""

    def __init__(self, converters: dict):
        self._converters   = converters
        self._last_counts  = {k: 0 for k in converters}
        self._timer        = rospy.Timer(rospy.Duration(5.0), self._cb)

    def _cb(self, _event):
        lines = ["[ORB-SLAM3 Wrapper Diagnostics]"]
        for name, conv in self._converters.items():
            curr  = conv._count
            delta = curr - self._last_counts[name]
            rate  = delta / 5.0
            self._last_counts[name] = curr
            lines.append(
                f"  {name:20s}: total={curr:6d}  rate={rate:6.1f} Hz"
            )
        rospy.loginfo("\n".join(lines))


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    rospy.init_node("orbslam3_wrapper_node", anonymous=False,
                    log_level=rospy.INFO)

    left_in = rospy.get_param("~left_camera_topic_in", DEFAULT_LEFT_IN)
    right_in = rospy.get_param("~right_camera_topic_in", DEFAULT_RIGHT_IN)
    left_out = rospy.get_param("~left_camera_topic_out", DEFAULT_LEFT_OUT)
    right_out = rospy.get_param("~right_camera_topic_out", DEFAULT_RIGHT_OUT)
    mono_out = rospy.get_param("~mono_camera_topic_out", DEFAULT_MONO_OUT)
    left_frame_id = rospy.get_param("~left_camera_frame_id", DEFAULT_LEFT_FRAME_ID)
    right_frame_id = rospy.get_param("~right_camera_frame_id", DEFAULT_RIGHT_FRAME_ID)
    stereo_swap_lr = rospy.get_param("~stereo_swap_lr", False)

    if stereo_swap_lr:
        left_conv = CameraConverter(right_in, left_out, left_frame_id)
        right_conv = CameraConverter(left_in, right_out, right_frame_id)
    else:
        left_conv = CameraConverter(left_in, left_out, left_frame_id)
        right_conv = CameraConverter(right_in, right_out, right_frame_id)
    mono_conv = CameraConverter(right_in, mono_out, right_frame_id)

    DiagnosticsTimer({
        "Left Camera": left_conv,
        "Right Camera": right_conv,
        "Mono Camera": mono_conv,
    })

    rospy.loginfo(
        "\n"
        "════════════════════════════════════════════════════════\n"
        "  UrbanNav → ORB-SLAM3 Camera Wrapper  ACTIVE\n"
        "════════════════════════════════════════════════════════\n"
        f"  Left input   : {left_in}\n"
        f"  Left output  : {left_out}\n"
        f"  Right input  : {right_in}\n"
        f"  Right output : {right_out}\n"
        f"  Mono output  : {mono_out}  (right camera alias)\n"
        f"  Stereo swap  : {stereo_swap_lr}\n"
        "  Sensor modes : Monocular right + Stereo left/right\n"
        "  NOT forwarded: LiDAR, IMU, GPS, ground-truth\n"
        "════════════════════════════════════════════════════════"
    )

    rospy.spin()


if __name__ == "__main__":
    main()
