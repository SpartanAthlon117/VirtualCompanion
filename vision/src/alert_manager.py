"""Gestión de alertas de fatiga con deduplicación y cooldown.

El gestor convierte una ``Assessment`` en cero o una alerta. Solo se
emite una alerta al entrar en un estado que requiere atención, no en
cada evaluación del mismo estado. El cooldown limita la frecuencia con
la que puede repetirse una alerta del mismo nivel si el estado oscila.

Las alertas son indicadores de apoyo del prototipo, no un diagnóstico
clínico ni una garantía de prevención de accidentes.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Callable

from config.settings import AlertSettings
from vision.src.models import (
    AlertEvent,
    AlertLevel,
    AlertType,
    Assessment,
    FatigueState,
)

_LEVEL_BY_STATE = {
    FatigueState.NORMAL: AlertLevel.NONE,
    FatigueState.WARNING: AlertLevel.WARNING,
    FatigueState.FATIGUE: AlertLevel.CRITICAL,
}

_TYPE_BY_LEVEL = {
    AlertLevel.WARNING: AlertType.FATIGUE_WARNING,
    AlertLevel.CRITICAL: AlertType.FATIGUE_CRITICAL,
}


def _utc_now() -> datetime:
    """Devuelve la fecha y hora actual en UTC."""

    return datetime.now(timezone.utc)


class AlertManager:
    """
    Emite alertas al cambiar a un estado que requiere atención.

    El reloj monotónico controla el cooldown y se puede inyectar en las
    pruebas. ``wall_clock`` solo determina la fecha de la alerta.

    Mientras el rostro no está presente no se emiten alertas ni se
    actualiza el estado recordado: la evaluación está en pausa.
    """

    def __init__(
        self,
        settings: AlertSettings,
        clock: Callable[[], float] | None = None,
        wall_clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._settings = settings
        self._clock = clock or time.monotonic
        self._wall_clock = wall_clock or _utc_now
        self.reset()

    def reset(self) -> None:
        """Olvida el estado previo y los cooldowns registrados."""

        self._last_state: str | None = None
        self._last_emitted: dict[str, float] = {}

    @staticmethod
    def level_for(state: str) -> str:
        """Devuelve el nivel de alerta asociado a un estado de fatiga."""

        try:
            return _LEVEL_BY_STATE[state]
        except KeyError as error:
            raise ValueError(f"Estado de fatiga desconocido: {state}.") from error

    def update(self, assessment: Assessment) -> tuple[AlertEvent, ...]:
        """
        Evalúa una ``Assessment`` y devuelve las alertas a emitir.

        La alerta se genera solo si el estado cambió respecto a la
        evaluación anterior y su cooldown ya expiró. Una evaluación en
        pausa no altera el estado recordado.
        """

        if assessment.paused:
            return ()

        level = self.level_for(assessment.state)
        previous_state = self._last_state
        self._last_state = assessment.state

        if assessment.state == previous_state:
            return ()

        if level == AlertLevel.NONE:
            return ()

        alert_type = _TYPE_BY_LEVEL[level]
        now = self._clock()
        cooldown = self._cooldown_for(level)
        last_emitted = self._last_emitted.get(alert_type)

        if last_emitted is not None and now - last_emitted < cooldown:
            return ()

        self._last_emitted[alert_type] = now

        return (
            AlertEvent(
                type=alert_type,
                level=level,
                message=self._build_message(level, assessment),
                occurred_at=self._wall_clock(),
            ),
        )

    def _cooldown_for(self, level: str) -> float:
        """Devuelve el cooldown configurado para un nivel de alerta."""

        if level == AlertLevel.WARNING:
            return self._settings.warning_cooldown_seconds

        if level == AlertLevel.CRITICAL:
            return self._settings.critical_cooldown_seconds

        return 0.0

    @staticmethod
    def _build_message(level: str, assessment: Assessment) -> str:
        """Construye el mensaje de usuario a partir del motivo principal."""

        reason = (
            assessment.reasons[0]
            if assessment.reasons
            else "Estado de fatiga detectado."
        )

        if level == AlertLevel.CRITICAL:
            return f"Fatiga crítica: {reason}"

        return f"Advertencia de fatiga: {reason}"
