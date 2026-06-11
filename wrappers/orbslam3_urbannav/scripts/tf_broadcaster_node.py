#!/usr/bin/env python3
"""
tf_broadcaster_node.py  (orbslam3_urbannav)
============================================
Static context transforms for ORB-SLAM3 RViz. The dynamic localisation TF
(camera_init -> camera_right) is published by pose_republisher_node.py.
"""

import numpy as np
import rospy
import tf2_ros
import geometry_msgs.msg as gm
import transforms3d


def mat4_to_stamped_transform(T: np.ndarray, parent: str, child: str) -> gm.TransformStamped:
    ts = gm.TransformStamped()
    ts.header.stamp = rospy.Time.now()
    ts.header.frame_id = parent
    ts.child_frame_id = child
    ts.transform.translation.x = float(T[0, 3])
    ts.transform.translation.y = float(T[1, 3])
    ts.transform.translation.z = float(T[2, 3])
    wxyz = transforms3d.quaternions.mat2quat(T[:3, :3])
    ts.transform.rotation.w = float(wxyz[0])
    ts.transform.rotation.x = float(wxyz[1])
    ts.transform.rotation.y = float(wxyz[2])
    ts.transform.rotation.z = float(wxyz[3])
    return ts


def translation_tf(x, y, z):
    T = np.eye(4)
    T[:3, 3] = [x, y, z]
    return T


# ROS optical-frame rotation: camera frame -> optical frame
CAM_TO_OPTICAL = np.array([
    [0., 0., 1., 0.],
    [-1., 0., 0., 0.],
    [0., -1., 0., 0.],
    [0., 0., 0., 1.],
])


def build_static_transforms():
    transforms = []
    world_frame = rospy.get_param("~world_frame_id", "camera_init")
    camera_frame = rospy.get_param("~camera_frame_id", "camera_right")
    optical_frame = rospy.get_param("~optical_frame_id", "camera_right_optical")

    # Dynamic pose is world_frame -> camera_frame. Do not publish it here.
    transforms.append(mat4_to_stamped_transform(CAM_TO_OPTICAL, camera_frame, optical_frame))

    # Context frames only. Kept disconnected from the dynamic ORB pose unless the
    # user explicitly changes parent frames in RViz.
    transforms.append(mat4_to_stamped_transform(translation_tf(0.0, 0.0, -0.28), camera_frame, "velodyne"))
    transforms.append(mat4_to_stamped_transform(np.eye(4), world_frame, "map"))
    return transforms


def main():
    rospy.init_node("orbslam3_tf_broadcaster_node", anonymous=False)
    broadcaster = tf2_ros.StaticTransformBroadcaster()
    transforms = build_static_transforms()
    broadcaster.sendTransform(transforms)
    rospy.loginfo(
        "[ORB-SLAM3 TF] Published %d static transforms:\n%s",
        len(transforms),
        "\n".join(f"  {t.header.frame_id} -> {t.child_frame_id}" for t in transforms),
    )
    rospy.spin()


if __name__ == "__main__":
    main()
