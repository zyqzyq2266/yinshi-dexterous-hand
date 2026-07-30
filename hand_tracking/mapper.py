from __future__ import annotations

import math
from collections.abc import Sequence


Point = Sequence[float]
THUMB_ROTATION_HOLD = 1000
FINGER_CURL_GAIN = 13.0
THUMB_FULL_FLEX_ANGLE = 70.0


def _angle(a: Point, b: Point, c: Point) -> float:
    first = tuple(a[index] - b[index] for index in range(3))
    second = tuple(c[index] - b[index] for index in range(3))
    first_length = math.sqrt(sum(value * value for value in first))
    second_length = math.sqrt(sum(value * value for value in second))
    if first_length == 0 or second_length == 0:
        return 180.0
    cosine = sum(first[index] * second[index] for index in range(3)) / (first_length * second_length)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def _curl(landmarks: Sequence[Point], mcp: int, pip: int, dip: int, tip: int) -> int:
    angle = (_angle(landmarks[mcp], landmarks[pip], landmarks[dip]) + _angle(landmarks[pip], landmarks[dip], landmarks[tip])) / 2
    return max(0, min(1000, round((180.0 - angle) * FINGER_CURL_GAIN)))


def _thumb_curl(landmarks: Sequence[Point]) -> int:
    thumb_angle = _angle(landmarks[2], landmarks[3], landmarks[4])
    return max(0, min(1000, round((thumb_angle - THUMB_FULL_FLEX_ANGLE) * 1000.0 / (180.0 - THUMB_FULL_FLEX_ANGLE))))


def map_left_hand(landmarks: Sequence[Point], invert_axes: Sequence[bool]) -> list[int]:
    """Map 21 MediaPipe left-hand landmarks to RH56's six-axis order."""
    if len(landmarks) != 21:
        raise ValueError("expected 21 hand landmarks")
    if len(invert_axes) != 6:
        raise ValueError("expected six inversion flags")
    angles = [
        _curl(landmarks, 17, 18, 19, 20),
        _curl(landmarks, 13, 14, 15, 16),
        _curl(landmarks, 9, 10, 11, 12),
        _curl(landmarks, 5, 6, 7, 8),
        _thumb_curl(landmarks),
        THUMB_ROTATION_HOLD,
    ]
    return [1000 - value if invert_axes[index] else value for index, value in enumerate(angles)]
