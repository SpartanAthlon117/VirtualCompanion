import pytest

from vision.src.eye_closure import ProlongedClosureDetector


@pytest.fixture
def clock():
    """Proporciona un reloj monotónico controlable."""

    current_time = [100.0]

    def now():
        return current_time[0]

    def advance(seconds):
        current_time[0] += seconds

    return now, advance


def make_detector(clock_now, threshold_seconds=1.0):
    return ProlongedClosureDetector(
        threshold_seconds=threshold_seconds,
        clock=clock_now,
    )


def test_initial_state(clock):
    clock_now, _ = clock
    detector = make_detector(clock_now)

    assert detector.get_prolonged_count() == 0
    assert detector.get_current_closed_duration() is None
    assert detector.get_last_prolonged_duration() is None
    assert detector.is_prolonged() is False
    assert detector.is_paused() is False
    assert detector.get_threshold_seconds() == 1.0


def test_rejects_invalid_threshold():
    with pytest.raises(ValueError):
        ProlongedClosureDetector(threshold_seconds=0.0)

    with pytest.raises(ValueError):
        ProlongedClosureDetector(threshold_seconds=-1.0)


def test_rejects_non_callable_clock():
    with pytest.raises(TypeError):
        ProlongedClosureDetector(clock=10.0)


def test_rejects_invalid_eye_state(clock):
    clock_now, _ = clock
    detector = make_detector(clock_now)

    with pytest.raises(ValueError):
        detector.update("INVALID")


def test_does_not_emit_before_threshold(clock):
    clock_now, advance = clock
    detector = make_detector(clock_now)

    detector.update(ProlongedClosureDetector.OPEN)
    detector.update(ProlongedClosureDetector.CLOSED)
    advance(0.9)

    assert detector.update(ProlongedClosureDetector.CLOSED) is False
    assert detector.get_prolonged_count() == 0
    assert detector.is_prolonged() is False
    assert detector.get_current_closed_duration() == pytest.approx(0.9)


def test_emits_at_threshold(clock):
    clock_now, advance = clock
    detector = make_detector(clock_now)

    detector.update(ProlongedClosureDetector.OPEN)
    detector.update(ProlongedClosureDetector.CLOSED)
    advance(1.0)

    assert detector.update(ProlongedClosureDetector.CLOSED) is True
    assert detector.get_prolonged_count() == 1
    assert detector.is_prolonged() is True
    assert detector.get_current_closed_duration() == pytest.approx(1.0)
    assert detector.get_last_prolonged_duration() == pytest.approx(1.0)


def test_emits_only_once_per_closure(clock):
    clock_now, advance = clock
    detector = make_detector(clock_now)

    detector.update(ProlongedClosureDetector.OPEN)
    detector.update(ProlongedClosureDetector.CLOSED)
    advance(1.0)
    assert detector.update(ProlongedClosureDetector.CLOSED) is True

    advance(1.0)

    assert detector.update(ProlongedClosureDetector.CLOSED) is False
    assert detector.get_prolonged_count() == 1
    assert detector.get_current_closed_duration() == pytest.approx(2.0)


def test_records_final_duration_on_reopen(clock):
    clock_now, advance = clock
    detector = make_detector(clock_now)

    detector.update(ProlongedClosureDetector.OPEN)
    detector.update(ProlongedClosureDetector.CLOSED)
    advance(1.0)
    detector.update(ProlongedClosureDetector.CLOSED)
    advance(0.5)

    assert detector.update(ProlongedClosureDetector.OPEN) is False
    assert detector.get_current_closed_duration() is None
    assert detector.is_prolonged() is False
    assert detector.get_last_prolonged_duration() == pytest.approx(1.5)
    assert detector.get_prolonged_count() == 1


def test_detects_threshold_crossed_between_updates(clock):
    clock_now, advance = clock
    detector = make_detector(clock_now)

    detector.update(ProlongedClosureDetector.OPEN)
    detector.update(ProlongedClosureDetector.CLOSED)
    advance(0.9)
    assert detector.update(ProlongedClosureDetector.CLOSED) is False

    advance(0.7)

    assert detector.update(ProlongedClosureDetector.OPEN) is True
    assert detector.get_prolonged_count() == 1
    assert detector.get_last_prolonged_duration() == pytest.approx(1.6)
    assert detector.is_prolonged() is False


def test_short_closure_is_not_prolonged(clock):
    clock_now, advance = clock
    detector = make_detector(clock_now)

    detector.update(ProlongedClosureDetector.OPEN)
    detector.update(ProlongedClosureDetector.CLOSED)
    advance(0.5)

    assert detector.update(ProlongedClosureDetector.OPEN) is False
    assert detector.get_prolonged_count() == 0
    assert detector.get_last_prolonged_duration() is None


def test_pause_discards_in_progress_closure(clock):
    clock_now, advance = clock
    detector = make_detector(clock_now)

    detector.update(ProlongedClosureDetector.OPEN)
    detector.update(ProlongedClosureDetector.CLOSED)
    advance(0.8)
    detector.pause()

    assert detector.is_paused() is True
    assert detector.get_current_closed_duration() is None
    assert detector.is_prolonged() is False
    assert detector.get_prolonged_count() == 0

    advance(1.0)
    detector.resume()

    assert detector.is_paused() is False
    assert detector.update(ProlongedClosureDetector.CLOSED) is False
    assert detector.get_prolonged_count() == 0

    advance(1.0)

    assert detector.update(ProlongedClosureDetector.CLOSED) is True
    assert detector.get_prolonged_count() == 1


def test_pause_after_event_keeps_count(clock):
    clock_now, advance = clock
    detector = make_detector(clock_now)

    detector.update(ProlongedClosureDetector.OPEN)
    detector.update(ProlongedClosureDetector.CLOSED)
    advance(1.0)
    detector.update(ProlongedClosureDetector.CLOSED)

    advance(0.5)
    detector.pause()

    assert detector.get_prolonged_count() == 1
    assert detector.get_current_closed_duration() is None
    assert detector.is_prolonged() is False
    assert detector.get_last_prolonged_duration() == pytest.approx(1.0)

    detector.resume()
    detector.update(ProlongedClosureDetector.OPEN)

    assert detector.get_prolonged_count() == 1


def test_paused_updates_are_ignored(clock):
    clock_now, _ = clock
    detector = make_detector(clock_now)

    detector.pause()

    assert detector.update(ProlongedClosureDetector.CLOSED) is False
    assert detector.get_prolonged_count() == 0
    assert detector.get_current_closed_duration() is None


def test_reset_clears_state(clock):
    clock_now, advance = clock
    detector = make_detector(clock_now)

    detector.update(ProlongedClosureDetector.OPEN)
    detector.update(ProlongedClosureDetector.CLOSED)
    advance(1.0)
    detector.update(ProlongedClosureDetector.CLOSED)

    detector.reset()

    assert detector.get_prolonged_count() == 0
    assert detector.get_current_closed_duration() is None
    assert detector.get_last_prolonged_duration() is None
    assert detector.is_prolonged() is False
    assert detector.is_paused() is False
