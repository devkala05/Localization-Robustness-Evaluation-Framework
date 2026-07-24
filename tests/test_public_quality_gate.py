import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))

from evaluate_public import assess_quality, crop_trajectory, travelled_distance  # noqa: E402


def result(ate_rmse, reference_distance=1000.0, associations=100, alignment="se3",
           ate_max=None):
    return {
        "alignment": alignment,
        "valid": True,
        "completion": {"status": "completed"},
        "associations": associations,
        "reference_distance_m": reference_distance,
        "reference_duration_sec": 100.0,
        "trajectory_duration_sec": 100.0,
        "ate_m": {"rmse": ate_rmse, "max": ate_rmse if ate_max is None else ate_max},
    }


def test_quality_gate_accepts_reasonable_normalized_ate():
    quality = assess_quality(result(10.0))
    assert quality["accepted"]
    assert quality["policy"]["effective_ate_limit_m"] == 20.0


def test_quality_gate_rejects_large_ate_and_too_few_matches():
    quality = assess_quality(result(25.0, associations=10, ate_max=25.0))
    assert not quality["accepted"]
    assert len(quality["reasons"]) == 3


def test_quality_gate_rejects_large_peak_despite_reasonable_rmse():
    quality = assess_quality(result(10.0, ate_max=15.01))
    assert not quality["accepted"]
    assert any("maximum ATE" in reason for reason in quality["reasons"])


def test_quality_gate_records_sim3_only_for_scale_unobservable_mode():
    quality = assess_quality(result(10.0, alignment="sim3"))
    assert quality["policy"]["metric"] == "SIM3 ATE RMSE"
    assert quality["policy"]["scale_fitting_allowed"] is True


def test_quality_gate_rejects_short_successful_fragment():
    candidate = result(0.1)
    candidate["trajectory_duration_sec"] = 8.5
    quality = assess_quality(candidate)
    assert not quality["accepted"]
    assert "duration coverage" in quality["reasons"][0]


def test_travelled_distance_uses_associated_path_segments():
    positions = np.asarray([[0.0, 0.0, 0.0], [3.0, 4.0, 0.0], [3.0, 4.0, 12.0]])
    assert travelled_distance(positions) == 17.0


def test_crop_trajectory_excludes_warmup_prefix():
    data = {
        "stamp": np.asarray([10.0, 11.0, 12.0, 13.0]),
        "position": np.arange(12, dtype=float).reshape(4, 3),
        "quaternion": np.ones((4, 4)),
    }
    cropped = crop_trajectory(data, start_time=11.0, duration=1.0)
    assert cropped["stamp"].tolist() == [11.0, 12.0]
    assert cropped["position"].shape == (2, 3)
