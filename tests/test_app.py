from pathlib import Path
import sys

import hand_tracking.app as app_module
from hand_tracking.app import TrackingApp, default_model_path
from hand_tracking.config import TrackingConfig


class FakeController:
    def __init__(self):
        self.commands: list[list[int]] = []

    def set_angles(self, values: list[int]) -> None:
        self.commands.append(values)


TEST_CONFIG = TrackingConfig(serial_port="COM3")


def test_lost_hand_does_not_emit_command():
    app = TrackingApp(config=TEST_CONFIG, controller=FakeController())

    app.process_landmarks(None, now=0.0)

    assert app.controller.commands == []


def test_space_sends_open_pose():
    app = TrackingApp(config=TEST_CONFIG, controller=FakeController())

    app.handle_key(ord(" "))

    assert app.controller.commands == [TEST_CONFIG.open_pose]


def test_default_model_path_uses_project_asset():
    assert default_model_path() == Path("assets/hand_landmarker.task")


def test_mirrored_left_hand_right_label_is_accepted_for_tracking():
    app = TrackingApp(config=TEST_CONFIG, controller=FakeController())

    accepted = app.accept_hand_label("Right")

    assert accepted is True


def test_serial_startup_does_not_send_open_pose(monkeypatch):
    controller = FakeController()
    controller.open = lambda: None
    controller.close = lambda: None
    monkeypatch.setattr(app_module, "RH56Serial", lambda *args: controller)
    monkeypatch.setattr(app_module, "run_camera", lambda *args: None)
    monkeypatch.setattr(sys, "argv", ["app.py", "--config", "config.example.yaml"])

    app_module.main()

    assert controller.commands == []
