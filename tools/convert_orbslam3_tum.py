#!/usr/bin/env python3
"""Convert ORB-SLAM3's finalized native TUM trajectory to benchmark CSV.

Only the fixed calibrated camera-optical-to-body coordinate transform is
applied. No reference trajectory, scale, start pose, or fitted correction is
accepted by this tool.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from pathlib import Path

import numpy as np


def quaternion_to_matrix(values):
    x, y, z, w = np.asarray(values, dtype=float)
    norm = float(np.linalg.norm([x, y, z, w]))
    if not math.isfinite(norm) or norm <= 1.0e-12:
        raise ValueError("invalid quaternion")
    x, y, z, w = x / norm, y / norm, z / norm, w / norm
    return np.array([
        [1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w)],
        [2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w)],
        [2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y)],
    ])


def matrix_to_quaternion(matrix):
    matrix = np.asarray(matrix, dtype=float)
    trace = float(np.trace(matrix))
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        values = [(matrix[2, 1]-matrix[1, 2])/s,
                  (matrix[0, 2]-matrix[2, 0])/s,
                  (matrix[1, 0]-matrix[0, 1])/s, 0.25*s]
    else:
        index = int(np.argmax(np.diag(matrix)))
        if index == 0:
            s = math.sqrt(1+matrix[0, 0]-matrix[1, 1]-matrix[2, 2])*2
            values = [0.25*s, (matrix[0, 1]+matrix[1, 0])/s,
                      (matrix[0, 2]+matrix[2, 0])/s,
                      (matrix[2, 1]-matrix[1, 2])/s]
        elif index == 1:
            s = math.sqrt(1+matrix[1, 1]-matrix[0, 0]-matrix[2, 2])*2
            values = [(matrix[0, 1]+matrix[1, 0])/s, 0.25*s,
                      (matrix[1, 2]+matrix[2, 1])/s,
                      (matrix[0, 2]-matrix[2, 0])/s]
        else:
            s = math.sqrt(1+matrix[2, 2]-matrix[0, 0]-matrix[1, 1])*2
            values = [(matrix[0, 2]+matrix[2, 0])/s,
                      (matrix[1, 2]+matrix[2, 1])/s, 0.25*s,
                      (matrix[1, 0]-matrix[0, 1])/s]
    values = np.asarray(values)
    return values / np.linalg.norm(values)


def invert_transform(transform):
    output = np.eye(4)
    output[:3, :3] = transform[:3, :3].T
    output[:3, 3] = -(output[:3, :3] @ transform[:3, 3])
    return output


def convert(input_path, output_path, rotation, translation, timestamp_scale=1.0):
    body_from_camera = np.eye(4)
    body_from_camera[:3, :3] = np.asarray(rotation, dtype=float).reshape(3, 3)
    body_from_camera[:3, 3] = np.asarray(translation, dtype=float).reshape(3)
    camera_from_body = invert_transform(body_from_camera)

    rows = []
    previous_stamp = -math.inf
    for line_number, text in enumerate(input_path.read_text(encoding="utf-8").splitlines(), 1):
        text = text.strip()
        if not text or text.startswith("#"):
            continue
        values = [float(item) for item in text.split()]
        if len(values) != 8 or not all(map(math.isfinite, values)):
            raise ValueError(f"{input_path}:{line_number}: expected 8 finite TUM values")
        stamp, tx, ty, tz, qx, qy, qz, qw = values
        stamp *= timestamp_scale
        if stamp <= previous_stamp:
            raise ValueError(f"{input_path}:{line_number}: timestamps are not strictly increasing")
        previous_stamp = stamp
        world_from_camera = np.eye(4)
        world_from_camera[:3, :3] = quaternion_to_matrix([qx, qy, qz, qw])
        world_from_camera[:3, 3] = [tx, ty, tz]
        initial_body_from_body = (
            body_from_camera @ world_from_camera @ camera_from_body
        )
        q = matrix_to_quaternion(initial_body_from_body[:3, :3])
        rows.append([stamp, *initial_body_from_body[:3, 3], *q,
                     "orbslam3_map", "base_link"])
    if not rows:
        raise ValueError(f"{input_path}: no poses")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # The live recorder runs inside Docker as root, so its placeholder can be
    # read-only to the host user. Write beside it and atomically replace the
    # directory entry; this also prevents evaluation from observing a partial
    # final trajectory.
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
                "w", newline="", encoding="utf-8", dir=output_path.parent,
                prefix=f".{output_path.name}.", suffix=".tmp",
                delete=False) as stream:
            temporary_name = stream.name
            writer = csv.writer(stream)
            writer.writerow(["timestamp_s", "x_m", "y_m", "z_m",
                             "qx", "qy", "qz", "qw", "frame_id", "child_frame_id"])
            writer.writerows(rows)
        os.replace(temporary_name, output_path)
    except Exception:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
        raise
    return len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--rotation", required=True,
                        help="JSON 3x3 camera-optical-to-body rotation")
    parser.add_argument("--translation", required=True,
                        help="JSON camera origin in body coordinates")
    parser.add_argument(
        "--timestamp-scale",
        type=float,
        default=1.0,
        help="multiply native timestamps by this value (mono EuRoC export uses 1e-9)",
    )
    args = parser.parse_args()
    rotation = json.loads(args.rotation)
    translation = json.loads(args.translation)
    if not math.isfinite(args.timestamp_scale) or args.timestamp_scale <= 0.0:
        parser.error("--timestamp-scale must be finite and positive")
    print(convert(
        args.input,
        args.output,
        rotation,
        translation,
        timestamp_scale=args.timestamp_scale,
    ))


if __name__ == "__main__":
    main()
