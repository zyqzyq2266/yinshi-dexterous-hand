import struct

import pytest

from hand_tracking.rh56 import RH56Serial, build_write_packet


class FakeSerial:
    def __init__(self):
        self.writes: list[bytes] = []
        self.closed = False

    def write(self, packet: bytes) -> int:
        self.writes.append(packet)
        return len(packet)

    def close(self) -> None:
        self.closed = True


def test_angle_packet_uses_documented_header_address_and_checksum():
    packet = build_write_packet(hand_id=1, address=1486, data=struct.pack("<6h", *([100] * 6)))

    assert packet[:2] == b"\xeb\x90"
    assert packet[5:7] == bytes([0xCE, 0x05])
    assert packet[-1] == sum(packet[2:-1]) & 0xFF


def test_set_angles_rejects_wrong_axis_count():
    controller = RH56Serial("COM3", 115200, 1, serial_instance=FakeSerial())

    with pytest.raises(ValueError, match="six"):
        controller.set_angles([100])


def test_set_angles_writes_all_six_targets():
    serial = FakeSerial()
    controller = RH56Serial("COM3", 115200, 1, serial_instance=serial)

    controller.set_angles([100, 200, 300, 400, 500, 600])

    assert serial.writes[0][7:-1] == struct.pack("<6h", 100, 200, 300, 400, 500, 600)
