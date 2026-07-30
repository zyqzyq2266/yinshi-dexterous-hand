from __future__ import annotations


class SafeCommandFilter:
    def __init__(self, minimum: list[int], maximum: list[int], deadband: int, send_hz: float, motion_scale: float) -> None:
        if not (len(minimum) == len(maximum) == 6):
            raise ValueError("expected six angle limits")
        self.minimum = minimum
        self.maximum = maximum
        self.deadband = deadband
        self.send_hz = send_hz
        self.motion_scale = motion_scale
        self.last_sent: list[int] | None = None
        self.last_time = float("-inf")

    def next(self, raw: list[int], now: float) -> list[int] | None:
        if len(raw) != 6:
            raise ValueError("expected six target angles")
        if now - self.last_time < 1 / self.send_hz:
            return None
        target = []
        for index, value in enumerate(raw):
            scaled = self.minimum[index] + (value - self.minimum[index]) * self.motion_scale
            target.append(max(self.minimum[index], min(self.maximum[index], round(scaled))))
        if self.last_sent is not None and max(abs(target[index] - self.last_sent[index]) for index in range(6)) < self.deadband:
            return None
        self.last_sent = target
        self.last_time = now
        return target
