from pathlib import Path

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_sensor_config(name):
    path = ROOT / "wrappers" / "localization_benchmark" / "config" / name
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def transform(values):
    matrix = np.asarray(values, dtype=float).reshape(4, 4)
    assert np.all(np.isfinite(matrix))
    assert np.allclose(matrix[3], [0.0, 0.0, 0.0, 1.0])
    assert np.allclose(matrix[:3, :3].T @ matrix[:3, :3], np.eye(3), atol=2e-6)
    assert np.isclose(np.linalg.det(matrix[:3, :3]), 1.0, atol=2e-6)
    return matrix


def static_transform(config, child):
    entry = next(item for item in config["static_transforms"] if item["child"] == child)
    matrix = np.eye(4)
    matrix[:3, :3] = np.asarray(entry["rotation"]).reshape(3, 3)
    matrix[:3, 3] = entry["translation"]
    return matrix


def test_public_orb_uses_metric_rgbd_without_reference_input():
    for name in (
        "boreas_2024_12_04_14_44.yaml",
        "urbanloco_ca_20190828184706.yaml",
    ):
        config = load_sensor_config(name)
        adapter = config["adapter"]
        rgbd = adapter["orb_rgbd"]
        assert adapter["orb_mode"] == "rgbd"
        assert rgbd["project_lidar_depth"] is True
        assert not adapter["topics"]["depth"]
        assert "ground_truth" not in str(rgbd).lower()


def test_lidar_depth_projection_matches_published_static_calibration():
    cases = (
        ("boreas_2024_12_04_14_44.yaml", "lidar", "camera"),
        ("urbanloco_ca_20190828184706.yaml", "rslidar", "camera0"),
    )
    for name, lidar_frame, camera_frame in cases:
        config = load_sensor_config(name)
        configured = transform(config["adapter"]["orb_rgbd"]["lidar_to_camera"])
        base_lidar = static_transform(config, lidar_frame)
        base_camera = static_transform(config, camera_frame)
        expected = np.linalg.inv(base_camera) @ base_lidar
        assert np.allclose(configured, expected, atol=2e-6)


def test_benchmark_defaults_orb_to_metric_rgbd():
    script = (ROOT / "run_benchmark.sh").read_text(encoding="utf-8")
    assert 'ORB_MODE="rgbd"' in script
    assert "ORB_EXECUTABLE=RGBD_Inertial" in script
    assert "ORB_EXECUTABLE=RGBD" in script
    assert 'ALIGNMENT=sim3' in script  # retained only for explicit mono ablations
