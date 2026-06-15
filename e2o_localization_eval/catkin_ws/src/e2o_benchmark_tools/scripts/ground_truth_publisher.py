#!/usr/bin/env python3
"""Publish a TUM trajectory as /ground_truth/odom and /ground_truth/path."""
import bisect
import os
import math
import rospy
import tf2_ros
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped, TransformStamped


def read_tum(path):
    poses = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 8:
                rospy.logwarn("Skipping malformed TUM line %d: %s", line_no, line)
                continue
            t, tx, ty, tz, qx, qy, qz, qw = map(float, parts)
            if not all(math.isfinite(v) for v in (t, tx, ty, tz, qx, qy, qz, qw)):
                continue
            poses.append((t, tx, ty, tz, qx, qy, qz, qw))
    poses.sort(key=lambda x: x[0])
    return poses


def make_pose_stamped(row, stamp, frame):
    _, tx, ty, tz, qx, qy, qz, qw = row
    ps = PoseStamped()
    ps.header.stamp = stamp
    ps.header.frame_id = frame
    ps.pose.position.x = tx
    ps.pose.position.y = ty
    ps.pose.position.z = tz
    ps.pose.orientation.x = qx
    ps.pose.orientation.y = qy
    ps.pose.orientation.z = qz
    ps.pose.orientation.w = qw
    return ps


def make_transform(ps, child_frame):
    tr = TransformStamped()
    tr.header = ps.header
    tr.child_frame_id = child_frame
    tr.transform.translation.x = ps.pose.position.x
    tr.transform.translation.y = ps.pose.position.y
    tr.transform.translation.z = ps.pose.position.z
    tr.transform.rotation = ps.pose.orientation
    return tr


if __name__ == "__main__":
    rospy.init_node("ground_truth_publisher")
    tum_file = rospy.get_param("~tum_file")
    odom_topic = rospy.get_param("~odom_topic", "/ground_truth/odom")
    path_topic = rospy.get_param("~path_topic", "/ground_truth/path")
    world_frame = rospy.get_param("~world_frame", "map")
    child_frame = rospy.get_param("~child_frame", "base_link_gt")
    rate_hz = float(rospy.get_param("~rate", 20.0))
    publish_full_path_each_tick = bool(rospy.get_param("~publish_full_path_each_tick", True))
    timed_playback = bool(rospy.get_param("~timed_playback", True))
    broadcast_tf = bool(rospy.get_param("~broadcast_tf", False))

    if not os.path.exists(tum_file):
        rospy.logerr("Ground-truth TUM file not found: %s", tum_file)
        raise SystemExit(2)
    traj = read_tum(tum_file)
    if not traj:
        rospy.logerr("No valid poses in TUM file: %s", tum_file)
        raise SystemExit(3)

    odom_pub = rospy.Publisher(odom_topic, Odometry, queue_size=20)
    path_pub = rospy.Publisher(path_topic, Path, queue_size=5, latch=True)
    tf_pub = tf2_ros.TransformBroadcaster() if broadcast_tf else None
    path = Path()
    path.header.frame_id = world_frame
    for row in traj:
        stamp = rospy.Time.from_sec(row[0]) if row[0] > 0 else rospy.Time.now()
        path.poses.append(make_pose_stamped(row, stamp, world_frame))
    traj_times = [row[0] for row in traj]
    rate = rospy.Rate(rate_hz)
    rospy.loginfo("Publishing %d GT poses from %s", len(traj), tum_file)
    path_pub.publish(path)

    next_index = 0
    last_published_index = -1
    while not rospy.is_shutdown():
        if timed_playback:
            now = rospy.Time.now().to_sec()
            index = bisect.bisect_right(traj_times, now) - 1
            if index < 0:
                rate.sleep()
                continue
            next_index = min(index, len(traj) - 1)
        elif next_index >= len(traj):
            break
        if next_index == last_published_index:
            rate.sleep()
            continue
        row = traj[next_index]
        stamp = rospy.Time.from_sec(row[0]) if row[0] > 0 else rospy.Time.now()
        ps = make_pose_stamped(row, stamp, world_frame)
        odom = Odometry()
        odom.header = ps.header
        odom.child_frame_id = child_frame
        odom.pose.pose = ps.pose
        odom_pub.publish(odom)
        if tf_pub:
            tf_pub.sendTransform(make_transform(ps, child_frame))
        path.header.stamp = stamp
        if publish_full_path_each_tick:
            path_pub.publish(path)
        last_published_index = next_index
        if not timed_playback:
            next_index += 1
        rate.sleep()

    path_pub.publish(path)
    rospy.loginfo("Finished publishing ground-truth trajectory.")
    rospy.spin()
