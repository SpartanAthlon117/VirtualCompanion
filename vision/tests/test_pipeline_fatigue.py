"""Pruebas de integración de la evaluación de fatiga en el pipeline."""

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from config.settings import load_settings
from vision.src.metrics_pipeline import MetricsPipeline
from vision.src.models import (
    AlertLevel,
    AlertType,
    FatigueState,
)


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


def make_settings():
    """Construye una configuración rápida para las pruebas."""

    settings = load_settings()

    return replace(
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
    )


def make_pipeline(settings=None):
    """Crea un pipeline con fecha de pared fija."""

    return MetricsPipeline(
        settings or make_settings(),
        wall_clock=lambda: FIXED_TIME,
    )


def update(pipeline, *, ear=0.30, face_present=True, has_new_result=True):
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
    update(pipeline)
    advance(4.0)
    return update(pipeline)


def test_pipeline_starts_normal_without_alerts(clock):
    pipeline = make_pipeline()
    pipeline.start_calibration()

    result = update(pipeline)

    assert result.assessment.state == FatigueState.NORMAL
    assert result.assessment.alert_level == AlertLevel.NONE
    assert result.assessment.paused is False
    assert result.assessment.reasons
    assert result.alerts == ()


def test_closure_escalates_warning_then_fatigue(clock):
    pipeline = make_pipeline()
    complete_calibration(pipeline, clock)

    clock(1.0)
    update(pipeline, ear=0.10)

    clock(1.6)
    warning = update(pipeline, ear=0.10)

    assert warning.assessment.state == FatigueState.WARNING
    assert warning.assessment.changed is True
    assert warning.assessment.alert_level == AlertLevel.WARNING
    assert len(warning.alerts) == 1

    alert = warning.alerts[0]

    assert alert.type == AlertType.FATIGUE_WARNING
    assert alert.level == AlertLevel.WARNING
    assert alert.occurred_at == FIXED_TIME
    assert "Advertencia de fatiga" in alert.message

    clock(0.1)
    repeated = update(pipeline, ear=0.10)

    assert repeated.assessment.state == FatigueState.WARNING
    assert repeated.assessment.changed is False
    assert repeated.alerts == ()

    clock(1.5)
    fatigue = update(pipeline, ear=0.10)

    assert fatigue.assessment.state == FatigueState.FATIGUE
    assert fatigue.assessment.changed is True
    assert fatigue.assessment.alert_level == AlertLevel.CRITICAL
    assert len(fatigue.alerts) == 1
    assert fatigue.alerts[0].type == AlertType.FATIGUE_CRITICAL
    assert fatigue.alerts[0].level == AlertLevel.CRITICAL


def test_face_loss_pauses_assessment_without_new_alert(clock):
    pipeline = make_pipeline()
    complete_calibration(pipeline, clock)

    clock(1.0)
    update(pipeline, ear=0.10)
    clock(3.1)
    fatigue = update(pipeline, ear=0.10)

    assert fatigue.assessment.state == FatigueState.FATIGUE
    assert len(fatigue.alerts) == 1

    paused = update(
        pipeline,
        ear=None,
        face_present=False,
        has_new_result=False,
    )

    assert paused.snapshot.paused is True
    assert paused.assessment.state == FatigueState.FATIGUE
    assert paused.assessment.paused is True
    assert paused.assessment.alert_level == AlertLevel.CRITICAL
    assert paused.alerts == ()
    assert any("pausa" in reason for reason in paused.assessment.reasons)

    recovered = update(pipeline)

    assert recovered.snapshot.paused is False
    assert recovered.assessment.state == FatigueState.FATIGUE
    assert recovered.assessment.paused is False
    assert recovered.alerts == ()


def test_perclos_warning_is_integrated_without_closure_alerts(clock):
    pipeline = make_pipeline()
    complete_calibration(pipeline, clock)

    # Deja que la ventana de PERCLOS se llene con los ojos abiertos
    # para evitar el valor artificialmente alto del primer cierre.
    clock(10.0)
    update(pipeline)

    alerts = []

    for _ in range(25):
        clock(0.75)
        result = update(pipeline, ear=0.10)
        alerts.extend(result.alerts)

        clock(0.25)
        result = update(pipeline)
        alerts.extend(result.alerts)

    assert result.assessment.state == FatigueState.WARNING
    assert result.assessment.alert_level == AlertLevel.WARNING
    assert any("PERCLOS" in reason for reason in result.assessment.reasons)
    assert len(alerts) == 1
    assert alerts[0].level == AlertLevel.WARNING


def test_recalibration_resets_assessment_and_alerts(clock):
    pipeline = make_pipeline()
    complete_calibration(pipeline, clock)

    clock(1.0)
    update(pipeline, ear=0.10)
    clock(3.1)
    assert update(pipeline, ear=0.10).assessment.state == (
        FatigueState.FATIGUE
    )

    pipeline.start_calibration()

    clock(5.2)
    result = update(pipeline)

    assert result.assessment.state == FatigueState.NORMAL
    assert result.assessment.alert_level == AlertLevel.NONE
    assert result.assessment.changed is False
    assert result.alerts == ()
