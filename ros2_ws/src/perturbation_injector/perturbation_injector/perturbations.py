from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional

import numpy as np


def _clone(msg: Any) -> Any:
    return copy.deepcopy(msg)


def _as_points(msg: Any) -> Optional[np.ndarray]:
    if isinstance(msg, dict) and "points" in msg:
        return np.asarray(msg["points"], dtype=float)
    if hasattr(msg, "points"):
        return np.asarray(msg.points, dtype=float)
    return None


def _set_points(msg: Any, points: np.ndarray) -> Any:
    if isinstance(msg, dict):
        msg["points"] = points.tolist()
    else:
        msg.points = points
    return msg


def _as_image(msg: Any) -> Optional[np.ndarray]:
    if isinstance(msg, dict) and "image" in msg:
        return np.asarray(msg["image"], dtype=np.uint8)
    if hasattr(msg, "image"):
        return np.asarray(msg.image, dtype=np.uint8)
    return None


def _set_image(msg: Any, image: np.ndarray) -> Any:
    image = np.clip(image, 0, 255).astype(np.uint8)
    if isinstance(msg, dict):
        msg["image"] = image
    else:
        msg.image = image
    return msg


def _vector_get(msg: Any, key: str, default: Iterable[float]) -> np.ndarray:
    if isinstance(msg, dict):
        return np.asarray(msg.get(key, default), dtype=float)
    return np.asarray(getattr(msg, key, default), dtype=float)


def _vector_set(msg: Any, key: str, value: np.ndarray) -> Any:
    if isinstance(msg, dict):
        msg[key] = value.tolist()
    else:
        setattr(msg, key, value)
    return msg


def _time_s(msg: Any) -> float:
    if isinstance(msg, dict):
        return float(msg.get("t", msg.get("stamp", 0.0)))
    return float(getattr(msg, "t", getattr(msg, "stamp", 0.0)))


def _within_window(msg: Any, params: Dict[str, Any]) -> bool:
    if "start_time" not in params and "end_time" not in params:
        return True
    t = _time_s(msg)
    return float(params.get("start_time", -math.inf)) <= t <= float(params.get("end_time", math.inf))


class Perturbation:
    """Base perturbation class used by ROS and non-ROS test paths."""

    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        raise NotImplementedError


class LidarGaussianNoise(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        pts = _as_points(out)
        if pts is None or len(pts) == 0:
            return out
        pts[:, :3] += np.random.normal(0.0, float(params["noise_std"]), pts[:, :3].shape)
        return _set_points(out, pts)


class LidarPointDropout(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        if not _within_window(msg, params):
            return msg
        out = _clone(msg)
        pts = _as_points(out)
        if pts is None or len(pts) == 0:
            return out
        keep = np.random.random(len(pts)) >= float(params["dropout_fraction"])
        return _set_points(out, pts[keep])


class LidarIntensityScale(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        pts = _as_points(out)
        if pts is not None and pts.shape[1] >= 4:
            pts[:, 3] *= float(params["intensity_scale"])
            return _set_points(out, pts)
        return out


class LidarBeamOcclusion(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        pts = _as_points(out)
        if pts is None or len(pts) == 0:
            return out
        mask = np.ones(len(pts), dtype=bool)
        for axis, bounds in enumerate(params.get("regions", [])):
            if len(bounds) == 2:
                mask &= ~((pts[:, axis] >= bounds[0]) & (pts[:, axis] <= bounds[1]))
        return _set_points(out, pts[mask])


class LidarAzimuthOcclusion(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        pts = _as_points(out)
        if pts is None or len(pts) == 0:
            return out
        az = (np.degrees(np.arctan2(pts[:, 1], pts[:, 0])) + 360.0) % 360.0
        start, end = float(params["azimuth_start"]), float(params["azimuth_end"])
        sector = (az >= start) & (az <= end) if start <= end else ((az >= start) | (az <= end))
        drop = sector & (np.random.random(len(pts)) < float(params["point_drop_ratio"]))
        return _set_points(out, pts[~drop])


class LidarReflectiveGhosts(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        pts = _as_points(out)
        if pts is None or len(pts) == 0:
            return out
        region = (
            (pts[:, 0] >= float(params["x_min"]))
            & (pts[:, 0] <= float(params["x_max"]))
            & (pts[:, 1] >= float(params["y_min"]))
            & (pts[:, 1] <= float(params["y_max"]))
        )
        real = pts[region]
        keep = np.ones(len(pts), dtype=bool)
        keep[region] = np.random.random(region.sum()) >= float(params["point_drop_ratio"])
        ghost_n = int(len(real) * float(params["ghost_point_ratio"]))
        if ghost_n:
            idx = np.random.choice(len(real), ghost_n, replace=len(real) < ghost_n)
            ghosts = real[idx].copy()
            ghosts[:, :3] += np.random.normal(0.0, float(params["noise_std"]), ghosts[:, :3].shape)
            pts = np.vstack([pts[keep], ghosts])
        else:
            pts = pts[keep]
        return _set_points(out, pts)


class LidarFogAttenuation(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        pts = _as_points(out)
        if pts is None or len(pts) == 0:
            return out
        dist = np.linalg.norm(pts[:, :3], axis=1)
        far = dist > float(params["visibility_distance"])
        drop = far & (np.random.random(len(pts)) < float(params["point_drop_ratio"]))
        pts = pts[~drop]
        if pts.shape[1] >= 4:
            pts[:, 3] *= float(params["intensity_scale"])
        ghost_n = int(len(pts) * float(params.get("backscatter_ratio", 0.0)))
        if ghost_n:
            ghosts = pts[np.random.choice(len(pts), ghost_n, replace=True)].copy()
            ghosts[:, :3] *= np.random.uniform(0.05, 0.35, (ghost_n, 1))
            pts = np.vstack([pts, ghosts])
        return _set_points(out, pts)


class LidarVibration(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        pts = _as_points(out)
        if pts is None or len(pts) == 0:
            return out
        yaw = math.radians(np.random.normal(0.0, float(params["yaw_sigma_deg"])))
        rot = np.array([[math.cos(yaw), -math.sin(yaw), 0.0], [math.sin(yaw), math.cos(yaw), 0.0], [0.0, 0.0, 1.0]])
        pts[:, :3] = pts[:, :3] @ rot.T + np.random.normal(0.0, float(params["position_sigma"]), (1, 3))
        return _set_points(out, pts)


class CameraBrightnessNoise(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        image = _as_image(out)
        if image is None:
            return out
        image = image.astype(float) * float(params["brightness_factor"])
        image += np.random.normal(0.0, float(params["noise_std"]), image.shape)
        return _set_image(out, image)


class CameraGlare(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        image = _as_image(out)
        if image is None:
            return out
        image = image.astype(float)
        mask = image > int(params["intensity_threshold"])
        image[mask] *= float(params["brightness_scale"])
        return _set_image(out, image)


class CameraMotionBlur(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        return _box_blur(msg, int(params["blur_kernel"]))


class CameraExposureShift(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        image = _as_image(out)
        if image is None:
            return out
        return _set_image(out, image.astype(float) * (2.0 ** float(params["exposure_shift"])))


class CameraRainDroplets(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        image = _as_image(out)
        if image is None:
            return out
        image = image.astype(float) * float(params.get("contrast_scale", 1.0))
        h, w = image.shape[:2]
        intensity = float(params["intensity"])
        for _ in range(int(params["droplet_count"])):
            x, y = random.randrange(w), random.randrange(h)
            length = int(params["streak_length"])
            image[max(0, y - length): y + 1, x: min(w, x + 2)] += 160 * intensity
        return _box_blur(_set_image(out, image), int(params["droplet_blur_kernel"]))


class CameraLensFlare(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        image = _as_image(out)
        if image is None:
            return out
        h, w = image.shape[:2]
        yy, xx = np.mgrid[:h, :w]
        cx, cy = int(w * 0.75), int(h * 0.25)
        flare = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / max(1.0, (0.12 * w) ** 2)))
        if image.ndim == 3:
            flare = flare[..., None]
        return _set_image(out, image.astype(float) + 255.0 * float(params["intensity"]) * flare)


class CameraFoliageMask(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        image = _as_image(out)
        if image is None:
            return out
        x0, x1 = int(params["x_min"]), int(params["x_max"])
        y0, y1 = int(params["y_min"]), int(params["y_max"])
        image = image.copy().astype(float)
        image[y0:y1, x0:x1] *= 1.0 - float(params["opacity"])
        return _set_image(out, image)


class CameraFogHaze(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        image = _as_image(out)
        if image is None:
            return out
        attenuated = image.astype(float) * math.exp(-float(params["density"]))
        haze = 220.0 * float(params["overlay_opacity"])
        return _set_image(out, attenuated + haze)


class CameraTunnelTransition(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        image = _as_image(out)
        if image is None:
            return out
        start, end = float(params["start_time"]), float(params["end_time"])
        frac = min(1.0, max(0.0, (_time_s(msg) - start) / max(1e-6, end - start)))
        scale = float(params["brightness_start"]) + frac * (float(params["brightness_end"]) - float(params["brightness_start"]))
        return _set_image(out, image.astype(float) * scale)


@dataclass
class CameraFrozenFrames(Perturbation):
    previous: Any = None

    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        if _within_window(msg, params) and self.previous is not None and random.random() < float(params["freeze_ratio"]):
            return _clone(self.previous)
        self.previous = _clone(msg)
        return msg


class CameraVibrationBlur(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        return _box_blur(msg, int(params["blur_kernel"]))


def _box_blur(msg: Any, kernel: int) -> Any:
    out = _clone(msg)
    image = _as_image(out)
    if image is None or kernel <= 1:
        return out
    kernel = kernel if kernel % 2 else kernel + 1
    pad = kernel // 2
    padded = np.pad(image.astype(float), [(pad, pad), (pad, pad)] + ([(0, 0)] if image.ndim == 3 else []), mode="edge")
    blurred = np.zeros_like(image, dtype=float)
    for dy in range(kernel):
        for dx in range(kernel):
            blurred += padded[dy: dy + image.shape[0], dx: dx + image.shape[1]]
    return _set_image(out, blurred / (kernel * kernel))


class ImuGyroBias(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        return _vector_set(out, "gyro", _vector_get(out, "gyro", [0, 0, 0]) + np.asarray(params["gyro_bias"], dtype=float))


class ImuAccelNoise(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        return _vector_set(out, "accel", _vector_get(out, "accel", [0, 0, 0]) + np.random.normal(0.0, float(params["accel_noise"]), 3))


@dataclass
class ImuAccelBiasDrift(Perturbation):
    bias: np.ndarray = field(default_factory=lambda: np.zeros(3))

    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        self.bias += np.random.normal(0.0, float(params["accel_bias_drift"]), 3)
        return _vector_set(out, "accel", _vector_get(out, "accel", [0, 0, 0]) + self.bias)


class ImuBiasDriftLinear(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        t = _time_s(out)
        out = _vector_set(out, "gyro", _vector_get(out, "gyro", [0, 0, 0]) + t * float(params["gyro_drift_rate"]))
        return _vector_set(out, "accel", _vector_get(out, "accel", [0, 0, 0]) + t * float(params["accel_drift_rate"]))


class ImuTemperatureScaleFactor(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        eps = 1.0 + float(params["scale_factor_error"])
        out = _vector_set(out, "gyro", _vector_get(out, "gyro", [0, 0, 0]) * eps)
        return _vector_set(out, "accel", _vector_get(out, "accel", [0, 0, 0]) * eps)


class ImuVibrationNoise(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        out = _vector_set(out, "accel", _vector_get(out, "accel", [0, 0, 0]) + np.random.normal(0.0, float(params["accel_noise_std"]), 3))
        return _vector_set(out, "gyro", _vector_get(out, "gyro", [0, 0, 0]) + np.random.normal(0.0, float(params["gyro_noise_std"]), 3))


@dataclass
class ImuFrozen(Perturbation):
    previous: Any = None

    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        if _within_window(msg, params) and self.previous is not None and random.random() < float(params["freeze_ratio"]):
            return _clone(self.previous)
        self.previous = _clone(msg)
        return msg


class GpsDropout(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        return None if random.random() < float(params["drop_probability"]) else msg


class GpsMultipath(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        t = _time_s(out)
        meters = float(params["amplitude"]) * math.sin(2.0 * math.pi * float(params["frequency"]) * t)
        delta_deg = meters / 111_111.0
        if isinstance(out, dict):
            out["latitude"] = float(out.get("latitude", 0.0)) + delta_deg
            out["longitude"] = float(out.get("longitude", 0.0)) + delta_deg
        return out


class GpsPartialFailure(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        if _within_window(msg, params) and random.random() < float(params["message_drop_ratio"]):
            return None
        return msg


class GlobalTimeOffset(Perturbation):
    def apply(self, msg: Any, params: Dict[str, Any]) -> Any:
        out = _clone(msg)
        offset = float(params["time_offset"])
        if isinstance(out, dict):
            out["t"] = _time_s(out) + offset
        return out


REGISTRY = {
    "gaussian_noise": LidarGaussianNoise,
    "point_dropout": LidarPointDropout,
    "intensity_scale": LidarIntensityScale,
    "beam_occlusion": LidarBeamOcclusion,
    "azimuth_occlusion": LidarAzimuthOcclusion,
    "reflective_ghosts": LidarReflectiveGhosts,
    "fog_attenuation": LidarFogAttenuation,
    "vibration": LidarVibration,
    "brightness_noise": CameraBrightnessNoise,
    "glare": CameraGlare,
    "motion_blur": CameraMotionBlur,
    "exposure_shift": CameraExposureShift,
    "rain_droplets": CameraRainDroplets,
    "lens_flare": CameraLensFlare,
    "foliage_mask": CameraFoliageMask,
    "fog_haze": CameraFogHaze,
    "tunnel_transition": CameraTunnelTransition,
    "frozen_frames": CameraFrozenFrames,
    "vibration_blur": CameraVibrationBlur,
    "gyro_bias": ImuGyroBias,
    "accel_noise": ImuAccelNoise,
    "accel_bias_drift": ImuAccelBiasDrift,
    "bias_drift_linear": ImuBiasDriftLinear,
    "temperature_scale_factor": ImuTemperatureScaleFactor,
    "vibration_noise": ImuVibrationNoise,
    "frozen": ImuFrozen,
    "dropout": GpsDropout,
    "multipath": GpsMultipath,
    "partial_failure": GpsPartialFailure,
    "time_offset": GlobalTimeOffset,
}


def build_chain(spec: Dict[str, Any]) -> Dict[str, list[tuple[Perturbation, Dict[str, Any]]]]:
    chains: Dict[str, list[tuple[Perturbation, Dict[str, Any]]]] = {}
    for sensor, perturbations in spec.get("perturbations", {}).items():
        chains[sensor] = []
        for name, params in (perturbations or {}).items():
            if not isinstance(params, dict) or not params.get("enabled", False):
                continue
            cls = REGISTRY.get(name)
            if cls is None:
                continue
            clean_params = {k: v for k, v in params.items() if k != "enabled"}
            chains[sensor].append((cls(), clean_params))
    return chains


def apply_chain(msg: Any, chain: list[tuple[Perturbation, Dict[str, Any]]]) -> Any:
    out = msg
    for perturbation, params in chain:
        if out is None:
            return None
        out = perturbation.apply(out, params)
    return out
