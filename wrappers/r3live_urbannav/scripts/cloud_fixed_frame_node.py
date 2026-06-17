#!/usr/bin/env python3
"""Republish R3LIVE visualization clouds in a stable fixed frame.

Some upstream R3LIVE builds publish registered/current clouds with body-ish frame
IDs while RViz Fixed Frame is camera_init. If RViz accumulates those messages with
Decay Time, old scans are re-rendered through the current body TF and the whole
world appears to roll around.  This node transforms each incoming cloud once at
its original timestamp and republishes a fixed-frame copy for RViz/benchmark
visualization.  It does not feed back into R3LIVE and does not change odometry.
"""

import copy
import math
import struct
import time
from typing import Dict

import rospy
import tf2_ros
from sensor_msgs.msg import PointCloud2, PointField

try:
    import tf2_sensor_msgs.tf2_sensor_msgs as tf2_sm
    _HAS_TF2_SENSOR = True
except Exception:
    _HAS_TF2_SENSOR = False


def _quat_to_rot(q):
    x = float(q.x)
    y = float(q.y)
    z = float(q.z)
    w = float(q.w)
    n = x * x + y * y + z * z + w * w
    if n <= 1e-24:
        return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    s = 2.0 / n
    xx, yy, zz = x * x * s, y * y * s, z * z * s
    xy, xz, yz = x * y * s, x * z * s, y * z * s
    wx, wy, wz = w * x * s, w * y * s, w * z * s
    return (
        (1.0 - yy - zz, xy - wz, xz + wy),
        (xy + wz, 1.0 - xx - zz, yz - wx),
        (xz - wy, yz + wx, 1.0 - xx - yy),
    )


def _manual_transform_cloud(cloud, transform):
    """Transform x/y/z in a PointCloud2 while preserving the original binary layout.

    This is a fallback for containers where ros-noetic-tf2-sensor-msgs was not
    installed.  It keeps all extra fields (intensity, rgb, normal, time, ring,
    etc.) untouched and changes only x, y, z float32 coordinates.
    """
    field_map = {f.name: f for f in cloud.fields}
    if not all(name in field_map for name in ('x', 'y', 'z')):
        raise RuntimeError('PointCloud2 has no x/y/z fields')
    fx, fy, fz = field_map['x'], field_map['y'], field_map['z']
    if fx.datatype != PointField.FLOAT32 or fy.datatype != PointField.FLOAT32 or fz.datatype != PointField.FLOAT32:
        raise RuntimeError('PointCloud2 x/y/z fields are not FLOAT32')

    out = copy.copy(cloud)
    data = bytearray(cloud.data)
    endian = '>' if cloud.is_bigendian else '<'
    fmt = endian + 'f'
    r = _quat_to_rot(transform.transform.rotation)
    t = transform.transform.translation
    tx, ty, tz = float(t.x), float(t.y), float(t.z)
    total = int(cloud.width) * int(cloud.height)
    step = int(cloud.point_step)
    for i in range(total):
        base = i * step
        try:
            x = struct.unpack_from(fmt, data, base + fx.offset)[0]
            y = struct.unpack_from(fmt, data, base + fy.offset)[0]
            z = struct.unpack_from(fmt, data, base + fz.offset)[0]
        except Exception:
            break
        if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
            continue
        nx = r[0][0] * x + r[0][1] * y + r[0][2] * z + tx
        ny = r[1][0] * x + r[1][1] * y + r[1][2] * z + ty
        nz = r[2][0] * x + r[2][1] * y + r[2][2] * z + tz
        struct.pack_into(fmt, data, base + fx.offset, float(nx))
        struct.pack_into(fmt, data, base + fy.offset, float(ny))
        struct.pack_into(fmt, data, base + fz.offset, float(nz))
    out.data = bytes(data)
    out.header.frame_id = transform.header.frame_id
    out.header.stamp = cloud.header.stamp
    return out


class CloudFixedFrameNode:
    def __init__(self):
        self.fixed_frame = rospy.get_param('~fixed_frame', 'camera_init')
        self.cloud_topics = self._parse_map(rospy.get_param(
            '~cloud_topics',
            '/cloud_registered:/r3live/cloud_registered_fixed,'
            '/laser_cloud_surround:/r3live/laser_cloud_surround_fixed,'
            '/RGB_map:/r3live/rgb_map_fixed'
        ))
        self.allow_header_only = bool(rospy.get_param('~allow_header_only_if_already_fixed', True))
        self.lookup_timeout = float(rospy.get_param('~lookup_timeout_sec', 0.03))
        self.warn_period = float(rospy.get_param('~warn_period_sec', 5.0))

        self.tf_buffer = tf2_ros.Buffer(cache_time=rospy.Duration(60.0))
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)
        self.pubs: Dict[str, rospy.Publisher] = {}
        self.last_warn: Dict[str, float] = {}
        self.counts: Dict[str, int] = {}

        for src, dst in self.cloud_topics.items():
            self.pubs[src] = rospy.Publisher(dst, PointCloud2, queue_size=3)
            rospy.Subscriber(src, PointCloud2, self._cb, callback_args=src, queue_size=3)
        rospy.loginfo('[R3LIVE CloudFixedFrame] fixed_frame=%s topics=%s tf2_sensor=%s',
                      self.fixed_frame,
                      ', '.join('%s->%s' % (s, d) for s, d in self.cloud_topics.items()),
                      _HAS_TF2_SENSOR)

    @staticmethod
    def _parse_map(text):
        out = {}
        for item in str(text).split(','):
            item = item.strip()
            if not item:
                continue
            if ':' not in item:
                continue
            src, dst = item.split(':', 1)
            src = src.strip()
            dst = dst.strip()
            if src and dst:
                out[src] = dst
        return out

    def _warn(self, src, msg, *args):
        now = time.monotonic()
        if now - self.last_warn.get(src, 0.0) > self.warn_period:
            rospy.logwarn(msg, *args)
            self.last_warn[src] = now

    def _cb(self, cloud, src):
        pub = self.pubs[src]
        frame = cloud.header.frame_id.strip().lstrip('/')
        fixed = self.fixed_frame.strip().lstrip('/')
        if not frame or frame == fixed:
            out = copy.copy(cloud)
            out.header.frame_id = self.fixed_frame
            pub.publish(out)
            return

        stamp = cloud.header.stamp
        try:
            transform = self.tf_buffer.lookup_transform(
                self.fixed_frame, cloud.header.frame_id,
                stamp if stamp != rospy.Time(0) else rospy.Time(0),
                rospy.Duration(self.lookup_timeout)
            )
            if _HAS_TF2_SENSOR:
                out = tf2_sm.do_transform_cloud(cloud, transform)
            else:
                out = _manual_transform_cloud(cloud, transform)
            out.header.frame_id = self.fixed_frame
            out.header.stamp = cloud.header.stamp
            pub.publish(out)
            n = self.counts.get(src, 0) + 1
            self.counts[src] = n
            if n == 1:
                mode = 'tf2_sensor_msgs' if _HAS_TF2_SENSOR else 'manual PointCloud2 transform'
                rospy.loginfo('[R3LIVE CloudFixedFrame] first transformed %s frame %s -> %s using %s',
                              src, frame, self.fixed_frame, mode)
        except Exception as exc:
            if self.allow_header_only:
                # Last-resort visualization fallback: keep points unchanged but anchor
                # them to the fixed frame so RViz does not re-transform old scans by
                # the current body pose.  This should only happen if TF is absent.
                out = copy.copy(cloud)
                out.header.frame_id = self.fixed_frame
                pub.publish(out)
                self._warn(src, '[R3LIVE CloudFixedFrame] TF unavailable for %s frame %s -> %s (%s); header-anchoring for RViz only',
                           src, frame, self.fixed_frame, exc)
            else:
                self._warn(src, '[R3LIVE CloudFixedFrame] dropping %s: cannot transform %s -> %s (%s)',
                           src, frame, self.fixed_frame, exc)


def main():
    rospy.init_node('r3live_cloud_fixed_frame', anonymous=False)
    CloudFixedFrameNode()
    rospy.spin()


if __name__ == '__main__':
    main()
