#!/usr/bin/env python3
"""Record independent estimator, fused, and health timelines."""
import csv
import json
import os
import shutil
import threading

import rospy
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Bool, String


class MultiTrajectoryRecorder:
    def __init__(self):
        self.lock = threading.Lock()
        self.output_dir = rospy.get_param("~output_dir", "/data/output/current_run")
        self.visual_path_frame = rospy.get_param("~visual_path_frame", "map")
        self.max_path_poses = int(rospy.get_param("~max_path_poses", 100000))
        os.makedirs(self.output_dir, exist_ok=True)
        topics = rospy.get_param("~topics", {
            "fast_livo2": "/fast_livo2/odometry",
            "orbslam3_live": "/orbslam3/camera_odometry",
            "orbslam3_raw": "/orbslam3/raw_camera_odometry",
            "lvisam": "/lvisam/odometry",
            "fused": "/fused_localization/odometry",
            "fused_continuous": "/fused_localization/continuous_odometry",
            "fused_metric": "/fused_localization/metric_odometry",
        })
        path_topics = rospy.get_param("~path_topics", {
            "orbslam3": "/orbslam3/camera_path",
            "orbslam3_optimized": "/orbslam3/optimized_camera_path",
        })
        self.files = {}
        self.writers = {}
        self.has_data = set()
        self.path_pubs = {}
        self.paths = {}
        for name, topic in topics.items():
            rospy.Subscriber(topic, Odometry, lambda msg, n=name: self.odom_cb(n, msg), queue_size=500)
            self.path_pubs[name] = rospy.Publisher(f"/debug_paths/{name}", Path, queue_size=2, latch=True)
            path = Path()
            path.header.frame_id = self.visual_path_frame
            self.paths[name] = path
        self.path_names = set()
        self.final_aliases = rospy.get_param("~final_aliases", {
            "orbslam3_optimized": "orbslam3",
        })
        for name, topic in path_topics.items():
            self.path_names.add(name)
            rospy.Subscriber(topic, Path, lambda msg, n=name: self.path_cb(n, msg), queue_size=5)
        self.timeline = open(os.path.join(self.output_dir, "localization_timeline.jsonl"), "w", encoding="utf-8")
        for topic in ("/localization_health/summary", "/fused_localization/status",
                      "/fused_localization/events", "/fused_localization/active_source"):
            rospy.Subscriber(topic, String, lambda msg, t=topic: self.text_cb(t, msg), queue_size=200)
        rospy.Subscriber("/fused_localization/navigation_ok", Bool, self.bool_cb, queue_size=200)
        rospy.on_shutdown(self.close)
        rospy.loginfo("[Recorder] output_dir=%s", self.output_dir)

    def open_csv(self, name: str):
        handle = open(os.path.join(self.output_dir, f"{name}_trajectory.csv"), "w", newline="", encoding="utf-8")
        writer = csv.writer(handle)
        writer.writerow(["timestamp_s", "x_m", "y_m", "z_m", "qx", "qy", "qz", "qw", "frame_id", "child_frame_id"])
        return handle, writer

    def ensure_csv(self, name: str):
        if name not in self.writers:
            handle, writer = self.open_csv(name)
            self.files[name] = handle
            self.writers[name] = writer
        return self.files[name], self.writers[name]

    def odom_cb(self, name: str, msg: Odometry) -> None:
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        with self.lock:
            handle, writer = self.ensure_csv(name)
            writer.writerow([msg.header.stamp.to_sec(), p.x, p.y, p.z, q.x, q.y, q.z, q.w,
                             msg.header.frame_id, msg.child_frame_id])
            self.has_data.add(name)
            handle.flush()
            pose = PoseStamped()
            pose.header.stamp = msg.header.stamp
            pose.header.frame_id = self.visual_path_frame
            pose.pose = msg.pose.pose
            path = self.paths[name]
            path.header.stamp = msg.header.stamp
            path.poses.append(pose)
            if len(path.poses) > self.max_path_poses:
                path.poses = path.poses[-self.max_path_poses:]
            self.path_pubs[name].publish(path)

    def path_cb(self, name: str, msg: Path) -> None:
        rows = []
        for pose in msg.poses:
            p = pose.pose.position
            q = pose.pose.orientation
            frame_id = pose.header.frame_id or msg.header.frame_id
            rows.append([pose.header.stamp.to_sec(), p.x, p.y, p.z, q.x, q.y, q.z, q.w,
                         frame_id, ""])
        with self.lock:
            if not rows:
                return
            try:
                self.files.pop(name).close()
            except Exception:
                pass
            self.writers.pop(name, None)
            handle, writer = self.open_csv(name)
            writer.writerows(rows)
            handle.flush()
            self.files[name] = handle
            self.writers[name] = writer
            self.has_data.add(name)

    def text_cb(self, topic: str, msg: String) -> None:
        with self.lock:
            try:
                payload = json.loads(msg.data)
            except Exception:
                payload = {"raw": msg.data}
            self.timeline.write(json.dumps({"topic": topic, "receipt_time": rospy.Time.now().to_sec(), "data": payload}, sort_keys=True) + "\n")
            self.timeline.flush()

    def bool_cb(self, msg: Bool) -> None:
        with self.lock:
            self.timeline.write(json.dumps({"topic": "/fused_localization/navigation_ok",
                                            "receipt_time": rospy.Time.now().to_sec(),
                                            "data": bool(msg.data)}, sort_keys=True) + "\n")
            self.timeline.flush()

    def close(self) -> None:
        with self.lock:
            for handle in self.files.values():
                try:
                    handle.close()
                except Exception:
                    pass
            for source, target in self.final_aliases.items():
                source_path = os.path.join(self.output_dir, f"{source}_trajectory.csv")
                target_path = os.path.join(self.output_dir, f"{target}_trajectory.csv")
                if source in self.has_data and os.path.isfile(source_path) and os.path.getsize(source_path) > 0:
                    try:
                        shutil.copyfile(source_path, target_path)
                    except Exception as exc:
                        rospy.logwarn("[Recorder] failed to finalize %s from %s: %s", target_path, source_path, exc)
            try:
                self.timeline.close()
            except Exception:
                pass


def main() -> None:
    rospy.init_node("multi_trajectory_recorder")
    MultiTrajectoryRecorder()
    rospy.spin()


if __name__ == "__main__":
    main()
