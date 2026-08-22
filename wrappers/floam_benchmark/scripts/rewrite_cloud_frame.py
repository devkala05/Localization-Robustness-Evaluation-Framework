#!/usr/bin/env python3
"""Present native LiDAR coordinates under FLOAM's expected processing frame."""

import copy

import numpy as np
import rospy
from sensor_msgs.msg import PointCloud2


class CloudFrameAdapter:
    def __init__(self):
        self.frame_id = rospy.get_param("~frame_id", "base_link")
        self.filter_rings = bool(rospy.get_param("~filter_rings", True))
        self.selected_rings = None
        output_topic = rospy.get_param("~output_topic", "/floam/points_raw")
        input_topic = rospy.get_param("~input_topic", "/benchmark/points_raw")
        self.publisher = rospy.Publisher(output_topic, PointCloud2, queue_size=2)
        self.subscriber = rospy.Subscriber(
            input_topic, PointCloud2, self.callback, queue_size=2
        )

    def callback(self, message):
        fields = {field.name: field for field in message.fields}
        required = ("x", "y", "z", "ring")
        if any(name not in fields for name in required) or message.is_bigendian:
            rospy.logerr_throttle(5.0, "FLOAM adapter requires little-endian x/y/z/ring fields")
            return
        count = message.width * message.height
        kwargs = {"buffer": message.data, "shape": (count,), "strides": (message.point_step,)}
        x = np.ndarray(dtype="<f4", offset=fields["x"].offset, **kwargs)
        y = np.ndarray(dtype="<f4", offset=fields["y"].offset, **kwargs)
        z = np.ndarray(dtype="<f4", offset=fields["z"].offset, **kwargs)
        rings = np.ndarray(dtype="<u2", offset=fields["ring"].offset, **kwargs)
        if self.filter_rings and self.selected_rings is None:
            elevation = np.degrees(np.arctan2(z, np.hypot(x, y)))
            candidates = []
            for ring in np.unique(rings):
                angle = float(np.median(elevation[rings == ring]))
                if angle >= -8.83:
                    scan_id = int((2.0 - angle) * 3.0 + 0.5)
                    target = 2.0 - scan_id / 3.0
                else:
                    scan_id = 32 + int((-8.83 - angle) * 2.0 + 0.5)
                    target = -8.83 - (scan_id - 32) / 2.0
                if 0 <= scan_id < 64:
                    candidates.append((scan_id, abs(angle - target), int(ring)))
            chosen = {}
            for scan_id, error, ring in candidates:
                if scan_id not in chosen or error < chosen[scan_id][0]:
                    chosen[scan_id] = (error, ring)
            self.selected_rings = np.asarray(
                [item[1] for item in chosen.values()], dtype=np.uint16
            )
            rospy.loginfo(
                "FLOAM adapter selected %d non-colliding rings from the 128-line scan",
                len(self.selected_rings),
            )
        records = np.frombuffer(message.data, dtype=np.uint8).reshape(count, message.point_step)
        filtered = records[np.isin(rings, self.selected_rings)] if self.filter_rings else records
        output = copy.copy(message)
        output.header.frame_id = self.frame_id
        output.height = 1
        output.width = len(filtered)
        output.row_step = output.point_step * output.width
        output.data = filtered.tobytes()
        self.publisher.publish(output)


if __name__ == "__main__":
    rospy.init_node("floam_cloud_frame_adapter")
    CloudFrameAdapter()
    rospy.spin()
