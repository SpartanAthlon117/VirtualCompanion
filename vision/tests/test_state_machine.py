"""Pruebas de la máquina de estados experimental de fatiga."""

import math

from config.settings import load_settings
from vision.src.models import FatigueState
from vision.src.state_machine import FatigueStateMachine


class FakeClock:
    """Reloj monotónico controlable para las pruebas."""

    def __init__(self, start: float = 100.0) -> None:
        self.current = start

    def __call__(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


def make_machine():
    """Crea la máquina con los umbrales por defecto y un reloj falso."""

    settings = load_settings().state_machine
    clock = FakeClock()

    return FatigueStateMachine(settings, clock=clock), clock


def observe(
    machine,
    clock,
    *,
    perclos=0.10,
    closure=None,
    face_present=True,
):
    """Ejecuta una actualización en el instante actual del reloj."""

    return machine.update(
        face_present=face_present,
        perclos=perclos,
        current_closed_duration=closure,
    )


def test_starts_in_normal_with_explanation():
    machine, clock = make_machine()

    assessment = observe(machine, clock, perclos=None)

    assert assessment.state == FatigueState.NORMAL
    assert assessment.changed is False
    assert assessment.paused is False
    assert any("Datos insuficientes" in reason for reason in assessment.reasons)


def test_perclos_warning_requires_sustained_time():
    machine, clock = make_machine()

    assert observe(machine, clock, perclos=0.25).state == FatigueState.NORMAL

    clock.advance(9.9)
    assert observe(machine, clock, perclos=0.25).state == FatigueState.NORMAL

    clock.advance(0.1)
    assessment = observe(machine, clock, perclos=0.25)

    assert assessment.state == FatigueState.WARNING
    assert assessment.changed is True
    assert any("PERCLOS 0.25" in reason for reason in assessment.reasons)


def test_warning_timer_restarts_after_perclos_drops():
    machine, clock = make_machine()

    observe(machine, clock, perclos=0.25)
    clock.advance(5.0)
    observe(machine, clock, perclos=0.25)

    # Un valor por debajo del umbral reinicia el sostenimiento.
    observe(machine, clock, perclos=0.19)
    observe(machine, clock, perclos=0.25)

    clock.advance(9.9)
    assert observe(machine, clock, perclos=0.25).state == FatigueState.NORMAL

    clock.advance(0.1)
    assert observe(machine, clock, perclos=0.25).state == FatigueState.WARNING


def test_perclos_fatigue_requires_sustained_time():
    machine, clock = make_machine()

    observe(machine, clock, perclos=0.35)
    clock.advance(9.9)
    assert observe(machine, clock, perclos=0.35).state == FatigueState.NORMAL

    clock.advance(0.1)
    assessment = observe(machine, clock, perclos=0.35)

    assert assessment.state == FatigueState.FATIGUE
    assert assessment.changed is True
    assert any("PERCLOS 0.35" in reason for reason in assessment.reasons)


def test_warning_can_escalate_to_fatigue():
    machine, clock = make_machine()

    observe(machine, clock, perclos=0.25)
    clock.advance(10.0)
    assert observe(machine, clock, perclos=0.25).state == FatigueState.WARNING

    assert observe(machine, clock, perclos=0.35).state == FatigueState.WARNING

    clock.advance(9.9)
    assert observe(machine, clock, perclos=0.35).state == FatigueState.WARNING

    clock.advance(0.1)
    assert observe(machine, clock, perclos=0.35).state == FatigueState.FATIGUE


def test_changed_is_true_only_on_transition():
    machine, clock = make_machine()

    observe(machine, clock, perclos=0.25)
    clock.advance(10.0)

    first = observe(machine, clock, perclos=0.25)
    second = observe(machine, clock, perclos=0.25)

    assert first.state == FatigueState.WARNING
    assert first.changed is True
    assert second.state == FatigueState.WARNING
    assert second.changed is False


def test_fatigue_recovers_to_normal_after_sustained_low_perclos():
    machine, clock = make_machine()

    observe(machine, clock, perclos=0.35)
    clock.advance(10.0)
    assert observe(machine, clock, perclos=0.35).state == FatigueState.FATIGUE

    assert observe(machine, clock, perclos=0.10).state == FatigueState.FATIGUE

    clock.advance(19.9)
    assert observe(machine, clock, perclos=0.10).state == FatigueState.FATIGUE

    clock.advance(0.1)
    assessment = observe(machine, clock, perclos=0.10)

    assert assessment.state == FatigueState.NORMAL
    assert assessment.changed is True


def test_warning_closure_triggers_warning_immediately():
    machine, clock = make_machine()

    assessment = observe(machine, clock, perclos=None, closure=1.5)

    assert assessment.state == FatigueState.WARNING
    assert assessment.changed is True
    assert any("Cierre ocular" in reason for reason in assessment.reasons)


def test_fatigue_closure_triggers_fatigue_immediately():
    machine, clock = make_machine()

    assessment = observe(machine, clock, perclos=None, closure=3.0)

    assert assessment.state == FatigueState.FATIGUE
    assert assessment.changed is True
    assert any("Cierre ocular" in reason for reason in assessment.reasons)


def test_short_closure_does_not_change_state():
    machine, clock = make_machine()

    assessment = observe(machine, clock, perclos=None, closure=1.49)

    assert assessment.state == FatigueState.NORMAL
    assert assessment.changed is False


def test_fatigue_does_not_downgrade_without_recovery():
    machine, clock = make_machine()

    observe(machine, clock, perclos=None, closure=3.0)

    clock.advance(5.0)
    assessment = observe(machine, clock, perclos=0.25)

    assert assessment.state == FatigueState.FATIGUE
    assert assessment.changed is False


def test_perclos_recovery_returns_to_normal_after_sustained_time():
    machine, clock = make_machine()

    observe(machine, clock, perclos=None, closure=1.6)
    assessment = observe(machine, clock, perclos=0.10)

    assert assessment.state == FatigueState.WARNING
    assert any(
        "Recuperación en curso" in reason for reason in assessment.reasons
    )

    clock.advance(19.9)
    assert observe(machine, clock, perclos=0.10).state == FatigueState.WARNING

    clock.advance(0.1)
    assessment = observe(machine, clock, perclos=0.10)

    assert assessment.state == FatigueState.NORMAL
    assert assessment.changed is True


def test_recovery_requires_perclos_below_exit_threshold():
    machine, clock = make_machine()

    observe(machine, clock, perclos=None, closure=1.6)

    clock.advance(30.0)
    assessment = observe(machine, clock, perclos=0.12)

    # 0.12 no es menor que el umbral de recuperación: sigue en WARNING.
    assert assessment.state == FatigueState.WARNING


def test_warning_closure_restarts_recovery_wait():
    machine, clock = make_machine()

    observe(machine, clock, perclos=None, closure=1.6)
    observe(machine, clock, perclos=0.10)

    clock.advance(10.0)
    observe(machine, clock, perclos=0.10, closure=1.6)

    clock.advance(1.0)
    observe(machine, clock, perclos=0.10)

    clock.advance(19.9)
    assert observe(machine, clock, perclos=0.10).state == FatigueState.WARNING

    clock.advance(0.1)
    assert observe(machine, clock, perclos=0.10).state == FatigueState.NORMAL


def test_normal_blinks_do_not_restart_recovery_wait():
    machine, clock = make_machine()

    observe(machine, clock, perclos=None, closure=1.6)
    observe(machine, clock, perclos=0.10)

    clock.advance(10.0)
    observe(machine, clock, perclos=0.10, closure=0.4)

    clock.advance(10.0)
    assert observe(machine, clock, perclos=0.10).state == FatigueState.NORMAL


def test_face_loss_pauses_without_changing_state():
    machine, clock = make_machine()

    observe(machine, clock, perclos=None, closure=1.6)
    clock.advance(5.0)

    assessment = observe(machine, clock, face_present=False)

    assert assessment.state == FatigueState.WARNING
    assert assessment.paused is True
    assert assessment.changed is False
    assert any("pausa" in reason for reason in assessment.reasons)


def test_timers_restart_after_face_is_recovered():
    machine, clock = make_machine()

    observe(machine, clock, perclos=None, closure=1.6)

    clock.advance(30.0)
    observe(machine, clock, face_present=False)

    clock.advance(30.0)
    assert observe(machine, clock, perclos=0.35).state == FatigueState.WARNING

    clock.advance(9.9)
    assert observe(machine, clock, perclos=0.35).state == FatigueState.WARNING

    clock.advance(0.1)
    assessment = observe(machine, clock, perclos=0.35)

    assert assessment.state == FatigueState.FATIGUE
    assert assessment.changed is True


def test_missing_or_non_finite_perclos_is_ignored():
    machine, clock = make_machine()

    for value in (None, math.nan, math.inf):
        assessment = observe(machine, clock, perclos=value)

        assert assessment.state == FatigueState.NORMAL
        assert any(
            "Datos insuficientes" in reason
            for reason in assessment.reasons
        )


def test_reset_returns_to_normal_and_clears_timers():
    machine, clock = make_machine()

    observe(machine, clock, perclos=None, closure=3.0)
    assert machine.state == FatigueState.FATIGUE

    machine.reset()

    assert machine.state == FatigueState.NORMAL

    clock.advance(0.1)
    observe(machine, clock, perclos=0.35)

    clock.advance(9.9)
    assert observe(machine, clock, perclos=0.35).state == FatigueState.NORMAL

    clock.advance(0.1)
    assert observe(machine, clock, perclos=0.35).state == FatigueState.FATIGUE


def test_warning_explains_current_perclos_and_recovery_target():
    machine, clock = make_machine()

    observe(machine, clock, perclos=None, closure=1.6)
    assessment = observe(machine, clock, perclos=0.14)

    assert assessment.state == FatigueState.WARNING
    assert any(
        "Recuperación: PERCLOS < 0.12 durante 20.0 s "
        "(actual: 0.14)." in reason
        for reason in assessment.reasons
    )


def test_recovery_progress_is_reported():
    machine, clock = make_machine()

    observe(machine, clock, perclos=None, closure=1.6)
    observe(machine, clock, perclos=0.10)

    clock.advance(12.5)
    assessment = observe(machine, clock, perclos=0.10)

    assert assessment.state == FatigueState.WARNING
    assert any(
        "durante 12.5 s de 20.0 s" in reason
        for reason in assessment.reasons
    )


def test_active_warning_closure_explains_recovery_wait():
    machine, clock = make_machine()

    observe(machine, clock, perclos=None, closure=1.6)
    assessment = observe(machine, clock, perclos=0.10, closure=1.6)

    assert assessment.state == FatigueState.WARNING
    assert any(
        "Recuperación en espera: cierre ocular en curso" in reason
        for reason in assessment.reasons
    )


def test_elevated_state_without_perclos_reports_missing_data():
    machine, clock = make_machine()

    observe(machine, clock, perclos=None, closure=1.6)
    assessment = observe(machine, clock, perclos=None)

    assert assessment.state == FatigueState.WARNING
    assert any(
        "Recuperación: PERCLOS < 0.12 durante 20.0 s "
        "(actual: sin datos)." in reason
        for reason in assessment.reasons
    )


def test_fatigue_explains_recovery_even_with_high_perclos():
    machine, clock = make_machine()

    observe(machine, clock, perclos=0.35)
    clock.advance(10.0)
    assessment = observe(machine, clock, perclos=0.35)

    assert assessment.state == FatigueState.FATIGUE
    assert any("PERCLOS 0.35" in reason for reason in assessment.reasons)
    assert any(
        "Recuperación: PERCLOS < 0.12 durante 20.0 s "
        "(actual: 0.35)." in reason
        for reason in assessment.reasons
    )
