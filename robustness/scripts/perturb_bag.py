#!/usr/bin/env python3
"""Create deterministic, interval-limited weather/sensor perturbation bags.

The writer preserves every untouched serialized message, record timestamp,
topic name, connection message type and message header. Only selected sensor
payloads inside the configured interval are changed. Ground-truth/reference
data is never read by this program and can therefore never leak into a bag.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import cv2
import numpy as np
import rosbag
import yaml
from sensor_msgs.msg import Image, Imu, NavSatFix, PointCloud2, PointField


FIELD_DTYPES = {
    PointField.INT8: "i1", PointField.UINT8: "u1",
    PointField.INT16: "i2", PointField.UINT16: "u2",
    PointField.INT32: "i4", PointField.UINT32: "u4",
    PointField.FLOAT32: "f4", PointField.FLOAT64: "f8",
}


def finite(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def validate_interval(config: dict, bag_duration: float) -> Tuple[float, float, float]:
    start = finite(config["start_time"], "start_time")
    end = finite(config["end_time"], "end_time")
    severity = finite(config.get("severity", 1.0), "severity")
    if not (0.0 <= start < end <= bag_duration + 1.0e-6):
        raise ValueError(f"interval [{start}, {end}] is outside bag duration {bag_duration:.6f}")
    if not 0.0 <= severity <= 1.0:
        raise ValueError("severity must be in [0, 1]")
    return start, end, severity


def topic_set(topics: dict, name: str) -> set:
    values = topics.get(name, [])
    return {str(item) for item in ([values] if isinstance(values, str) else values)}


def field_view(message: PointCloud2, field_name: str, writable: np.ndarray) -> np.ndarray:
    field = next((item for item in message.fields if item.name == field_name), None)
    if field is None or field.datatype not in FIELD_DTYPES or field.count != 1:
        raise ValueError(f"PointCloud2 field {field_name!r} is missing or unsupported")
    endian = ">" if message.is_bigendian else "<"
    point_count = int(writable.nbytes // message.point_step)
    return np.ndarray(
        shape=(point_count,),
        dtype=np.dtype(endian + FIELD_DTYPES[field.datatype]),
        buffer=writable,
        offset=field.offset,
        strides=(message.point_step,),
    )


def perturb_lidar(message: PointCloud2, params: dict, severity: float,
                  rng: np.random.Generator, mode: str) -> PointCloud2:
    count = message.width * message.height
    if count == 0:
        return message
    records = np.frombuffer(message.data, dtype=np.uint8).reshape(count, message.point_step).copy()
    flat = records.reshape(-1)
    x = field_view(message, "x", flat)
    y = field_view(message, "y", flat)
    z = field_view(message, "z", flat)
    ranges = np.sqrt(x.astype(np.float64) ** 2 + y.astype(np.float64) ** 2 + z.astype(np.float64) ** 2)
    finite_xyz = np.isfinite(ranges) & (ranges > 1.0e-6)

    maximum_range = float(params.get("maximum_usable_range_m", np.inf))
    base_dropout = severity * float(params.get("dropout_percentage", 0.0)) / 100.0
    dropout_probability = np.full(count, np.clip(base_dropout, 0.0, 1.0))
    extinction = severity * float(params.get("extinction_coefficient_per_m", 0.0))
    if extinction > 0.0:
        dropout_probability = 1.0 - (1.0 - dropout_probability) * np.exp(-extinction * ranges)
    keep = finite_xyz & (ranges <= maximum_range) & (rng.random(count) >= dropout_probability)

    noise_std = severity * float(params.get("range_noise_std_m", 0.0))
    if noise_std > 0.0:
        selected = np.flatnonzero(keep)
        noisy_range = np.maximum(0.05, ranges[selected] + rng.normal(0.0, noise_std, len(selected)))
        scale = noisy_range / ranges[selected]
        x[selected] *= scale.astype(x.dtype)
        y[selected] *= scale.astype(y.dtype)
        z[selected] *= scale.astype(z.dtype)

    intensity_field = next((item for item in message.fields if item.name == "intensity"), None)
    if intensity_field is not None:
        intensity = field_view(message, "intensity", flat)
        attenuation = np.clip(severity * float(params.get("intensity_attenuation", 0.0)), 0.0, 1.0)
        if mode == "fog" and extinction > 0.0:
            factor = (1.0 - attenuation) * np.exp(-extinction * ranges)
        else:
            factor = np.full(count, 1.0 - attenuation)
        intensity[:] = np.clip(intensity.astype(np.float64) * factor, 0.0,
                               np.iinfo(intensity.dtype).max if np.issubdtype(intensity.dtype, np.integer) else np.inf).astype(intensity.dtype)

    kept_records = records[keep]
    false_fraction = severity * float(params.get("false_return_percentage", 0.0)) / 100.0
    false_count = min(len(kept_records), int(round(count * false_fraction)))
    if false_count > 0 and len(kept_records) > 0:
        false_records = kept_records[rng.integers(0, len(kept_records), false_count)].copy()
        false_flat = false_records.reshape(-1)
        fx = field_view(message, "x", false_flat)
        fy = field_view(message, "y", false_flat)
        fz = field_view(message, "z", false_flat)
        direction = np.column_stack((fx, fy, fz)).astype(np.float64)
        norm = np.linalg.norm(direction, axis=1)
        direction /= np.maximum(norm[:, None], 1.0e-6)
        direction += rng.normal(0.0, 0.004 if mode == "rain" else 0.002, direction.shape)
        direction /= np.maximum(np.linalg.norm(direction, axis=1)[:, None], 1.0e-6)
        false_ranges = rng.uniform(float(params.get("false_return_min_range_m", 1.0)),
                                   float(params.get("false_return_max_range_m", 15.0)), false_count)
        xyz = direction * false_ranges[:, None]
        fx[:], fy[:], fz[:] = xyz[:, 0], xyz[:, 1], xyz[:, 2]
        if intensity_field is not None:
            fi = field_view(message, "intensity", false_flat)
            if np.issubdtype(fi.dtype, np.integer):
                fi[:] = rng.integers(0, max(2, int(np.iinfo(fi.dtype).max * 0.03)), false_count)
            else:
                fi[:] = rng.uniform(0.0, 3.0, false_count)
        kept_records = np.concatenate((kept_records, false_records), axis=0)

    output = copy.copy(message)
    output.height = 1
    output.width = int(len(kept_records))
    output.row_step = output.point_step * output.width
    output.data = kept_records.tobytes()
    output.is_dense = message.is_dense
    return output


def image_array(message: Image) -> Tuple[np.ndarray, str]:
    encoding = message.encoding.lower()
    if encoding in ("rgb8", "bgr8"):
        channels, dtype = 3, np.uint8
    elif encoding in ("mono8", "8uc1"):
        channels, dtype = 1, np.uint8
    elif encoding in ("16uc1", "mono16"):
        channels, dtype = 1, np.dtype(">u2" if message.is_bigendian else "<u2")
    elif encoding == "32fc1":
        channels, dtype = 1, np.dtype(">f4" if message.is_bigendian else "<f4")
    else:
        raise ValueError(f"unsupported image encoding {message.encoding!r}")
    row_values = message.step // np.dtype(dtype).itemsize
    raw = np.frombuffer(message.data, dtype=dtype).reshape(message.height, row_values)
    width_values = message.width * channels
    array = raw[:, :width_values].copy()
    if channels > 1:
        array = array.reshape(message.height, message.width, channels)
    return array, encoding


def pack_image(message: Image, array: np.ndarray) -> Image:
    output = copy.copy(message)
    contiguous = np.ascontiguousarray(array)
    output.step = int(contiguous.strides[0])
    output.data = contiguous.tobytes()
    return output


def perturb_camera(message: Image, params: dict, severity: float,
                   rng: np.random.Generator) -> Image:
    array, encoding = image_array(message)
    if array.dtype != np.uint8:
        return message
    strength = np.clip(severity * float(params.get("degradation_strength", 0.0)), 0.0, 1.0)
    atmospheric = 255.0 * np.clip(float(params.get("atmospheric_light", 0.85)), 0.0, 1.0)
    # A smooth vertical transmission gradient approximates thicker haze toward
    # the horizon without requiring scene depth or altering camera geometry.
    rows = np.linspace(0.65, 1.0, message.height, dtype=np.float32)[:, None]
    transmission = np.clip(1.0 - strength * rows, 0.08, 1.0)
    if array.ndim == 3:
        transmission = transmission[:, :, None]
    degraded = array.astype(np.float32) * transmission + atmospheric * (1.0 - transmission)
    sigma = severity * float(params.get("blur_sigma_px", 0.0))
    if sigma > 0.05:
        degraded = cv2.GaussianBlur(degraded, (0, 0), sigmaX=sigma, sigmaY=sigma)
    # Low-amplitude veiling-luminance variation avoids an unrealistically flat
    # constant overlay while remaining deterministic.
    veil = cv2.GaussianBlur(rng.normal(0.0, 2.0 * strength, (message.height, message.width)).astype(np.float32),
                            (0, 0), sigmaX=25.0)
    if degraded.ndim == 3:
        veil = veil[:, :, None]
    degraded = np.clip(degraded + veil, 0, 255).astype(np.uint8)
    return pack_image(message, degraded)


def perturb_depth(message: Image, params: dict, severity: float,
                  rng: np.random.Generator) -> Image:
    depth, encoding = image_array(message)
    if encoding not in ("16uc1", "mono16", "32fc1"):
        return message
    depth = depth.copy()
    metres = depth.astype(np.float64) * (0.001 if depth.dtype.itemsize == 2 else 1.0)
    maximum = float(params.get("depth_maximum_usable_range_m", np.inf))
    dropout = np.clip(severity * float(params.get("depth_dropout_percentage", 0.0)) / 100.0, 0.0, 1.0)
    invalid = (metres > maximum) | (rng.random(depth.shape) < dropout)
    depth[invalid] = 0
    return pack_image(message, depth)


def perturb_gps(message: NavSatFix, params: dict, severity: float,
                rng: np.random.Generator) -> NavSatFix:
    output = copy.deepcopy(message)
    latitude_rad = math.radians(output.latitude)
    east = severity * (float(params.get("multipath_bias_east_m", 0.0)) +
                       rng.normal(0.0, float(params.get("horizontal_noise_std_m", 0.0))))
    north = severity * (float(params.get("multipath_bias_north_m", 0.0)) +
                        rng.normal(0.0, float(params.get("horizontal_noise_std_m", 0.0))))
    up = severity * (float(params.get("multipath_bias_up_m", 0.0)) +
                     rng.normal(0.0, float(params.get("vertical_noise_std_m", 0.0))))
    earth_radius = 6378137.0
    output.latitude += math.degrees(north / earth_radius)
    output.longitude += math.degrees(east / (earth_radius * max(0.1, math.cos(latitude_rad))))
    output.altitude += up
    if len(output.position_covariance) == 9:
        covariance = list(output.position_covariance)
        h_var = (severity * float(params.get("horizontal_noise_std_m", 0.0))) ** 2
        v_var = (severity * float(params.get("vertical_noise_std_m", 0.0))) ** 2
        covariance[0] += h_var
        covariance[4] += h_var
        covariance[8] += v_var
        output.position_covariance = covariance
    return output


class ImuPerturber:
    def __init__(self, params: dict, severity: float, rng: np.random.Generator):
        self.params, self.severity, self.rng = params, severity, rng
        self.gyro_walk = np.zeros(3)
        self.accel_walk = np.zeros(3)
        self.previous_stamp: Optional[float] = None

    def __call__(self, message: Imu) -> Imu:
        output = copy.deepcopy(message)
        stamp = output.header.stamp.to_sec()
        dt = max(0.0, min(0.1, stamp - self.previous_stamp)) if self.previous_stamp is not None else 0.0
        self.previous_stamp = stamp
        self.gyro_walk += self.rng.normal(0.0, self.severity * float(self.params.get("bias_random_walk_std_rad_s_sqrt_s", 0.0)) * math.sqrt(dt), 3)
        self.accel_walk += self.rng.normal(0.0, self.severity * float(self.params.get("accel_bias_random_walk_std_m_s2_sqrt_s", 0.0)) * math.sqrt(dt), 3)
        gyro_bias = self.severity * np.asarray(self.params.get("angular_velocity_bias_rad_s", [0, 0, 0]), dtype=float) + self.gyro_walk
        accel_bias = self.severity * np.asarray(self.params.get("linear_acceleration_bias_m_s2", [0, 0, 0]), dtype=float) + self.accel_walk
        gyro = np.array([output.angular_velocity.x, output.angular_velocity.y, output.angular_velocity.z])
        accel = np.array([output.linear_acceleration.x, output.linear_acceleration.y, output.linear_acceleration.z])
        gyro += gyro_bias + self.rng.normal(0.0, self.severity * float(self.params.get("angular_velocity_noise_std_rad_s", 0.0)), 3)
        accel += accel_bias + self.rng.normal(0.0, self.severity * float(self.params.get("linear_acceleration_noise_std_m_s2", 0.0)), 3)
        output.angular_velocity.x, output.angular_velocity.y, output.angular_velocity.z = gyro
        output.linear_acceleration.x, output.linear_acceleration.y, output.linear_acceleration.z = accel
        gyro_var = (self.severity * float(self.params.get("angular_velocity_noise_std_rad_s", 0.0))) ** 2
        accel_var = (self.severity * float(self.params.get("linear_acceleration_noise_std_m_s2", 0.0))) ** 2
        for covariance, variance in ((output.angular_velocity_covariance, gyro_var),
                                     (output.linear_acceleration_covariance, accel_var)):
            if len(covariance) == 9 and covariance[0] >= 0.0:
                updated = list(covariance)
                updated[0] += variance; updated[4] += variance; updated[8] += variance
                if covariance is output.angular_velocity_covariance:
                    output.angular_velocity_covariance = updated
                else:
                    output.linear_acceleration_covariance = updated
        return output


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def generate(input_path: Path, output_path: Path, scenario_name: str,
             root_config: dict, overwrite: bool) -> dict:
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"output exists (use --overwrite): {output_path}")
    scenario = root_config["scenarios"][scenario_name]
    seed = int(root_config.get("random_seed", 0)) + {"rain": 101, "fog": 202, "sensor_degradation": 303}[scenario_name]
    rng = np.random.default_rng(seed)
    topics = root_config["topics"]
    with rosbag.Bag(str(input_path), "r") as source:
        bag_start, bag_end = source.get_start_time(), source.get_end_time()
        start, end, severity = validate_interval(scenario, bag_end - bag_start)
        absolute_start, absolute_end = bag_start + start, bag_start + end
        imu_perturber = ImuPerturber(scenario.get("imu", {}), severity, rng)
        counts: Dict[str, Dict[str, int]] = {}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with rosbag.Bag(str(output_path), "w", compression=source.compression) as destination:
            for topic, message, record_time, connection_header in source.read_messages(return_connection_header=True):
                stats = counts.setdefault(topic, {"read": 0, "written": 0, "modified": 0, "dropped": 0})
                stats["read"] += 1
                event = record_time.to_sec()
                active = absolute_start <= event <= absolute_end
                output = message
                drop = False
                try:
                    if active and scenario_name in ("rain", "fog") and topic in topic_set(topics, "lidar"):
                        output = perturb_lidar(message, scenario["lidar"], severity, rng, scenario_name)
                    elif active and scenario_name == "fog" and topic in topic_set(topics, "camera"):
                        output = perturb_camera(message, scenario["camera"], severity, rng)
                    elif active and scenario_name == "fog" and topic in topic_set(topics, "depth"):
                        output = perturb_depth(message, scenario["camera"], severity, rng)
                    elif active and scenario_name == "sensor_degradation" and topic in topic_set(topics, "gps"):
                        gps = scenario["gps"]
                        outage_start = bag_start + float(gps.get("outage_start_time", start))
                        outage_end = bag_start + float(gps.get("outage_end_time", end))
                        drop = bool(gps.get("drop_messages_during_outage", True) and outage_start <= event <= outage_end)
                        if not drop:
                            output = perturb_gps(message, gps, severity, rng)
                    elif active and scenario_name == "sensor_degradation" and topic in topic_set(topics, "imu"):
                        output = imu_perturber(message)
                except (TypeError, ValueError) as exc:
                    raise RuntimeError(f"{scenario_name}: failed to perturb {topic} at {event:.9f}: {exc}") from exc
                if drop:
                    stats["dropped"] += 1
                    continue
                if output is not message:
                    stats["modified"] += 1
                destination.write(topic, output, record_time, connection_header=connection_header)
                stats["written"] += 1
    manifest = {
        "schema_version": 1,
        "scenario": scenario_name,
        "seed": seed,
        "source_bag": str(input_path.resolve()),
        "source_sha256": sha256_file(input_path),
        "output_bag": str(output_path.resolve()),
        "output_sha256": sha256_file(output_path),
        "bag_start_time": bag_start,
        "bag_end_time": bag_end,
        "perturbation_start_time_relative_s": start,
        "perturbation_end_time_relative_s": end,
        "perturbation_start_time_absolute_s": absolute_start,
        "perturbation_end_time_absolute_s": absolute_end,
        "severity": severity,
        "topic_counts": counts,
        "ground_truth_modified": False,
        "parameters": scenario,
    }
    output_path.with_suffix(output_path.suffix + ".manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--scenario", required=True,
                        choices=("rain", "fog", "sensor_degradation"))
    parser.add_argument("--input")
    parser.add_argument("--output")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    input_path = Path(args.input or config["input_bag"]).resolve()
    if not input_path.is_file():
        raise SystemExit(f"input bag not found: {input_path}")
    output_dir = Path(config.get("output_directory", "robustness/bags"))
    if not output_dir.is_absolute():
        output_dir = (config_path.parents[2] / output_dir).resolve()
    output_path = Path(args.output).resolve() if args.output else output_dir / config["scenarios"][args.scenario]["output_bag"]
    manifest = generate(input_path, output_path, args.scenario, config, args.overwrite)
    print(json.dumps({key: manifest[key] for key in ("scenario", "output_bag", "output_sha256")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
