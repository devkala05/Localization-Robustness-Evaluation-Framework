#!/usr/bin/env python3
"""Exec a pinned native ORB-SLAM3 ROS example.

roslaunch appends remapping arguments (for example ``__name:=...`` and
``/tf:=...``) to this wrapper's argv. They must be forwarded to the C++ binary;
otherwise the native node name/topic/TF remaps configured by the launch file are
silently lost. ORB-SLAM3 calls ``ros::init`` before checking argc, so ROS removes
those remapping arguments before its normal vocabulary/settings argument check.
"""
import os
import sys
from pathlib import Path
from typing import List, Sequence, Tuple


def split_arguments(argv: Sequence[str]) -> Tuple[List[str], List[str]]:
    """Return positional arguments and ROS remapping arguments.

    ROS1 remapping arguments use ``name:=value``. The two positional arguments
    are the vocabulary and camera settings paths.
    """
    positional = [argv[0]]
    remaps = []
    for argument in argv[1:]:
        if ":=" in argument:
            remaps.append(argument)
        else:
            positional.append(argument)
    return positional, remaps


def find_native_binary(root: Path, executable: str = "RGBD") -> Path:
    if not executable or "/" in executable:
        raise ValueError(f"invalid ORB-SLAM3 executable name: {executable!r}")
    package = root / "Examples_old" / "ROS" / "ORB_SLAM3"
    candidates = (
        package / executable,
        package / "bin" / executable,
        package / "build" / executable,
        package / "build" / "bin" / executable,
    )
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    searched = "\n  ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"native ORB-SLAM3 {executable} executable not found; searched:\n  {searched}")


def build_exec_argv(argv: Sequence[str], root: Path) -> Tuple[Path, List[str]]:
    positional, remaps = split_arguments(argv)
    if len(positional) != 3:
        raise ValueError("Usage: run_orbslam3_native.py VOCABULARY CAMERA_CONFIG")
    executable = os.environ.get("ORB_SLAM3_EXECUTABLE", "RGBD")
    binary = find_native_binary(root, executable)
    # Preserve remaps after the two application arguments. ros::init removes
    # them from argc before ORB-SLAM3's native ``argc != 3`` check.
    return binary, [str(binary), positional[1], positional[2], *remaps]


def main() -> int:
    root = Path(os.environ.get("ORB_SLAM3_ROOT", "/root/ORB_SLAM3"))
    try:
        binary, exec_argv = build_exec_argv(sys.argv, root)
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    os.execv(str(binary), exec_argv)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
