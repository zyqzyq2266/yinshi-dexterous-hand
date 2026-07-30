from __future__ import annotations

import argparse
import time
from collections.abc import Sequence
from pathlib import Path

from hand_tracking.config import TrackingConfig
from hand_tracking.mapper import map_left_hand
from hand_tracking.rh56 import RH56Serial
from hand_tracking.safety import SafeCommandFilter


def default_model_path() -> Path:
    return Path("assets/hand_landmarker.task")


class TrackingApp:
    def __init__(self, config: TrackingConfig, controller: RH56Serial) -> None:
        self.config = config
        self.controller = controller
        self.filter = SafeCommandFilter(
            config.min_angles,
            config.max_angles,
            config.deadband,
            config.send_hz,
            config.motion_scale,
        )
        self.status = "waiting for left hand"
        self.last_targets: list[int] | None = None

    def process_landmarks(self, landmarks: Sequence[Sequence[float]] | None, now: float) -> None:
        if landmarks is None:
            self.status = "left hand not detected - commands paused"
            return
        raw = map_left_hand(landmarks, self.config.invert_axes)
        target = self.filter.next(raw, now)
        if target is None:
            self.status = "tracking - command held by safety filter"
            return
        self.controller.set_angles(target)
        self.last_targets = target
        self.status = "tracking - command sent"

    def accept_hand_label(self, handedness: str) -> bool:
        # The mirrored selfie frame labels the user's physical left hand as Right.
        if handedness == "Right":
            return True
        self.status = f"{handedness.lower()} hand detected - commands paused"
        return False

    def handle_key(self, key: int) -> bool:
        if key == ord(" "):
            self.controller.set_angles(self.config.open_pose)
            self.last_targets = self.config.open_pose
            self.status = "open pose sent"
        if key == 27:
            self.status = "exit requested"
            return True
        return False


def _draw_overlay(frame, app: TrackingApp) -> None:
    import cv2

    cv2.putText(frame, f"Status: {app.status}", (16, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
    cv2.putText(frame, "Space: open pose | Esc: exit", (16, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    if app.last_targets is not None:
        labels = ("little", "ring", "middle", "index", "thumb bend", "thumb rotate")
        for index, (label, value) in enumerate(zip(labels, app.last_targets)):
            cv2.putText(frame, f"{label}: {value}", (16, 90 + index * 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 255), 1)


def run_camera(app: TrackingApp, camera_index: int, model_path: Path | None = None) -> None:
    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    model_path = model_path or default_model_path()
    if not model_path.is_file():
        raise FileNotFoundError(f"HandLandmarker model not found: {model_path}")
    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        raise RuntimeError(f"cannot open camera index {camera_index}")
    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.7,
        min_hand_presence_confidence=0.7,
        min_tracking_confidence=0.6,
    )
    landmarker = vision.HandLandmarker.create_from_options(options)
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError("camera frame capture failed")
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            result = landmarker.detect_for_video(image, int(time.monotonic() * 1000))
            landmarks = None
            rejected_hand = False
            if result.hand_landmarks and result.handedness:
                handedness = result.handedness[0][0].category_name
                hand_landmarks = result.hand_landmarks[0]
                height, width = frame.shape[:2]
                for point in hand_landmarks:
                    cv2.circle(frame, (int(point.x * width), int(point.y * height)), 3, (0, 255, 255), -1)
                if app.accept_hand_label(handedness):
                    landmarks = [(point.x, point.y, point.z) for point in hand_landmarks]
                else:
                    rejected_hand = True
            if not rejected_hand:
                app.process_landmarks(landmarks, time.monotonic())
            _draw_overlay(frame, app)
            cv2.imshow("RH56DFTP-2L Left-Hand Tracking", frame)
            if app.handle_key(cv2.waitKey(1) & 0xFF):
                return
    finally:
        landmarker.close()
        camera.release()
        cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser(description="Track a left hand and control an RH56DFTP-2L left hand.")
    parser.add_argument("--config", required=True, help="Path to JSON or YAML configuration")
    parser.add_argument("--camera", type=int, default=0, help="OpenCV camera index")
    parser.add_argument("--no-serial", action="store_true", help="Preview camera tracking without opening a COM port")
    args = parser.parse_args()
    config = TrackingConfig.load(args.config)

    class PreviewController:
        def set_angles(self, values: list[int]) -> None:
            return None

    controller = PreviewController() if args.no_serial else RH56Serial(config.serial_port, config.baudrate, config.hand_id)
    if not args.no_serial:
        controller.open()
    try:
        run_camera(TrackingApp(config, controller), args.camera)
    finally:
        if not args.no_serial:
            controller.close()


if __name__ == "__main__":
    main()
