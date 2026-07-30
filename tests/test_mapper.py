import math

from hand_tracking.mapper import _curl, map_left_hand


OPEN_RIGHT_HAND = [(0.5, 0.9, 0.0)] * 21
BENT_RIGHT_HAND = [(0.5, 0.9, 0.0)] * 21


def test_mapper_returns_six_clamped_angles():
    targets = map_left_hand(OPEN_RIGHT_HAND, [False] * 6)

    assert len(targets) == 6
    assert all(0 <= value <= 1000 for value in targets)


def test_inverted_axis_reverses_one_target():
    normal = map_left_hand(BENT_RIGHT_HAND, [False] * 6)
    inverted = map_left_hand(BENT_RIGHT_HAND, [True, False, False, False, False, False])

    assert inverted[0] == 1000 - normal[0]


def test_thumb_curl_maps_straight_and_flexed_thumb_joint_angles():
    def hand_with_thumb_joint_angle(angle_degrees: float):
        landmarks = [(0.0, 0.0, 0.0)] * 21
        radians = math.radians(angle_degrees)
        landmarks[2] = (0.0, 0.0, 0.0)
        landmarks[3] = (1.0, 0.0, 0.0)
        landmarks[4] = (1.0 - math.cos(radians), math.sin(radians), 0.0)
        landmarks[5] = (2.0, 0.0, 0.0)
        landmarks[17] = (-2.0, 0.0, 0.0)
        return landmarks

    straight = map_left_hand(hand_with_thumb_joint_angle(180.0), [False] * 6)
    flexed = map_left_hand(hand_with_thumb_joint_angle(70.0), [False] * 6)

    assert straight[4] == 1000
    assert flexed[4] == 0


def test_thumb_rotation_stays_at_calibrated_hold_when_thumb_tip_moves_horizontally():
    def hand_with_thumb_tip(thumb_tip_x: float):
        landmarks = [(0.0, 0.0, 0.0)] * 21
        landmarks[0] = (0.0, 0.0, 0.0)
        landmarks[2] = (0.4, 0.0, 0.0)
        landmarks[4] = (thumb_tip_x, 0.2, 0.0)
        landmarks[5] = (1.0, 0.0, 0.0)
        landmarks[17] = (-1.0, 0.0, 0.0)
        return landmarks

    inward = map_left_hand(hand_with_thumb_tip(0.1), [False] * 6)
    outward = map_left_hand(hand_with_thumb_tip(0.9), [False] * 6)

    assert inward[5] == 1000
    assert outward[5] == 1000


def test_thumb_elevation_ignores_wrist_landmark_jitter():
    def hand_with_wrist_y(wrist_y: float):
        landmarks = [(0.0, 0.0, 0.0)] * 21
        landmarks[0] = (0.0, wrist_y, 0.0)
        landmarks[2] = (0.4, 0.0, 0.0)
        landmarks[4] = (0.4, -0.6, 0.0)
        landmarks[5] = (1.0, 0.0, 0.0)
        landmarks[17] = (-1.0, 0.0, 0.0)
        return landmarks

    steady = map_left_hand(hand_with_wrist_y(0.0), [False] * 6)
    jittered = map_left_hand(hand_with_wrist_y(0.3), [False] * 6)

    assert steady[4] == jittered[4]


def test_four_finger_curl_reaches_full_range_for_a_tight_fist_angle():
    mcp = (0.0, 0.0, 0.0)
    pip = (1.0, 0.0, 0.0)
    angle = math.radians(100.0)
    dip = (1.0 - math.cos(angle), math.sin(angle), 0.0)
    first_segment_direction = math.atan2(pip[1] - dip[1], pip[0] - dip[0])
    tip = (
        dip[0] + math.cos(first_segment_direction + angle),
        dip[1] + math.sin(first_segment_direction + angle),
        0.0,
    )

    assert _curl([mcp, pip, dip, tip], 0, 1, 2, 3) == 1000
