from __future__ import annotations

import struct
from typing import Any

import serial


ANGLE_SET_ADDRESS = 1486
REQUEST_HEADER = b"\xeb\x90"
WRITE_FLAG = 0x12


def build_write_packet(hand_id: int, address: int, data: bytes) -> bytes:
    body = bytes([hand_id, len(data) + 3, WRITE_FLAG, address & 0xFF, address >> 8]) + data
    return REQUEST_HEADER + body + bytes([sum(body) & 0xFF])


class RH56Serial:
    def __init__(self, port: str, baudrate: int, hand_id: int, serial_instance: Any | None = None) -> None:
        self.port = port
        self.baudrate = baudrate
        self.hand_id = hand_id
        self.serial = serial_instance

    def open(self) -> None:
        if self.serial is None:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=0.2)

    def set_angles(self, values: list[int]) -> None:
        if len(values) != 6:
            raise ValueError("expected six angles")
        if self.serial is None:
            raise RuntimeError("serial port is not open")
        data = struct.pack("<6h", *values)
        self.serial.write(build_write_packet(self.hand_id, ANGLE_SET_ADDRESS, data))

    def send_open_pose(self, values: list[int]) -> None:
        self.set_angles(values)

    def close(self) -> None:
        if self.serial is not None:
            self.serial.close()
            self.serial = None
