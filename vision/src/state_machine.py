"""Máquina de estados experimental para la evaluación de fatiga.

La estimación combina únicamente dos indicadores observables:

- PERCLOS sostenido por encima de un umbral.
- Duración del cierre ocular en curso.

La frecuencia y la ausencia de parpadeo no intervienen en las
transiciones; se conservan como información para una fase posterior.

Las reglas son deliberadamente simples y explicables, no un diagnóstico
clínico. Los umbrales provienen de ``StateMachineSettings`` y son
experimentales hasta que exista una validación con más observaciones.
"""

from __future__ import annotations

import math
import time
from typing import Callable

from config.settings import StateMachineSettings
from vision.src.models import Assessment, FatigueState


def _finite_or_none(value: float | None) -> float | None:
    """Normaliza un valor ausente o no finito a None."""

    if value is None:
        return None

    number = float(value)

    if not math.isfinite(number):
        return None

    return max(0.0, number)


class FatigueStateMachine:
    """
    Evalúa el estado de fatiga con histéresis y sostenimiento temporal.

    El reloj es inyectable para poder probar los tiempos sin esperas
    reales. ``update`` recibe la presencia del rostro, el PERCLOS y la
    duración del cierre ocular actual; devuelve una ``Assessment``
    inmutable con el estado, los motivos y si cambió en esa llamada.

    Sin rostro no se evalúa ni se cambia de estado: los temporizadores
    se reinician para que una pausa no cuente como observación
    sostenida. Al reanudarse, cada condición debe sostenerse de nuevo.
    """

    def __init__(
        self,
        settings: StateMachineSettings,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._settings = settings
        self._clock = clock or time.monotonic
        self.reset()

    @property
    def state(self) -> str:
        """Estado actual de la evaluación."""

        return self._state

    def reset(self) -> None:
        """Devuelve la evaluación a NORMAL y descarta los temporizadores."""

        self._state = FatigueState.NORMAL
        self._warning_since: float | None = None
        self._fatigue_since: float | None = None
        self._recovery_since: float | None = None

    def update(
        self,
        *,
        face_present: bool,
        perclos: float | None,
        current_closed_duration: float | None,
    ) -> Assessment:
        """
        Evalúa una observación y devuelve el estado resultante.

        ``perclos`` debe ser None cuando no hay datos suficientes y
        ``current_closed_duration`` debe ser None cuando los ojos no
        están cerrados.
        """

        now = self._clock()

        if not face_present:
            self._clear_timers()

            return Assessment(
                state=self._state,
                reasons=("Sin rostro: evaluación en pausa.",),
                changed=False,
                paused=True,
            )

        perclos = _finite_or_none(perclos)
        closure = _finite_or_none(current_closed_duration)

        self._update_perclos_timers(now, perclos)
        self._update_recovery_timer(now, perclos, closure)

        previous = self._state
        target = self._evaluate_target(now, closure)

        self._state = target

        if target == FatigueState.NORMAL and self._recovery_since is not None:
            self._recovery_since = None

        return Assessment(
            state=self._state,
            reasons=tuple(self._build_reasons(now, perclos, closure)),
            changed=target != previous,
            paused=False,
        )

    def _update_perclos_timers(
        self,
        now: float,
        perclos: float | None,
    ) -> None:
        """Actualiza los inicios de las condiciones que elevan el estado."""

        threshold = self._settings.warning_perclos

        if perclos is not None and perclos >= threshold:
            if self._warning_since is None:
                self._warning_since = now
        else:
            self._warning_since = None

        threshold = self._settings.fatigue_perclos

        if perclos is not None and perclos >= threshold:
            if self._fatigue_since is None:
                self._fatigue_since = now
        else:
            self._fatigue_since = None

    def _update_recovery_timer(
        self,
        now: float,
        perclos: float | None,
        closure: float | None,
    ) -> None:
        """Mantiene la recuperación solo mientras se cumpla su condición."""

        warning_closure_active = (
            closure is not None
            and closure >= self._settings.warning_closure_seconds
        )

        if (
            self._state != FatigueState.NORMAL
            and perclos is not None
            and perclos < self._settings.warning_exit_perclos
            and not warning_closure_active
        ):
            if self._recovery_since is None:
                self._recovery_since = now
        else:
            self._recovery_since = None

    def _evaluate_target(
        self,
        now: float,
        closure: float | None,
    ) -> str:
        """Decide el estado aplicando escalado inmediato y recuperación."""

        target = self._state

        if closure is not None:
            if closure >= self._settings.fatigue_closure_seconds:
                return FatigueState.FATIGUE

            if (
                closure >= self._settings.warning_closure_seconds
                and self._state != FatigueState.FATIGUE
            ):
                return FatigueState.WARNING

        if (
            self._fatigue_since is not None
            and now - self._fatigue_since
            >= self._settings.fatigue_sustain_seconds
        ):
            return FatigueState.FATIGUE

        if (
            self._warning_since is not None
            and now - self._warning_since
            >= self._settings.warning_sustain_seconds
            and self._state != FatigueState.FATIGUE
        ):
            target = FatigueState.WARNING

        if (
            self._state != FatigueState.NORMAL
            and self._recovery_since is not None
            and now - self._recovery_since
            >= self._settings.recovery_sustain_seconds
            and not (
                closure is not None
                and closure >= self._settings.warning_closure_seconds
            )
        ):
            return FatigueState.NORMAL

        return target

    def _build_reasons(
        self,
        now: float,
        perclos: float | None,
        closure: float | None,
    ) -> list[str]:
        """Construye explicaciones legibles del estado actual."""

        reasons: list[str] = []

        if closure is not None and closure > 0:
            if closure >= self._settings.fatigue_closure_seconds:
                reasons.append(
                    f"Cierre ocular de {closure:.1f} s "
                    f"(umbral de fatiga: "
                    f"{self._settings.fatigue_closure_seconds:.1f} s)."
                )
            elif closure >= self._settings.warning_closure_seconds:
                reasons.append(
                    f"Cierre ocular de {closure:.1f} s "
                    f"(umbral de advertencia: "
                    f"{self._settings.warning_closure_seconds:.1f} s)."
                )

        if perclos is None:
            if self._state == FatigueState.NORMAL:
                reasons.append(
                    "Datos insuficientes de PERCLOS; "
                    "solo se evalúan los cierres."
                )
        elif (
            self._state == FatigueState.FATIGUE
            and self._fatigue_since is not None
            and perclos >= self._settings.fatigue_perclos
        ):
            reasons.append(
                f"PERCLOS {perclos:.2f} >= "
                f"{self._settings.fatigue_perclos:.2f} durante "
                f"{now - self._fatigue_since:.1f} s "
                f"(sostenimiento: "
                f"{self._settings.fatigue_sustain_seconds:.1f} s)."
            )
        elif (
            self._state in (FatigueState.WARNING, FatigueState.FATIGUE)
            and self._warning_since is not None
            and perclos >= self._settings.warning_perclos
        ):
            reasons.append(
                f"PERCLOS {perclos:.2f} >= "
                f"{self._settings.warning_perclos:.2f} durante "
                f"{now - self._warning_since:.1f} s "
                f"(sostenimiento: "
                f"{self._settings.warning_sustain_seconds:.1f} s)."
            )

        if self._recovery_since is not None:
            reasons.append(
                f"Recuperación en curso: PERCLOS < "
                f"{self._settings.warning_exit_perclos:.2f} durante "
                f"{now - self._recovery_since:.1f} s de "
                f"{self._settings.recovery_sustain_seconds:.1f} s."
            )
        elif self._state in (
            FatigueState.WARNING,
            FatigueState.FATIGUE,
        ):
            current_perclos = (
                "sin datos"
                if perclos is None
                else f"{perclos:.2f}"
            )
            warning_closure_active = (
                closure is not None
                and closure
                >= self._settings.warning_closure_seconds
            )

            if warning_closure_active:
                reasons.append(
                    "Recuperación en espera: cierre ocular en curso "
                    f"(PERCLOS actual: {current_perclos})."
                )
            else:
                reasons.append(
                    "Recuperación: PERCLOS < "
                    f"{self._settings.warning_exit_perclos:.2f} "
                    "durante "
                    f"{self._settings.recovery_sustain_seconds:.1f} s "
                    f"(actual: {current_perclos})."
                )

        if not reasons:
            reasons.append("Sin indicadores de fatiga activos.")

        return reasons

    def _clear_timers(self) -> None:
        """Descarta los temporizadores por una pausa o un reinicio."""

        self._warning_since = None
        self._fatigue_since = None
        self._recovery_since = None
