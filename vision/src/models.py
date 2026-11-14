"""Contratos internos del motor de visión."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


class VisionEventType:
    """Tipos de evento emitidos por el pipeline de métricas."""

    BLINK = "BLINK"
    PROLONGED_CLOSURE = "PROLONGED_CLOSURE"
    CALIBRATION_COMPLETED = "CALIBRATION_COMPLETED"
    CALIBRATION_FAILED = "CALIBRATION_FAILED"
    FACE_LOST = "FACE_LOST"
    FACE_RECOVERED = "FACE_RECOVERED"


class FatigueState:
    """Estados de la evaluación experimental de fatiga."""

    NORMAL = "NORMAL"
    WARNING = "WARNING"
    FATIGUE = "FATIGUE"


class AlertLevel:
    """Niveles de alerta presentados al usuario."""

    NONE = "NONE"
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertType:
    """Tipos de alerta emitidos por el gestor."""

    FATIGUE_WARNING = "FATIGUE_WARNING"
    FATIGUE_CRITICAL = "FATIGUE_CRITICAL"


@dataclass(frozen=True)
class Assessment:
    """Resultado de la evaluación experimental del estado de fatiga."""

    state: str
    reasons: tuple[str, ...]
    changed: bool
    paused: bool
    alert_level: str = AlertLevel.NONE


@dataclass(frozen=True)
class CalibrationStatus:
    """Estado actual de la calibración del EAR."""

    completed: bool
    paused: bool
    progress: float
    sample_count: int
    current_ear: float | None
    reference_ear: float | None
    eye_threshold: float | None


@dataclass(frozen=True)
class VisionEvent:
    """Evento relevante generado durante el procesamiento."""

    type: str
    occurred_at: datetime
    message: str
    duration_seconds: float | None = None


@dataclass(frozen=True)
class AlertEvent:
    """Alerta generada al entrar en un estado que requiere atención."""

    type: str
    level: str
    message: str
    occurred_at: datetime
    id: int | None = None


@dataclass(frozen=True)
class MetricsSnapshot:
    """Instantánea de los indicadores visuales observados."""

    captured_at: datetime
    elapsed_seconds: float
    face_present: bool
    left_ear: float | None
    right_ear: float | None
    average_ear: float | None
    eye_state: str | None
    blink_count: int
    last_closed_duration: float | None
    mean_closed_duration: float | None
    blink_rate_per_minute: float
    time_since_last_blink: float | None
    current_closed_duration: float | None
    prolonged_closure_count: int
    prolonged_active: bool
    perclos: float | None
    perclos_window_seconds: float
    paused: bool


@dataclass(frozen=True)
class PipelineUpdate:
    """Resultado de una actualización del pipeline."""

    snapshot: MetricsSnapshot
    calibration: CalibrationStatus
    events: tuple[VisionEvent, ...]
    assessment: Assessment
    alerts: tuple[AlertEvent, ...]
