#!/usr/bin/env python3
import os
import sys


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: run_orbslam3_native.py Mono|Stereo ORB_ARGS...",
            file=sys.stderr,
        )
        return 2

    mode = sys.argv[1]
    orb_slam3_root = os.environ.get("ORB_SLAM3_ROOT", "/root/ORB_SLAM3")
    binary = os.path.join(
        orb_slam3_root,
        "Examples_old",
        "ROS",
        "ORB_SLAM3",
        mode,
    )

    if not os.path.isfile(binary) or not os.access(binary, os.X_OK):
        print(f"ERROR: Native ORB-SLAM3 executable not found: {binary}", file=sys.stderr)
        return 1

    os.execv(binary, [binary] + sys.argv[2:])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
