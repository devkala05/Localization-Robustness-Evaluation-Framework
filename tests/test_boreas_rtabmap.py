from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_boreas_rtabmap_keeps_native_midpoint_point_times():
    benchmark = (ROOT / "run_benchmark.sh").read_text(encoding="utf-8")
    launch = (
        ROOT
        / "wrappers/localization_benchmark/launch/dataset_input_pipeline.launch"
    ).read_text(encoding="utf-8")
    adapter = (
        ROOT
        / "wrappers/localization_benchmark/scripts/e2o_sensor_adapter.py"
    ).read_text(encoding="utf-8")

    assert (
        '[[ "$DATASET" == boreas_rt ]] '
        "&& NORMALIZE_RAW_NEGATIVE_POINT_TIME=false"
    ) in benchmark
    assert 'name="normalize_raw_negative_point_time"' in launch
    assert "self.normalize_raw_negative_point_time" in adapter
    assert (
        "if self.normalize_raw_negative_point_time else copy.deepcopy(msg)"
        in adapter
    )


def test_boreas_rtabmap_solves_vertical_motion_without_flattening():
    config_path = (
        ROOT
        / "wrappers/rtabmap_benchmark/config/boreas_2024_12_04_14_44.yaml"
    )
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert config["Icp/Strategy"] == "1"
    assert config["Icp/PointToPlane"] == "true"
    assert config["Icp/Force4DoF"] == "true"
    assert "Reg/Force3DoF" not in config
    assert config["Odom/Strategy"] == "1"
    assert config["Odom/ScanKeyFrameThr"] == "0.0"
