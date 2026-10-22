import pytest

from vision.src.ear_calibrator import EARCalibrator


@pytest.fixture
def clock(monkeypatch):
    current_time = [100.0]

    monkeypatch.setattr(
        "vision.src.ear_calibrator.time.monotonic",
        lambda: current_time[0],
    )

    def advance(seconds):
        current_time[0] += seconds

    return advance


def test_collects_samples_after_stabilization(clock):
    calibrator = EARCalibrator(
        duration_seconds=5.0,
        stabilization_seconds=1.0,
        minimum_ear=0.15,
    )
    calibrator.start()

    clock(0.5)
    calibrator.update(0.30)

    assert calibrator.get_sample_count() == 0

    clock(0.6)
    calibrator.update(0.30)

    assert calibrator.get_sample_count() == 1
    assert calibrator.get_current_ear() == pytest.approx(0.30)
    assert calibrator.is_completed() is False


def test_ignores_ear_below_minimum(clock):
    calibrator = EARCalibrator(
        duration_seconds=5.0,
        stabilization_seconds=1.0,
        minimum_ear=0.15,
    )
    calibrator.start()

    clock(1.0)
    calibrator.update(0.10)

    assert calibrator.get_sample_count() == 0

    calibrator.update(0.30)

    assert calibrator.get_sample_count() == 1


def test_ignores_invalid_ear_values(clock):
    calibrator = EARCalibrator(
        duration_seconds=5.0,
        stabilization_seconds=1.0,
        minimum_ear=0.15,
    )
    calibrator.start()

    clock(1.0)
    calibrator.update(None)
    calibrator.update(float("nan"))
    calibrator.update(float("inf"))

    assert calibrator.get_sample_count() == 0
    assert calibrator.get_current_ear() is None


def test_pause_freezes_progress_and_ignores_updates(clock):
    calibrator = EARCalibrator(
        duration_seconds=5.0,
        stabilization_seconds=1.0,
        minimum_ear=0.15,
    )
    calibrator.start()

    clock(1.0)
    calibrator.update(0.30)

    clock(1.0)
    calibrator.update(0.30)

    assert calibrator.get_progress() == pytest.approx(0.4)

    calibrator.pause()

    assert calibrator.is_paused() is True
    assert calibrator.get_current_ear() is None

    clock(100.0)

    assert calibrator.get_progress() == pytest.approx(0.4)

    calibrator.update(0.40)

    assert calibrator.get_sample_count() == 2

    calibrator.resume()

    assert calibrator.is_paused() is False
    assert calibrator.get_progress() == pytest.approx(0.4)

    clock(3.0)
    calibrator.update(0.30)

    assert calibrator.is_completed() is True
    assert calibrator.get_reference_ear() == pytest.approx(0.30)


def test_resume_without_pause_does_not_change_progress(clock):
    calibrator = EARCalibrator(
        duration_seconds=5.0,
        stabilization_seconds=1.0,
        minimum_ear=0.15,
    )
    calibrator.start()

    clock(1.0)
    calibrator.resume()

    assert calibrator.get_progress() == pytest.approx(0.2)
