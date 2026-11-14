"""Pruebas del gestor de alertas con deduplicación y cooldown."""

from datetime import datetime, timezone

import pytest

from config.settings import load_settings
from vision.src.alert_manager import AlertManager
from vision.src.models import (
    AlertLevel,
    AlertType,
    Assessment,
    FatigueState,
)


FIXED_TIME = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class FakeClock:
    """Reloj monotónico controlable para las pruebas."""

    def __init__(self, start: float = 100.0) -> None:
        self.current = start

    def __call__(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


def make_manager():
    """Crea el gestor con la configuración real y relojes falsos."""

    settings = load_settings().alerts
    clock = FakeClock()

    return (
        AlertManager(
            settings,
            clock=clock,
            wall_clock=lambda: FIXED_TIME,
        ),
        clock,
    )


def assessment(
    state,
    *,
    reasons=("Motivo de prueba.",),
    changed=True,
    paused=False,
):
    """Construye una evaluación para el gestor."""

    return Assessment(
        state=state,
        reasons=tuple(reasons),
        changed=changed,
        paused=paused,
    )


def test_level_for_state():
    assert AlertManager.level_for(FatigueState.NORMAL) == AlertLevel.NONE
    assert AlertManager.level_for(FatigueState.WARNING) == AlertLevel.WARNING
    assert AlertManager.level_for(FatigueState.FATIGUE) == AlertLevel.CRITICAL


def test_level_for_unknown_state_raises():
    with pytest.raises(ValueError, match="desconocido"):
        AlertManager.level_for("DROWSY")


def test_normal_state_does_not_emit_alerts():
    manager, _ = make_manager()

    assert manager.update(assessment(FatigueState.NORMAL)) == ()


def test_warning_emits_alert_with_reason_and_timestamp():
    manager, _ = make_manager()

    events = manager.update(
        assessment(
            FatigueState.WARNING,
            reasons=("PERCLOS 0.25 >= 0.20 durante 10.0 s.",),
        )
    )

    assert len(events) == 1
    event = events[0]

    assert event.type == AlertType.FATIGUE_WARNING
    assert event.level == AlertLevel.WARNING
    assert event.occurred_at == FIXED_TIME
    assert event.id is None
    assert "Advertencia de fatiga" in event.message
    assert "PERCLOS 0.25" in event.message


def test_fatigue_emits_critical_alert():
    manager, _ = make_manager()

    events = manager.update(assessment(FatigueState.FATIGUE))

    assert len(events) == 1
    assert events[0].type == AlertType.FATIGUE_CRITICAL
    assert events[0].level == AlertLevel.CRITICAL
    assert "Fatiga crítica" in events[0].message


def test_same_state_is_not_alerted_twice():
    manager, clock = make_manager()

    manager.update(assessment(FatigueState.WARNING))
    clock.advance(120.0)

    assert manager.update(assessment(FatigueState.WARNING)) == ()


def test_manager_deduplicates_even_if_changed_is_true():
    manager, _ = make_manager()

    manager.update(assessment(FatigueState.WARNING))

    assert (
        manager.update(
            assessment(FatigueState.WARNING, changed=True)
        )
        == ()
    )


def test_changed_flag_is_not_required_to_alert_first_entry():
    manager, _ = make_manager()

    events = manager.update(
        assessment(FatigueState.WARNING, changed=False)
    )

    assert len(events) == 1


def test_warning_cooldown_suppresses_reentry():
    manager, clock = make_manager()

    manager.update(assessment(FatigueState.WARNING))

    clock.advance(5.0)
    manager.update(assessment(FatigueState.NORMAL))

    clock.advance(5.0)
    assert manager.update(assessment(FatigueState.WARNING)) == ()


def test_warning_reentry_is_allowed_after_cooldown():
    manager, clock = make_manager()

    manager.update(assessment(FatigueState.WARNING))

    clock.advance(5.0)
    manager.update(assessment(FatigueState.NORMAL))

    clock.advance(5.0)
    assert manager.update(assessment(FatigueState.WARNING)) == ()

    clock.advance(5.0)
    manager.update(assessment(FatigueState.NORMAL))

    clock.advance(15.0)
    events = manager.update(assessment(FatigueState.WARNING))

    assert len(events) == 1
    assert events[0].level == AlertLevel.WARNING


def test_critical_cooldown_is_independent_and_longer():
    manager, clock = make_manager()

    manager.update(assessment(FatigueState.WARNING))
    assert len(manager.update(assessment(FatigueState.FATIGUE))) == 1

    clock.advance(5.0)
    manager.update(assessment(FatigueState.NORMAL))

    clock.advance(5.0)
    assert manager.update(assessment(FatigueState.WARNING)) == ()

    clock.advance(5.0)
    manager.update(assessment(FatigueState.NORMAL))

    clock.advance(15.0)
    events = manager.update(assessment(FatigueState.WARNING))

    # El cooldown de advertencia ya expiró, pero el crítico no.
    assert len(events) == 1
    manager.update(assessment(FatigueState.NORMAL))

    clock.advance(24.0)
    assert manager.update(assessment(FatigueState.FATIGUE)) == ()

    clock.advance(1.0)
    manager.update(assessment(FatigueState.NORMAL))

    clock.advance(5.0)
    events = manager.update(assessment(FatigueState.FATIGUE))

    assert len(events) == 1
    assert events[0].level == AlertLevel.CRITICAL


def test_paused_assessment_emits_nothing_and_keeps_last_state():
    manager, clock = make_manager()

    manager.update(assessment(FatigueState.NORMAL))

    clock.advance(1.0)
    paused = assessment(
        FatigueState.FATIGUE,
        paused=True,
        reasons=("Sin rostro: evaluación en pausa.",),
    )

    assert manager.update(paused) == ()

    clock.advance(1.0)
    events = manager.update(assessment(FatigueState.FATIGUE))

    assert len(events) == 1
    assert events[0].level == AlertLevel.CRITICAL


def test_reset_allows_immediate_alert_and_forgets_cooldowns():
    manager, _ = make_manager()

    manager.update(assessment(FatigueState.WARNING))
    manager.reset()

    events = manager.update(assessment(FatigueState.WARNING))

    assert len(events) == 1


def test_empty_reasons_use_generic_message():
    manager, _ = make_manager()

    events = manager.update(
        assessment(FatigueState.FATIGUE, reasons=())
    )

    assert len(events) == 1
    assert "Estado de fatiga detectado" in events[0].message
