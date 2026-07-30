import json

import pytest

from hand_tracking.config import TrackingConfig


def test_loads_safe_defaults_from_json(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"serial_port": "COM3"}), encoding="utf-8")

    config = TrackingConfig.load(path)

    assert config.serial_port == "COM3"
    assert config.baudrate == 115200
    assert config.motion_scale == 0.2
    assert config.open_pose == [1000] * 6


def test_rejects_wrong_axis_length(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"serial_port": "COM3", "min_angles": [0, 0]}), encoding="utf-8")

    with pytest.raises(ValueError, match="six"):
        TrackingConfig.load(path)
