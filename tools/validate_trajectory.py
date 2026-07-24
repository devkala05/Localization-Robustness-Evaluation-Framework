#!/usr/bin/env python3
"""Strict validation for a recorder trajectory before it can be marked complete."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def validate(path: Path):
    count = 0
    last_stamp = None
    reasons = []
    try:
        stream = path.open(newline="", encoding="utf-8")
    except OSError as exc:
        return {"valid": False, "pose_count": 0, "reasons": [str(exc)]}
    with stream:
        for line, row in enumerate(csv.DictReader(stream), 2):
            try:
                values = [float(row[name]) for name in
                          ("timestamp_s", "x_m", "y_m", "z_m", "qx", "qy", "qz", "qw")]
            except (KeyError, TypeError, ValueError) as exc:
                reasons.append(f"line {line}: malformed pose ({exc})")
                continue
            if not all(math.isfinite(value) for value in values):
                reasons.append(f"line {line}: non-finite pose")
            stamp = values[0]
            if last_stamp is not None and stamp <= last_stamp:
                reasons.append(f"line {line}: timestamp is not strictly increasing")
            last_stamp = stamp
            norm = math.sqrt(sum(value*value for value in values[4:]))
            if not math.isfinite(norm) or norm < 1e-9:
                reasons.append(f"line {line}: invalid quaternion")
            count += 1
    if count == 0:
        reasons.append("trajectory contains no poses")
    return {"valid": not reasons, "pose_count": count, "reasons": reasons[:100]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trajectory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.trajectory)
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
