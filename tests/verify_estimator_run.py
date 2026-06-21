#!/usr/bin/env python3
"""Validate one independently recorded estimator trajectory."""
import argparse
import csv
import math
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("algorithm", choices=("fast_livo2", "orbslam3", "lvisam"))
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    filenames = {
        "fast_livo2": "fast_livo2_trajectory.csv",
        "orbslam3": "orbslam3_trajectory.csv",
        "lvisam": "lvisam_trajectory.csv",
    }
    filename = filenames[args.algorithm]
    path = args.run_dir / filename
    if not path.is_file():
        raise SystemExit(f"FAIL: missing {path}")
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) < 20:
        raise SystemExit(f"FAIL: only {len(rows)} poses recorded")
    fields = ("timestamp_s", "x_m", "y_m", "z_m", "qx", "qy", "qz", "qw")
    values = [[float(row[field]) for field in fields] for row in rows]
    if not all(math.isfinite(value) for row in values for value in row):
        raise SystemExit("FAIL: trajectory contains non-finite values")
    stamps = [row[0] for row in values]
    if any(right <= left for left, right in zip(stamps, stamps[1:])):
        raise SystemExit("FAIL: timestamps are not strictly increasing")
    duration = stamps[-1] - stamps[0]
    if duration <= 2.0:
        raise SystemExit(f"FAIL: trajectory duration is only {duration:.2f}s")
    rate = (len(rows) - 1) / duration
    if rate < 2.0:
        raise SystemExit(f"FAIL: pose rate is only {rate:.2f}Hz")
    positions = [row[1:4] for row in values]
    displacement = math.dist(positions[0], positions[-1])
    span = max(math.dist(positions[0], position) for position in positions)
    if span < 0.05:
        raise SystemExit(f"FAIL: maximum motion is only {span:.3f}m")
    norms = [math.sqrt(sum(value * value for value in row[4:8])) for row in values]
    if min(norms) < 0.99 or max(norms) > 1.01:
        raise SystemExit(f"FAIL: quaternion norm range is {min(norms):.4f}-{max(norms):.4f}")
    print(f"PASS: {args.algorithm}")
    print(f"poses={len(rows)} duration={duration:.2f}s rate={rate:.2f}Hz")
    print(f"net_displacement={displacement:.3f}m maximum_span={span:.3f}m")
    print(f"quaternion_norm={min(norms):.6f}-{max(norms):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
