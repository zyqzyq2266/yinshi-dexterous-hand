from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _six_values(value: Any, name: str, default: list[Any]) -> list[Any]:
    result = default if value is None else list(value)
    if len(result) != 6:
        raise ValueError(f"{name} must contain six values")
    return result


@dataclass(frozen=True)
class TrackingConfig:
    serial_port: str
    baudrate: int = 115200
    hand_id: int = 1
    motion_scale: float = 0.2
    send_hz: float = 10.0
    deadband: int = 8
    min_angles: list[int] = field(default_factory=lambda: [0] * 6)
    max_angles: list[int] = field(default_factory=lambda: [1000] * 6)
    invert_axes: list[bool] = field(default_factory=lambda: [False] * 6)
    open_pose: list[int] = field(default_factory=lambda: [1000] * 6)

    @classmethod
    def load(cls, path: Path) -> "TrackingConfig":
        text = Path(path).read_text(encoding="utf-8")
        data = json.loads(text) if Path(path).suffix.lower() == ".json" else yaml.safe_load(text)
        data = data or {}
        if not data.get("serial_port"):
            raise ValueError("serial_port is required")
        config = cls(
            serial_port=str(data["serial_port"]),
            baudrate=int(data.get("baudrate", 115200)),
            hand_id=int(data.get("hand_id", 1)),
            motion_scale=float(data.get("motion_scale", 0.2)),
            send_hz=float(data.get("send_hz", 10.0)),
            deadband=int(data.get("deadband", 8)),
            min_angles=[int(x) for x in _six_values(data.get("min_angles"), "min_angles", [0] * 6)],
            max_angles=[int(x) for x in _six_values(data.get("max_angles"), "max_angles", [1000] * 6)],
            invert_axes=[bool(x) for x in _six_values(data.get("invert_axes"), "invert_axes", [False] * 6)],
            open_pose=[int(x) for x in _six_values(data.get("open_pose"), "open_pose", [1000] * 6)],
        )
        if not 0 < config.motion_scale <= 1:
            raise ValueError("motion_scale must be in (0, 1]")
        if config.send_hz <= 0:
            raise ValueError("send_hz must be positive")
        if any(low > high for low, high in zip(config.min_angles, config.max_angles)):
            raise ValueError("each min_angles value must be <= max_angles")
        return config
