from hand_tracking.safety import SafeCommandFilter


def test_filter_scales_first_command_to_startup_range():
    filter_ = SafeCommandFilter([0] * 6, [1000] * 6, deadband=8, send_hz=10, motion_scale=0.2)

    assert filter_.next([500] * 6, now=0.0) == [100] * 6


def test_filter_skips_small_change_and_rate_limits():
    filter_ = SafeCommandFilter([0] * 6, [1000] * 6, deadband=8, send_hz=10, motion_scale=1.0)
    assert filter_.next([500] * 6, now=0.0) == [500] * 6
    assert filter_.next([700] * 6, now=0.01) is None
    assert filter_.next([505] * 6, now=0.2) is None
