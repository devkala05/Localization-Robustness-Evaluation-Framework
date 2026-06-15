#!/usr/bin/env python3
"""Record nav_msgs/Odometry or geometry_msgs/PoseStamped to TUM format."""
import os
import rospy
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped


class TumRecorder:
    def __init__(self):
        self.topic = rospy.get_param("~topic", "/localization/odometry")
        self.message_type = rospy.get_param("~message_type", "nav_msgs/Odometry")
        self.output = rospy.get_param("~output", "data/outputs/trajectory.tum")
        os.makedirs(os.path.dirname(os.path.abspath(self.output)), exist_ok=True)
        self.f = open(self.output, "a", encoding="utf-8")
        if self.message_type == "geometry_msgs/PoseStamped":
            cls = PoseStamped
        elif self.message_type == "geometry_msgs/PoseWithCovarianceStamped":
            cls = PoseWithCovarianceStamped
        else:
            cls = Odometry
        self.sub = rospy.Subscriber(self.topic, cls, self.cb, queue_size=100)
        rospy.loginfo("Recording %s [%s] to %s", self.topic, self.message_type, self.output)

    def cb(self, msg):
        if isinstance(msg, Odometry):
            pose = msg.pose.pose
            stamp = msg.header.stamp
        elif isinstance(msg, PoseWithCovarianceStamped):
            pose = msg.pose.pose
            stamp = msg.header.stamp
        else:
            pose = msg.pose
            stamp = msg.header.stamp
        t = stamp.to_sec() if stamp else rospy.Time.now().to_sec()
        p, q = pose.position, pose.orientation
        self.f.write(f"{t:.9f} {p.x:.9f} {p.y:.9f} {p.z:.9f} {q.x:.9f} {q.y:.9f} {q.z:.9f} {q.w:.9f}\n")
        self.f.flush()

    def close(self):
        try:
            self.f.close()
        except Exception:
            pass


if __name__ == "__main__":
    rospy.init_node("odom_pose_to_tum")
    rec = TumRecorder()
    rospy.on_shutdown(rec.close)
    rospy.spin()
