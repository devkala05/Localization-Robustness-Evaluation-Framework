#!/usr/bin/env python3
"""Apply a configured ALIVE perturbation live, without modifying a rosbag."""
from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import rospy
import yaml
from sensor_msgs.msg import Image, Imu, NavSatFix, PointCloud2

from perturb_bag import ImuPerturber, perturb_camera, perturb_depth, perturb_gps, perturb_lidar


class LivePerturbation:
    def __init__(self) -> None:
        config_path = Path(rospy.get_param("~config")).resolve()
        self.scenario_name = str(rospy.get_param("~scenario"))
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if self.scenario_name not in config["scenarios"]:
            raise rospy.ROSInitException(f"unknown scenario: {self.scenario_name}")
        self.config = config
        self.scenario = config["scenarios"][self.scenario_name]
        self.topics = config["topics"]
        self.start = float(self.scenario["start_time"])
        self.end = float(self.scenario["end_time"])
        self.severity = float(self.scenario.get("severity", 1.0))
        self.bag_start = float(rospy.get_param("~bag_start_time_s"))
        seed = int(config.get("random_seed", 0)) + {"rain": 101, "fog": 202, "sensor_degradation": 303}[self.scenario_name]
        child_seeds = np.random.SeedSequence(seed).spawn(5)
        self.rng = {name: np.random.default_rng(child) for name, child in zip(
            ("lidar", "camera", "depth", "gps", "imu"), child_seeds)}
        self.imu = ImuPerturber(self.scenario.get("imu", {}), self.severity, self.rng["imu"])
        self.publishers = {}
        self._wire("lidar", PointCloud2, self.lidar_callback)
        self._wire("camera", Image, self.camera_callback)
        self._wire("depth", Image, self.depth_callback)
        self._wire("gps", NavSatFix, self.gps_callback)
        self._wire("imu", Imu, self.imu_callback)
        rospy.loginfo("[live_perturbation] scenario=%s interval=[%.3f, %.3f]", self.scenario_name, self.start, self.end)

    def _wire(self, name, message_type, callback) -> None:
        source = str(rospy.get_param(f"~{name}_input_topic", ""))
        output = str(rospy.get_param(f"~{name}_output_topic", ""))
        if not source or not output:
            return
        self.publishers[name] = rospy.Publisher(output, message_type, queue_size=200 if name in ("imu", "gps") else 20)
        rospy.Subscriber(source, message_type, callback, queue_size=200 if name in ("imu", "gps") else 20)

    def active(self) -> bool:
        relative = rospy.Time.now().to_sec() - self.bag_start
        return self.start <= relative <= self.end

    def publish(self, name, message) -> None:
        self.publishers[name].publish(message)

    def lidar_callback(self, message: PointCloud2) -> None:
        output = message
        if self.active() and self.scenario_name in ("rain", "fog"):
            output = perturb_lidar(message, self.scenario["lidar"], self.severity, self.rng["lidar"], self.scenario_name)
        self.publish("lidar", output)

    def camera_callback(self, message: Image) -> None:
        output = message
        if self.active() and self.scenario_name == "fog":
            output = perturb_camera(message, self.scenario["camera"], self.severity, self.rng["camera"])
        self.publish("camera", output)

    def depth_callback(self, message: Image) -> None:
        output = message
        if self.active() and self.scenario_name == "fog":
            output = perturb_depth(message, self.scenario["camera"], self.severity, self.rng["depth"])
        self.publish("depth", output)

    def gps_callback(self, message: NavSatFix) -> None:
        if self.active() and self.scenario_name == "sensor_degradation":
            relative = rospy.Time.now().to_sec() - self.bag_start
            gps = self.scenario["gps"]
            if bool(gps.get("drop_messages_during_outage", True)) and float(gps["outage_start_time"]) <= relative <= float(gps["outage_end_time"]):
                return
            self.publish("gps", perturb_gps(message, gps, self.severity, self.rng["gps"]))
            return
        self.publish("gps", message)

    def imu_callback(self, message: Imu) -> None:
        output = self.imu(message) if self.active() and self.scenario_name == "sensor_degradation" else message
        self.publish("imu", output)


if __name__ == "__main__":
    rospy.init_node("alive_live_perturbation")
    LivePerturbation()
    rospy.spin()
