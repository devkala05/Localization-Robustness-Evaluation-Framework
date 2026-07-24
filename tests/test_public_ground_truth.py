import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

MODULE_PATH = Path(__file__).parents[1] / "tools" / "convert_public_ground_truth.py"
SPEC = importlib.util.spec_from_file_location("convert_public_ground_truth", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
urban_novatel_timestamp = MODULE.urban_novatel_timestamp


def test_urban_novatel_timestamp_uses_receiver_measurement_time():
    header = SimpleNamespace(gps_week=2068, gps_week_seconds=352046850)
    assert urban_novatel_timestamp(header) == pytest.approx(1567043228.85)


@pytest.mark.parametrize(
    "week,milliseconds",
    [(0, 1), (2068, -1), (2068, 604800000)],
)
def test_urban_novatel_timestamp_rejects_invalid_values(week, milliseconds):
    header = SimpleNamespace(gps_week=week, gps_week_seconds=milliseconds)
    with pytest.raises(ValueError):
        urban_novatel_timestamp(header)
