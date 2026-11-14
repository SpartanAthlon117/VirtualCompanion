"""Pruebas del reporte de estado y alertas del CLI."""

import logging
from datetime import datetime, timezone

from vision.src.face_tracker import (
    _assessment_color,
    _report_alert,
    _report_assessment,
)
from vision.src.models import (
    AlertEvent,
    AlertLevel,
    AlertType,
    Assessment,
    FatigueState,
)


FIXED_TIME = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class FakeLogger:
    """Captura las llamadas de registro para comprobarlas."""

    def __init__(self):
        self.records = []

    def log(self, level, message, *args):
        self.records.append((level, message % args if args else message))


def make_assessment(state, *, paused=False):
    return Assessment(
        state=state,
        reasons=("Motivo de prueba.",),
        changed=True,
        paused=paused,
        alert_level=AlertLevel.WARNING,
    )


def test_reports_warning_state_to_log_and_console(capsys):
    logger = FakeLogger()

    _report_assessment(
        logger,
        make_assessment(FatigueState.WARNING),
    )

    assert logger.records == [
        (logging.WARNING, "Estado WARNING. Motivos: Motivo de prueba.")
    ]
    assert "ESTADO | ADVERTENCIA: Motivo de prueba." in capsys.readouterr().out


def test_reports_fatigue_state_as_critical(capsys):
    logger = FakeLogger()

    _report_assessment(
        logger,
        make_assessment(FatigueState.FATIGUE),
    )

    assert logger.records[0][0] == logging.CRITICAL
    assert "ESTADO | FATIGA" in capsys.readouterr().out


def test_reports_recovery_as_info(capsys):
    logger = FakeLogger()

    _report_assessment(
        logger,
        make_assessment(FatigueState.NORMAL),
    )

    assert logger.records[0][0] == logging.INFO
    assert "ESTADO | NORMAL" in capsys.readouterr().out


def test_reports_critical_alert(capsys):
    logger = FakeLogger()
    alert = AlertEvent(
        type=AlertType.FATIGUE_CRITICAL,
        level=AlertLevel.CRITICAL,
        message="Fatiga crítica: cierre ocular prolongado.",
        occurred_at=FIXED_TIME,
    )

    _report_alert(logger, alert)

    assert logger.records == [
        (
            logging.CRITICAL,
            "Alerta CRITICAL: Fatiga crítica: cierre ocular prolongado.",
        )
    ]
    assert (
        "ALERTA CRITICA | Fatiga crítica: cierre ocular prolongado."
        in capsys.readouterr().out
    )


def test_assessment_color_reflects_state_and_pause():
    assert _assessment_color(
        make_assessment(FatigueState.NORMAL)
    ) == (0, 255, 0)
    assert _assessment_color(
        make_assessment(FatigueState.WARNING)
    ) == (0, 255, 255)
    assert _assessment_color(
        make_assessment(FatigueState.FATIGUE)
    ) == (0, 0, 255)
    assert _assessment_color(
        make_assessment(FatigueState.FATIGUE, paused=True)
    ) == (0, 255, 255)
