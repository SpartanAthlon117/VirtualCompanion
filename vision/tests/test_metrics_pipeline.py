"""Pruebas del pipeline puro de métricas."""

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from config.settings import load_settings
from vision.src.metrics_pipeline import MetricsPipeline
from vision.src.models import VisionEventType


FIXED_TIME = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def clock(monkeypatch):
    """Proporciona un reloj monotónico controlable."""

    current_time = [100.0]

    def now():
        return current_time[0]

    def advance(seconds):
        current_time[0] += seconds

    monkeypatch.setattr(
        "vision.src.blink_detector.time.monotonic",
        now,
    )

    return advance


def make_settings(**overrides):
    """Construye una configuración con valores cómodos para pruebas."""

    settings = load_settings()
    settings = replace(
        settings,
        calibration=replace(
            settings.calibration,
            duration_seconds=5.0,
            stabilization_seconds=1.0,
            minimum_ear=0.15,
        ),
        perclos=replace(
            settings.perclos,
            window_seconds=10.0,
            minimum_observation_seconds=0.0,
        ),
        prolonged_closure=replace(
            settings.prolonged_closure,
            threshold_seconds=1.5,
        ),
    )

    for name, value in overrides.items():
        settings = replace(settings, **{name: value})

    return settings


def make_pipeline(settings=None):
    """Crea un pipeline con reloj de pared fijo."""

    return MetricsPipeline(
        settings or make_settings(),
        wall_clock=lambda: FIXED_TIME,
    )


def update(
    pipeline,
    *,
    face_present=True,
    ear=0.30,
    has_new_result=True,
):
    """Actualiza el pipeline con valores homogéneos para ambos ojos."""

    return pipeline.update(
        face_present=face_present,
        left_ear=ear,
        right_ear=ear,
        average_ear=ear,
        has_new_result=has_new_result,
    )


def complete_calibration(pipeline, advance):
    """Completa una calibración con EAR estable."""

    pipeline.start_calibration()
    advance(1.2)
    update(pipeline, ear=0.30)
    advance(4.0)
    return update(pipeline, ear=0.30)


def event_types(result):
    """Devuelve los tipos de evento de una actualización."""

    return [event.type for event in result.events]


def test_first_face_does_not_emit_recovered_event(clock):
    pipeline = make_pipeline()
    pipeline.start_calibration()

    result = update(pipeline)

    assert result.snapshot.face_present is True
    assert VisionEventType.FACE_RECOVERED not in event_types(result)
    assert result.calibration.completed is False


def test_calibration_requires_stabilization_time(clock):
    pipeline = make_pipeline()
    pipeline.start_calibration()

    clock(0.6)
    result = update(pipeline, ear=0.30)

    assert result.calibration.sample_count == 0
    assert result.calibration.progress < 0.2


def test_calibration_completes_and_sets_reference(clock):
    pipeline = make_pipeline()

    result = complete_calibration(pipeline, clock)

    assert result.calibration.completed is True
    assert result.calibration.reference_ear == pytest.approx(0.30)
    assert result.calibration.eye_threshold == pytest.approx(0.21)
    assert result.snapshot.eye_state == "OPEN"
    assert VisionEventType.CALIBRATION_COMPLETED in event_types(result)


def test_calibration_fails_without_valid_samples(clock):
    settings = make_settings(
        calibration=replace(
            load_settings().calibration,
            duration_seconds=5.0,
            stabilization_seconds=1.0,
            minimum_ear=0.90,
        )
    )
    pipeline = make_pipeline(settings)
    pipeline.start_calibration()

    clock(5.2)
    result = update(pipeline, ear=0.30)

    assert result.calibration.completed is True
    assert result.calibration.reference_ear is None
    assert result.calibration.eye_threshold is None
    assert result.snapshot.eye_state is None
    assert VisionEventType.CALIBRATION_FAILED in event_types(result)


def test_detects_completed_blink_after_calibration(clock):
    pipeline = make_pipeline()
    complete_calibration(pipeline, clock)

    clock(1.0)
    closed = update(pipeline, ear=0.10)

    assert closed.snapshot.eye_state == "CLOSED"
    assert closed.snapshot.blink_count == 0

    clock(0.3)
    opened = update(pipeline, ear=0.30)

    assert opened.snapshot.eye_state == "OPEN"
    assert opened.snapshot.blink_count == 1
    assert opened.snapshot.last_closed_duration == pytest.approx(0.3)
    assert VisionEventType.BLINK in event_types(opened)


def test_detects_prolonged_closure_once(clock):
    pipeline = make_pipeline()
    complete_calibration(pipeline, clock)

    clock(1.0)
    update(pipeline, ear=0.10)

    clock(1.6)
    result = update(pipeline, ear=0.10)

    assert result.snapshot.prolonged_closure_count == 1
    assert result.snapshot.prolonged_active is True
    assert result.snapshot.current_closed_duration == pytest.approx(1.6)
    assert VisionEventType.PROLONGED_CLOSURE in event_types(result)

    clock(0.5)
    repeated = update(pipeline, ear=0.10)

    assert repeated.snapshot.prolonged_closure_count == 1
    assert VisionEventType.PROLONGED_CLOSURE not in event_types(repeated)


def test_prolonged_closure_is_not_counted_as_blink(clock):
    pipeline = make_pipeline()
    complete_calibration(pipeline, clock)

    clock(1.0)
    update(pipeline, ear=0.10)

    clock(1.6)
    prolonged = update(pipeline, ear=0.10)

    assert VisionEventType.PROLONGED_CLOSURE in event_types(prolonged)

    clock(0.6)
    opened = update(pipeline, ear=0.30)

    assert opened.snapshot.blink_count == 0
    assert opened.snapshot.last_closed_duration == pytest.approx(2.2)
    assert VisionEventType.BLINK not in event_types(opened)


def test_calculates_perclos_without_minimum_observation(clock):
    pipeline = make_pipeline()
    complete_calibration(pipeline, clock)

    clock(1.0)
    update(pipeline, ear=0.10)

    clock(1.0)
    result = update(pipeline, ear=0.30)

    assert result.snapshot.perclos == pytest.approx(0.5)


def test_face_loss_pauses_and_recovery_preserves_reference(clock):
    pipeline = make_pipeline()
    completed = complete_calibration(pipeline, clock)
    reference = completed.calibration.reference_ear

    lost = update(
        pipeline,
        face_present=False,
        ear=None,
        has_new_result=False,
    )

    assert lost.snapshot.paused is True
    assert lost.snapshot.face_present is False
    assert lost.snapshot.eye_state is None
    assert lost.snapshot.average_ear is None
    assert lost.calibration.completed is True
    assert VisionEventType.FACE_LOST in event_types(lost)

    repeated = update(
        pipeline,
        face_present=False,
        ear=None,
        has_new_result=False,
    )

    assert VisionEventType.FACE_LOST not in event_types(repeated)

    clock(2.0)
    recovered = update(pipeline, ear=0.30)

    assert recovered.snapshot.paused is False
    assert recovered.snapshot.face_present is True
    assert recovered.snapshot.average_ear == pytest.approx(0.30)
    assert recovered.calibration.reference_ear == pytest.approx(reference)
    assert VisionEventType.FACE_RECOVERED in event_types(recovered)


def test_face_loss_interrupts_closure_without_counting_blink(clock):
    pipeline = make_pipeline()
    complete_calibration(pipeline, clock)

    clock(1.0)
    update(pipeline, ear=0.10)

    update(
        pipeline,
        face_present=False,
        ear=None,
        has_new_result=False,
    )
    clock(1.0)
    update(
        pipeline,
        face_present=False,
        ear=None,
        has_new_result=False,
    )

    recovered = update(pipeline, ear=0.30)

    assert recovered.snapshot.blink_count == 0
    assert recovered.snapshot.current_closed_duration is None


def test_new_result_is_required_for_calibration_updates(clock):
    pipeline = make_pipeline()
    calibrated = complete_calibration(pipeline, clock)
    samples = calibrated.calibration.sample_count

    clock(1.0)
    without_result = update(
        pipeline,
        ear=0.10,
        has_new_result=False,
    )

    assert without_result.calibration.sample_count == samples
    assert without_result.snapshot.eye_state == "OPEN"
    assert without_result.snapshot.average_ear == pytest.approx(0.10)
