#!/usr/bin/env python3
from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ros2_ws/src/perturbation_injector"))

from perturbation_injector.perturbations import (  # noqa: E402
    CameraBrightnessNoise,
    CameraExposureShift,
    CameraFogHaze,
    CameraFoliageMask,
    CameraFrozenFrames,
    CameraGlare,
    CameraLensFlare,
    CameraMotionBlur,
    CameraRainDroplets,
    CameraTunnelTransition,
    CameraVibrationBlur,
    GlobalTimeOffset,
    GpsDropout,
    GpsMultipath,
    GpsPartialFailure,
    ImuAccelBiasDrift,
    ImuAccelNoise,
    ImuBiasDriftLinear,
    ImuFrozen,
    ImuGyroBias,
    ImuTemperatureScaleFactor,
    ImuVibrationNoise,
    LidarAzimuthOcclusion,
    LidarBeamOcclusion,
    LidarFogAttenuation,
    LidarGaussianNoise,
    LidarIntensityScale,
    LidarPointDropout,
    LidarReflectiveGhosts,
    LidarVibration,
)


def lidar_msg(n: int = 1000) -> dict:
    rng = np.random.default_rng(7)
    xyz = rng.uniform([-20, -20, -2], [20, 20, 3], size=(n, 3))
    intensity = np.full((n, 1), 100.0)
    return {"t": 10.0, "points": np.hstack([xyz, intensity]).tolist()}


def image_msg() -> dict:
    image = np.tile(np.linspace(20, 240, 96, dtype=np.uint8), (64, 1))
    return {"t": 25.0, "image": image}


def imu_msg() -> dict:
    return {"t": 10.0, "gyro": [0.1, 0.2, 0.3], "accel": [1.0, 2.0, 9.8]}


def gps_msg() -> dict:
    return {"t": 10.0, "latitude": 49.0, "longitude": 8.0}


def arr_points(msg: dict) -> np.ndarray:
    return np.asarray(msg["points"], dtype=float)


def arr_image(msg: dict) -> np.ndarray:
    return np.asarray(msg["image"], dtype=np.uint8)


def report(name: str, ok: bool, detail: str) -> bool:
    status = "PASS" if ok else "FAIL"
    print(f"{name:<28} [{status}] {detail}")
    return ok


def main() -> int:
    np.random.seed(3)
    checks: list[bool] = []

    msg = lidar_msg()
    out = LidarPointDropout().apply(copy.deepcopy(msg), {"dropout_fraction": 0.2})
    checks.append(report("LidarPointDropout", len(out["points"]) < len(msg["points"]), f"{len(msg['points'])} -> {len(out['points'])} points"))

    msg = lidar_msg()
    before = arr_points(msg)[:, :3]
    out = LidarGaussianNoise().apply(copy.deepcopy(msg), {"noise_std": 0.02})
    delta = np.linalg.norm(arr_points(out)[:, :3] - before, axis=1).mean()
    checks.append(report("LidarGaussianNoise", 0.005 < delta < 0.08, f"mean position change {delta:.4f} m"))

    msg = lidar_msg()
    out = LidarIntensityScale().apply(copy.deepcopy(msg), {"intensity_scale": 0.8})
    checks.append(report("LidarIntensityScale", np.isclose(arr_points(out)[:, 3].mean(), 80.0), f"mean intensity {arr_points(out)[:, 3].mean():.1f}"))

    msg = lidar_msg()
    out = LidarBeamOcclusion().apply(copy.deepcopy(msg), {"regions": [[-5, 5], [-5, 5], [-2, 2]]})
    checks.append(report("LidarBeamOcclusion", len(out["points"]) < len(msg["points"]), f"{len(msg['points'])} -> {len(out['points'])} points"))

    msg = lidar_msg()
    out = LidarAzimuthOcclusion().apply(copy.deepcopy(msg), {"azimuth_start": 330, "azimuth_end": 30, "point_drop_ratio": 1.0})
    checks.append(report("LidarAzimuthOcclusion", len(out["points"]) < len(msg["points"]), f"{len(msg['points'])} -> {len(out['points'])} points"))

    msg = lidar_msg()
    out = LidarReflectiveGhosts().apply(copy.deepcopy(msg), {"x_min": -20, "x_max": 20, "y_min": -20, "y_max": 20, "point_drop_ratio": 0.1, "ghost_point_ratio": 0.2, "noise_std": 0.1})
    checks.append(report("LidarReflectiveGhosts", len(out["points"]) != len(msg["points"]), f"{len(msg['points'])} -> {len(out['points'])} points"))

    msg = lidar_msg()
    out = LidarFogAttenuation().apply(copy.deepcopy(msg), {"visibility_distance": 10.0, "intensity_scale": 0.7, "point_drop_ratio": 0.5, "backscatter_ratio": 0.05})
    checks.append(report("LidarFogAttenuation", len(out["points"]) < len(msg["points"]) and arr_points(out)[:, 3].mean() < 100, f"{len(msg['points'])} -> {len(out['points'])}, mean intensity {arr_points(out)[:, 3].mean():.1f}"))

    msg = lidar_msg()
    before = arr_points(msg)[:, :3]
    out = LidarVibration().apply(copy.deepcopy(msg), {"position_sigma": 0.05, "yaw_sigma_deg": 1.0})
    checks.append(report("LidarVibration", np.linalg.norm(arr_points(out)[:, :3] - before, axis=1).mean() > 0.01, "frame transform changed points"))

    msg = image_msg()
    out = CameraBrightnessNoise().apply(copy.deepcopy(msg), {"brightness_factor": 0.5, "noise_std": 2})
    checks.append(report("CameraBrightnessNoise", arr_image(out).mean() < arr_image(msg).mean(), f"mean {arr_image(msg).mean():.1f} -> {arr_image(out).mean():.1f}"))

    msg = image_msg()
    out = CameraGlare().apply(copy.deepcopy(msg), {"intensity_threshold": 160, "brightness_scale": 1.4})
    checks.append(report("CameraGlare", arr_image(out).max() >= arr_image(msg).max(), f"max {arr_image(msg).max()} -> {arr_image(out).max()}"))

    msg = {"t": 0.0, "image": np.zeros((32, 32), dtype=np.uint8)}
    msg["image"][16, 16] = 255
    out = CameraMotionBlur().apply(copy.deepcopy(msg), {"blur_kernel": 5})
    checks.append(report("CameraMotionBlur", arr_image(out)[16, 16] < 255 and arr_image(out).sum() > 0, "impulse blurred"))

    msg = image_msg()
    out = CameraExposureShift().apply(copy.deepcopy(msg), {"exposure_shift": -1.0})
    checks.append(report("CameraExposureShift", arr_image(out).mean() < arr_image(msg).mean(), f"mean {arr_image(msg).mean():.1f} -> {arr_image(out).mean():.1f}"))

    msg = image_msg()
    out = CameraRainDroplets().apply(copy.deepcopy(msg), {"intensity": 0.8, "streak_length": 8, "contrast_scale": 0.9, "droplet_count": 30, "droplet_blur_kernel": 5})
    checks.append(report("CameraRainDroplets", not np.array_equal(arr_image(out), arr_image(msg)), "image changed"))

    msg = image_msg()
    out = CameraLensFlare().apply(copy.deepcopy(msg), {"intensity": 0.6})
    checks.append(report("CameraLensFlare", arr_image(out).mean() > arr_image(msg).mean(), f"mean {arr_image(msg).mean():.1f} -> {arr_image(out).mean():.1f}"))

    msg = image_msg()
    out = CameraFoliageMask().apply(copy.deepcopy(msg), {"x_min": 10, "x_max": 40, "y_min": 10, "y_max": 40, "opacity": 0.8})
    checks.append(report("CameraFoliageMask", arr_image(out)[10:40, 10:40].mean() < arr_image(msg)[10:40, 10:40].mean(), "masked region darkened"))

    msg = image_msg()
    out = CameraFogHaze().apply(copy.deepcopy(msg), {"density": 0.5, "overlay_opacity": 0.3})
    checks.append(report("CameraFogHaze", not np.array_equal(arr_image(out), arr_image(msg)), "atmospheric attenuation applied"))

    msg = image_msg()
    out = CameraTunnelTransition().apply(copy.deepcopy(msg), {"start_time": 20.0, "end_time": 30.0, "brightness_start": 1.0, "brightness_end": 0.2})
    checks.append(report("CameraTunnelTransition", arr_image(out).mean() < arr_image(msg).mean(), f"mean {arr_image(msg).mean():.1f} -> {arr_image(out).mean():.1f}"))

    freeze = CameraFrozenFrames()
    first = freeze.apply(copy.deepcopy({"t": 30.0, "image": np.zeros((8, 8), dtype=np.uint8)}), {"freeze_ratio": 1.0, "start_time": 30.0, "end_time": 50.0})
    second = freeze.apply(copy.deepcopy({"t": 31.0, "image": np.ones((8, 8), dtype=np.uint8) * 200}), {"freeze_ratio": 1.0, "start_time": 30.0, "end_time": 50.0})
    checks.append(report("CameraFrozenFrames", np.array_equal(arr_image(first), arr_image(second)), "second frame reused previous"))

    msg = {"t": 0.0, "image": np.zeros((32, 32), dtype=np.uint8)}
    msg["image"][16, 16] = 255
    out = CameraVibrationBlur().apply(copy.deepcopy(msg), {"blur_kernel": 5, "rotation_std_deg": 1.0})
    checks.append(report("CameraVibrationBlur", arr_image(out)[16, 16] < 255 and arr_image(out).sum() > 0, "blur applied"))

    msg = imu_msg()
    out = ImuGyroBias().apply(copy.deepcopy(msg), {"gyro_bias": [0.1, 0.1, 0.1]})
    checks.append(report("ImuGyroBias", np.allclose(out["gyro"], [0.2, 0.3, 0.4]), f"gyro {out['gyro']}"))

    msg = imu_msg()
    out = ImuAccelNoise().apply(copy.deepcopy(msg), {"accel_noise": 0.5})
    checks.append(report("ImuAccelNoise", not np.allclose(out["accel"], msg["accel"]), f"accel {out['accel']}"))

    drift = ImuAccelBiasDrift()
    out = drift.apply(copy.deepcopy(imu_msg()), {"accel_bias_drift": 0.1})
    checks.append(report("ImuAccelBiasDrift", not np.allclose(out["accel"], imu_msg()["accel"]), f"accel {out['accel']}"))

    msg = imu_msg()
    out = ImuBiasDriftLinear().apply(copy.deepcopy(msg), {"gyro_drift_rate": 0.01, "accel_drift_rate": 0.1})
    checks.append(report("ImuBiasDriftLinear", out["gyro"][0] > msg["gyro"][0] and out["accel"][0] > msg["accel"][0], "time-proportional bias added"))

    msg = imu_msg()
    out = ImuTemperatureScaleFactor().apply(copy.deepcopy(msg), {"scale_factor_error": 0.1})
    checks.append(report("ImuTemperatureScaleFactor", np.isclose(out["accel"][2], 10.78), f"accel z {out['accel'][2]:.3f}"))

    msg = imu_msg()
    out = ImuVibrationNoise().apply(copy.deepcopy(msg), {"accel_noise_std": 0.2, "gyro_noise_std": 0.05})
    checks.append(report("ImuVibrationNoise", not np.allclose(out["gyro"], msg["gyro"]) and not np.allclose(out["accel"], msg["accel"]), "accel and gyro changed"))

    freeze_imu = ImuFrozen()
    first = freeze_imu.apply(copy.deepcopy({"t": 30.0, "gyro": [1, 1, 1], "accel": [2, 2, 2]}), {"freeze_ratio": 1.0, "start_time": 30.0, "end_time": 50.0})
    second = freeze_imu.apply(copy.deepcopy({"t": 31.0, "gyro": [9, 9, 9], "accel": [9, 9, 9]}), {"freeze_ratio": 1.0, "start_time": 30.0, "end_time": 50.0})
    checks.append(report("ImuFrozen", first == second, "second sample reused previous"))

    out = GpsDropout().apply(copy.deepcopy(gps_msg()), {"drop_probability": 1.0})
    checks.append(report("GpsDropout", out is None, "message dropped at p=1.0"))

    msg = gps_msg()
    out = GpsMultipath().apply(copy.deepcopy(msg), {"amplitude": 5.0, "frequency": 0.025})
    checks.append(report("GpsMultipath", not math.isclose(out["latitude"], msg["latitude"]), f"lat {msg['latitude']} -> {out['latitude']}"))

    out = GpsPartialFailure().apply(copy.deepcopy(gps_msg()), {"start_time": 0.0, "end_time": 20.0, "message_drop_ratio": 1.0})
    checks.append(report("GpsPartialFailure", out is None, "windowed message dropped"))

    msg = gps_msg()
    out = GlobalTimeOffset().apply(copy.deepcopy(msg), {"time_offset": 0.25})
    checks.append(report("GlobalTimeOffset", math.isclose(out["t"], 10.25), f"t {msg['t']} -> {out['t']}"))

    passed = sum(checks)
    print(f"\nSummary: {passed}/{len(checks)} perturbation checks passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
