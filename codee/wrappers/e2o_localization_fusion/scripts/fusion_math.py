#!/usr/bin/env python3
"""Small, dependency-light SE(3) helpers used by the fusion wrappers."""
import math
from typing import Iterable, Sequence

import numpy as np
from geometry_msgs.msg import Pose, Quaternion


def normalize_quaternion(q: Sequence[float]) -> np.ndarray:
    out = np.asarray(q, dtype=float)
    norm = float(np.linalg.norm(out))
    if not math.isfinite(norm) or norm < 1.0e-12:
        raise ValueError("invalid zero/non-finite quaternion")
    return out / norm


def quaternion_to_matrix(q_xyzw: Sequence[float]) -> np.ndarray:
    x, y, z, w = normalize_quaternion(q_xyzw)
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return np.array([
        [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
        [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
        [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
    ], dtype=float)


def matrix_to_quaternion(R: np.ndarray) -> np.ndarray:
    """Return quaternion as x,y,z,w."""
    m = np.asarray(R, dtype=float)
    trace = float(np.trace(m))
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        q = np.array([(m[2, 1] - m[1, 2]) / s,
                      (m[0, 2] - m[2, 0]) / s,
                      (m[1, 0] - m[0, 1]) / s,
                      0.25 * s])
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
        q = np.array([0.25 * s, (m[0, 1] + m[1, 0]) / s,
                      (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s])
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
        q = np.array([(m[0, 1] + m[1, 0]) / s, 0.25 * s,
                      (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s])
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
        q = np.array([(m[0, 2] + m[2, 0]) / s,
                      (m[1, 2] + m[2, 1]) / s, 0.25 * s,
                      (m[1, 0] - m[0, 1]) / s])
    return normalize_quaternion(q)


def pose_to_matrix(pose: Pose) -> np.ndarray:
    values = [pose.position.x, pose.position.y, pose.position.z,
              pose.orientation.x, pose.orientation.y,
              pose.orientation.z, pose.orientation.w]
    if not np.all(np.isfinite(values)):
        raise ValueError("pose contains NaN or infinity")
    T = np.eye(4, dtype=float)
    T[:3, :3] = quaternion_to_matrix(values[3:7])
    T[:3, 3] = values[:3]
    return T


def matrix_to_pose(T: np.ndarray) -> Pose:
    if not np.all(np.isfinite(T)):
        raise ValueError("transform contains NaN or infinity")
    q = matrix_to_quaternion(T[:3, :3])
    out = Pose()
    out.position.x, out.position.y, out.position.z = map(float, T[:3, 3])
    out.orientation.x, out.orientation.y, out.orientation.z, out.orientation.w = map(float, q)
    return out


def invert_transform(T: np.ndarray) -> np.ndarray:
    out = np.eye(4, dtype=float)
    out[:3, :3] = T[:3, :3].T
    out[:3, 3] = -(out[:3, :3] @ T[:3, 3])
    return out


def quaternion_angle(q1_xyzw: Sequence[float], q2_xyzw: Sequence[float]) -> float:
    q1 = normalize_quaternion(q1_xyzw)
    q2 = normalize_quaternion(q2_xyzw)
    dot = min(1.0, max(-1.0, abs(float(np.dot(q1, q2)))))
    return 2.0 * math.acos(dot)


def rotation_angle(R: np.ndarray) -> float:
    value = min(1.0, max(-1.0, (float(np.trace(R)) - 1.0) * 0.5))
    return math.acos(value)


def slerp(q0_xyzw: Sequence[float], q1_xyzw: Sequence[float], alpha: float) -> np.ndarray:
    q0 = normalize_quaternion(q0_xyzw)
    q1 = normalize_quaternion(q1_xyzw)
    dot = float(np.dot(q0, q1))
    if dot < 0.0:
        q1 = -q1
        dot = -dot
    dot = min(1.0, max(-1.0, dot))
    if dot > 0.9995:
        return normalize_quaternion(q0 + alpha * (q1 - q0))
    theta = math.acos(dot)
    sin_theta = math.sin(theta)
    return (math.sin((1.0 - alpha) * theta) / sin_theta) * q0 + (math.sin(alpha * theta) / sin_theta) * q1


def interpolate_transform(T0: np.ndarray, T1: np.ndarray, alpha: float) -> np.ndarray:
    alpha = min(1.0, max(0.0, float(alpha)))
    out = np.eye(4, dtype=float)
    out[:3, 3] = (1.0 - alpha) * T0[:3, 3] + alpha * T1[:3, 3]
    out[:3, :3] = quaternion_to_matrix(slerp(matrix_to_quaternion(T0[:3, :3]), matrix_to_quaternion(T1[:3, :3]), alpha))
    return out


def average_transforms(transforms: Iterable[np.ndarray]) -> np.ndarray:
    items = list(transforms)
    if not items:
        raise ValueError("cannot average an empty transform list")
    out = np.eye(4, dtype=float)
    out[:3, 3] = np.median(np.asarray([T[:3, 3] for T in items]), axis=0)
    quats = [matrix_to_quaternion(T[:3, :3]) for T in items]
    reference = quats[0]
    aligned = [q if np.dot(q, reference) >= 0.0 else -q for q in quats]
    A = sum(np.outer(q, q) for q in aligned)
    _, vectors = np.linalg.eigh(A)
    out[:3, :3] = quaternion_to_matrix(vectors[:, -1])
    return out


def estimate_camera_to_base_similarity(pairs, camera_to_base: np.ndarray, fixed_scale: float = 0.0):
    """Estimate a similarity from monocular camera poses to metric base poses.

    ``pairs`` contains ``(T_metric_base, T_mono_camera)``. The known metric
    ``T_camera_base`` lever arm is applied after scale, so rotations of an
    off-center camera do not create a source-switch position error.

    Returns ``(T_metric_world_from_mono_world, scale, position_rmse,
    orientation_rmse_rad)``.
    """
    items = list(pairs)
    if not items:
        raise ValueError("no synchronized pose pairs")
    T_camera_base = np.asarray(camera_to_base, dtype=float)
    if T_camera_base.shape != (4, 4) or not np.all(np.isfinite(T_camera_base)):
        raise ValueError("camera_to_base must be a finite 4x4 transform")

    rotation_candidates = []
    orientation_errors = []
    for T_base, T_camera in items:
        R_candidate = T_base[:3, :3] @ (T_camera[:3, :3] @ T_camera_base[:3, :3]).T
        candidate = np.eye(4)
        candidate[:3, :3] = R_candidate
        rotation_candidates.append(candidate)
    R_align = average_transforms(rotation_candidates)[:3, :3]

    mono_points = np.asarray([R_align @ T_camera[:3, 3] for _, T_camera in items])
    metric_points = np.asarray([
        T_base[:3, 3] - R_align @ T_camera[:3, :3] @ T_camera_base[:3, 3]
        for T_base, T_camera in items
    ])
    mono_mean = mono_points.mean(axis=0)
    metric_mean = metric_points.mean(axis=0)
    X = mono_points - mono_mean
    Y = metric_points - metric_mean
    variance = float(np.sum(X * X))
    if fixed_scale > 0.0:
        scale = float(fixed_scale)
    else:
        if variance < 1.0e-4:
            raise ValueError("insufficient monocular translation for scale estimation")
        scale = float(np.sum(X * Y) / variance)
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError("invalid positive scale estimate")
    translation = metric_mean - scale * mono_mean

    residuals = []
    for T_base, T_camera in items:
        predicted_position = (scale * (R_align @ T_camera[:3, 3]) + translation +
                              R_align @ T_camera[:3, :3] @ T_camera_base[:3, 3])
        residuals.append(float(np.linalg.norm(predicted_position - T_base[:3, 3])))
        predicted_rotation = R_align @ T_camera[:3, :3] @ T_camera_base[:3, :3]
        orientation_errors.append(rotation_angle(T_base[:3, :3].T @ predicted_rotation))

    alignment = np.eye(4)
    alignment[:3, :3] = R_align
    alignment[:3, 3] = translation
    position_rmse = float(math.sqrt(np.mean(np.square(residuals))))
    orientation_rmse = float(math.sqrt(np.mean(np.square(orientation_errors))))
    return alignment, scale, position_rmse, orientation_rmse


def apply_camera_to_base_similarity(alignment: np.ndarray, scale: float,
                                    camera_to_base: np.ndarray,
                                    T_mono_camera: np.ndarray) -> np.ndarray:
    """Apply a metric monocular-world alignment and known camera lever arm."""
    R_align = alignment[:3, :3]
    R_camera = T_mono_camera[:3, :3]
    out = np.eye(4)
    out[:3, :3] = R_align @ R_camera @ camera_to_base[:3, :3]
    out[:3, 3] = (float(scale) * (R_align @ T_mono_camera[:3, 3]) +
                  alignment[:3, 3] +
                  R_align @ R_camera @ camera_to_base[:3, 3])
    return out
