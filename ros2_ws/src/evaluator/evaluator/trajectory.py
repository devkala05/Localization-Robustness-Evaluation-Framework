from __future__ import annotations

import math
from pathlib import Path
from typing import Tuple

import numpy as np


def load_tum(path: str | Path) -> np.ndarray:
    rows = []
    with Path(path).open() as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            vals = [float(x) for x in line.split()]
            if len(vals) >= 8:
                rows.append(vals[:8])
    if not rows:
        raise ValueError(f"no TUM poses found in {path}")
    return np.asarray(rows, dtype=float)


def save_tum(path: str | Path, poses: np.ndarray) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w") as handle:
        for row in poses:
            handle.write(" ".join(f"{value:.9f}" for value in row) + "\n")


def synthetic_trajectory(duration_s: float, rate_hz: float, noise_m: float, yaw_noise_deg: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(0.0, duration_s, 1.0 / rate_hz)
    x = 0.9 * t
    y = 2.0 * np.sin(t / 18.0)
    z = 0.15 * np.sin(t / 30.0)
    x += rng.normal(0.0, noise_m, len(t))
    y += rng.normal(0.0, noise_m, len(t))
    z += rng.normal(0.0, noise_m * 0.4, len(t))
    yaw = np.arctan2(np.gradient(y), np.gradient(x)) + rng.normal(0.0, math.radians(yaw_noise_deg), len(t))
    qz = np.sin(yaw / 2.0)
    qw = np.cos(yaw / 2.0)
    return np.column_stack([t, x, y, z, np.zeros_like(t), np.zeros_like(t), qz, qw])


def interpolate_positions(reference: np.ndarray, target_times: np.ndarray) -> np.ndarray:
    return np.column_stack([np.interp(target_times, reference[:, 0], reference[:, axis]) for axis in (1, 2, 3)])


def yaw_from_quat(q: np.ndarray) -> np.ndarray:
    qx, qy, qz, qw = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    return np.arctan2(siny_cosp, cosy_cosp)


def interpolate_yaw(reference: np.ndarray, target_times: np.ndarray) -> np.ndarray:
    yaw = np.unwrap(yaw_from_quat(reference[:, 4:8]))
    return np.interp(target_times, reference[:, 0], yaw)


def umeyama_align(source: np.ndarray, target: np.ndarray, allow_translation: bool = False) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    src_mean = source.mean(axis=0)
    tgt_mean = target.mean(axis=0)
    src_c = source - src_mean
    tgt_c = target - tgt_mean
    cov = src_c.T @ tgt_c / len(source)
    u, _, vt = np.linalg.svd(cov)
    d = np.eye(3)
    if np.linalg.det(u @ vt) < 0:
        d[-1, -1] = -1
    rot = u @ d @ vt
    trans = tgt_mean - src_mean @ rot.T if allow_translation else np.zeros(3)
    aligned = source @ rot.T + trans
    return aligned, rot, trans


def wrap_angle_rad(angle: np.ndarray) -> np.ndarray:
    return (angle + np.pi) % (2.0 * np.pi) - np.pi
