import csv
import subprocess
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "convert_orbslam3_tum.py"


def test_native_orb_trajectory_conversion_is_fixed_transform_only(tmp_path):
    source = tmp_path / "native.tum"
    source.write_text(
        "1.0 0 0 0 0 0 0 1\n"
        "2.0 0 0 2 0 0 0 1\n",
        encoding="utf-8",
    )
    output = tmp_path / "orbslam3_trajectory.csv"
    rotation = [[0, 0, 1], [-1, 0, 0], [0, -1, 0]]
    subprocess.run([
        sys.executable, str(TOOL), str(source), str(output),
        "--rotation", json_text(rotation),
        "--translation", "[0,0,0]",
    ], check=True, capture_output=True, text=True)
    rows = list(csv.DictReader(output.open(encoding="utf-8")))
    assert len(rows) == 2
    assert np.allclose(
        [float(rows[1][key]) for key in ("x_m", "y_m", "z_m")],
        [2.0, 0.0, 0.0],
    )
    assert rows[1]["child_frame_id"] == "base_link"


def test_native_orb_converter_rejects_duplicate_timestamps(tmp_path):
    source = tmp_path / "native.tum"
    source.write_text(
        "1.0 0 0 0 0 0 0 1\n"
        "1.0 1 0 0 0 0 0 1\n",
        encoding="utf-8",
    )
    result = subprocess.run([
        sys.executable, str(TOOL), str(source), str(tmp_path / "out.csv"),
        "--rotation", json_text(np.eye(3).tolist()),
        "--translation", "[0,0,0]",
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert "strictly increasing" in result.stderr


def test_native_orb_converter_scales_euroc_nanosecond_timestamps(tmp_path):
    source = tmp_path / "native_euroc.txt"
    source.write_text(
        "1733341473000000000 0 0 0 0 0 0 1\n"
        "1733341473100000000 0 0 1 0 0 0 1\n",
        encoding="utf-8",
    )
    output = tmp_path / "orbslam3_trajectory.csv"
    subprocess.run([
        sys.executable, str(TOOL), str(source), str(output),
        "--rotation", json_text(np.eye(3).tolist()),
        "--translation", "[0,0,0]",
        "--timestamp-scale", "1e-9",
    ], check=True, capture_output=True, text=True)
    rows = list(csv.DictReader(output.open(encoding="utf-8")))
    assert np.isclose(float(rows[0]["timestamp_s"]), 1733341473.0)
    assert np.isclose(float(rows[1]["timestamp_s"]), 1733341473.1)


def test_rgbd_benchmark_requires_native_finalized_all_frame_export():
    benchmark = (ROOT / "run_benchmark.sh").read_text(encoding="utf-8")
    native_patch = (
        ROOT / "docker/orbslam3/patches/add_orbslam3_pose_publishers.py"
    ).read_text(encoding="utf-8")
    assert "SLAM.SaveTrajectoryTUM(trajectory_file)" in native_patch
    assert "orbslam3_native_camera_trajectory.tum" in benchmark
    assert '"$ORB_MODE" == mono-inertial' in benchmark
    assert "convert_orbslam3_tum.py" in benchmark
    assert 'REASON="native trajectory finalization failed"' in benchmark


def test_mono_benchmark_uses_native_finalized_all_frame_export():
    benchmark = (ROOT / "run_benchmark.sh").read_text(encoding="utf-8")
    native_patch = (
        ROOT / "docker/orbslam3/patches/add_mono_inertial_publishers.py"
    ).read_text(encoding="utf-8")
    assert "SLAM.SaveTrajectoryEuRoC(trajectory_file)" in native_patch
    assert '"$ORB_MODE" == mono || "$ORB_MODE" == mono-inertial' in benchmark


def json_text(value):
    import json
    return json.dumps(value, separators=(",", ":"))
