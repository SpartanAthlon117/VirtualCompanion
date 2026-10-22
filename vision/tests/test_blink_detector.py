import pytest

from vision.src.blink_detector import BlinkDetector

@pytest.fixture
def clock(monkeypatch):
    '''Proporciona un reloj monotónico controlable para las pruebas.'''
    current_time = [100.0]

    monkeypatch.setattr(
        "vision.src.blink_detector.time.monotonic",
        lambda: current_time[0],
    )

    def advance(seconds):
        current_time[0] += seconds

    return advance

def test_initial_state():
    detector = BlinkDetector()

    assert detector.is_blink() is False
    assert detector.get_blink_count() == 0
    assert detector.get_last_closed_duration() is None
    assert detector.get_average_closed_duration() is None
    assert detector.get_blink_rate_per_minute() == 0.0
    assert detector.get_time_since_last_blink() is None
    assert detector.is_paused() is False

def test_detects_completed_blink(clock):
    detector = BlinkDetector()

    detector.update(BlinkDetector.OPEN)
    clock(0.1)
    detector.update(BlinkDetector.CLOSED)
    clock(0.2)
    detector.update(BlinkDetector.OPEN)

    assert detector.is_blink() is True
    assert detector.get_blink_count() == 1
    assert detector.get_last_closed_duration() == pytest.approx(0.2)


def test_does_not_count_blink_until_eyes_reopen(clock):
    detector = BlinkDetector()

    detector.update(BlinkDetector.OPEN)
    clock(0.1)
    detector.update(BlinkDetector.CLOSED)
    clock(1.5)

    assert detector.is_blink() is False
    assert detector.get_blink_count() == 0
    assert detector.get_last_closed_duration() is None


def test_measures_prolonged_eye_closure(clock):
    detector = BlinkDetector()

    detector.update(BlinkDetector.OPEN)
    detector.update(BlinkDetector.CLOSED)
    clock(1.5)
    detector.update(BlinkDetector.OPEN)

    assert detector.is_blink() is True
    assert detector.get_last_closed_duration() == pytest.approx(1.5)


def test_calculates_average_closed_duration(clock):
    detector = BlinkDetector()

    detector.update(BlinkDetector.OPEN)

    detector.update(BlinkDetector.CLOSED)
    clock(0.2)
    detector.update(BlinkDetector.OPEN)

    detector.update(BlinkDetector.CLOSED)
    clock(0.4)
    detector.update(BlinkDetector.OPEN)

    assert detector.get_blink_count() == 2
    assert detector.get_average_closed_duration() == pytest.approx(0.3)


def test_reset_clears_detector_state(clock):
    detector = BlinkDetector()

    detector.update(BlinkDetector.OPEN)
    detector.update(BlinkDetector.CLOSED)
    clock(0.2)
    detector.update(BlinkDetector.OPEN)

    detector.reset()

    assert detector.is_blink() is False
    assert detector.get_blink_count() == 0
    assert detector.get_last_closed_duration() is None
    assert detector.get_average_closed_duration() is None
    assert detector.get_blink_rate_per_minute() == 0.0
    assert detector.get_time_since_last_blink() is None


def test_rejects_invalid_eye_state():
    detector = BlinkDetector()

    with pytest.raises(ValueError):
        detector.update("UNKNOWN")


def test_pause_does_not_count_interrupted_blink(clock):
    detector = BlinkDetector()

    detector.update(BlinkDetector.OPEN)
    detector.update(BlinkDetector.CLOSED)
    clock(0.5)

    detector.pause()

    assert detector.is_paused() is True

    clock(5.0)
    detector.resume()
    detector.update(BlinkDetector.OPEN)

    assert detector.is_blink() is False
    assert detector.get_blink_count() == 0
    assert detector.get_last_closed_duration() is None


def test_pause_excludes_face_loss_time_from_blink_rate(clock):
    detector = BlinkDetector(analysis_window_seconds=60.0)

    detector.update(BlinkDetector.OPEN)
    clock(10.0)
    detector.update(BlinkDetector.CLOSED)
    detector.update(BlinkDetector.OPEN)

    assert detector.get_blink_rate_per_minute() == pytest.approx(6.0)

    detector.pause()
    clock(60.0)
    detector.resume()

    assert detector.get_blink_rate_per_minute() == pytest.approx(6.0)

    clock(10.0)

    assert detector.get_blink_rate_per_minute() == pytest.approx(3.0)


def test_update_is_ignored_while_paused(clock):
    detector = BlinkDetector()

    detector.update(BlinkDetector.OPEN)
    detector.pause()

    clock(1.0)
    detector.update(BlinkDetector.CLOSED)

    clock(1.0)
    detector.update(BlinkDetector.OPEN)

    assert detector.get_blink_count() == 0
    assert detector.is_blink() is False


def test_reset_clears_pause_state(clock):
    detector = BlinkDetector()

    detector.pause()

    assert detector.is_paused() is True

    detector.reset()

    assert detector.is_paused() is False

    detector.update(BlinkDetector.OPEN)
    clock(1.0)
    detector.update(BlinkDetector.CLOSED)
    detector.update(BlinkDetector.OPEN)

    assert detector.get_blink_count() == 1


@pytest.mark.parametrize("window", [0, -1, -60])
def test_rejects_invalid_analysis_window(window):
    with pytest.raises(ValueError):
        BlinkDetector(analysis_window_seconds=window)

def test_uses_elapsed_time_before_analysis_window_is_complete(clock):
    detector = BlinkDetector(analysis_window_seconds=60.0)

    detector.update(BlinkDetector.OPEN)
    clock(10.0)
    detector.update(BlinkDetector.CLOSED)
    detector.update(BlinkDetector.OPEN)

    assert detector.get_blink_rate_per_minute() == pytest.approx(6.0)


def test_uses_configured_window_after_it_is_complete(clock):
    detector = BlinkDetector(analysis_window_seconds=60.0)

    detector.update(BlinkDetector.OPEN)

    clock(30.0)
    detector.update(BlinkDetector.CLOSED)
    detector.update(BlinkDetector.OPEN)

    clock(30.0)
    detector.update(BlinkDetector.CLOSED)
    detector.update(BlinkDetector.OPEN)

    assert detector.get_blink_rate_per_minute() == pytest.approx(2.0)


def test_excludes_blinks_outside_rolling_window(clock):
    detector = BlinkDetector(analysis_window_seconds=10.0)

    detector.update(BlinkDetector.OPEN)
    detector.update(BlinkDetector.CLOSED)
    detector.update(BlinkDetector.OPEN)

    clock(8.0)
    detector.update(BlinkDetector.CLOSED)
    detector.update(BlinkDetector.OPEN)

    clock(3.0)

    assert detector.get_blink_rate_per_minute() == pytest.approx(6.0)