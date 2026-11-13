"""Pipeline puro de cálculo de métricas visuales."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Callable

from config.settings import AppSettings
from vision.src.blink_detector import BlinkDetector
from vision.src.ear_calibrator import EARCalibrator
from vision.src.eye_closure import ProlongedClosureDetector
from vision.src.eye_state import EyeStateClassifier
from vision.src.models import (
    CalibrationStatus,
    MetricsSnapshot,
    PipelineUpdate,
    VisionEvent,
    VisionEventType,
)
from vision.src.perclos import PerclosCalculator


def _utc_now() -> datetime:
    """Devuelve la fecha y hora actual en UTC."""

    return datetime.now(timezone.utc)


def _finite_or_none(value: float | None) -> float | None:
    """Normaliza un valor numérico no finito a None."""

    if value is None:
        return None

    number = float(value)

    if not math.isfinite(number):
        return None

    return number


class MetricsPipeline:
    """
    Orquesta la calibración, la clasificación ocular y las métricas.

    No depende de OpenCV, MediaPipe ni de la interfaz. Recibe el
    estado del rostro y los valores EAR ya calculados, y devuelve
    una instantánea inmutable junto con los eventos ocurridos.

    La semántica de pausa, calibración y PERCLOS se conserva respecto
    al flujo anterior de face_tracker.py.
    """

    def __init__(
        self,
        settings: AppSettings,
        *,
        wall_clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._wall_clock = wall_clock or _utc_now
        self._threshold_factor = settings.eye_state.threshold_factor

        self._calibrator = EARCalibrator(
            duration_seconds=settings.calibration.duration_seconds,
            stabilization_seconds=(
                settings.calibration.stabilization_seconds
            ),
            minimum_ear=settings.calibration.minimum_ear,
        )
        self._classifier = EyeStateClassifier(
            threshold_factor=self._threshold_factor,
        )
        self._blink_detector = BlinkDetector(
            analysis_window_seconds=(
                settings.blink.analysis_window_seconds
            ),
            # Un cierre que alcanza el umbral de cierre prolongado
            # deja de contarse como parpadeo para no duplicar el
            # indicador ni inflar la frecuencia de parpadeo.
            max_duration_seconds=(
                settings.prolonged_closure.threshold_seconds
            ),
        )
        self._closure_detector = ProlongedClosureDetector(
            threshold_seconds=(
                settings.prolonged_closure.threshold_seconds
            ),
        )
        self._perclos_calculator = PerclosCalculator(
            window_seconds=settings.perclos.window_seconds,
            minimum_observation_seconds=(
                settings.perclos.minimum_observation_seconds
            ),
        )

        self._last_eye_state: str | None = None
        self._face_was_present = False
        self._has_seen_face = False

    def start_calibration(self) -> None:
        """
        Inicia una calibración nueva y reinicia las métricas derivadas.

        Se utiliza al comenzar una sesión o al solicitar una
        recalibración. La referencia ocular anterior deja de ser válida.
        """

        self._calibrator.start()
        self._classifier = EyeStateClassifier(
            threshold_factor=self._threshold_factor,
        )
        self._blink_detector.reset()
        self._closure_detector.reset()
        self._perclos_calculator.reset()
        self._last_eye_state = None
        self._face_was_present = False
        self._has_seen_face = False

    def update(
        self,
        *,
        face_present: bool,
        left_ear: float | None,
        right_ear: float | None,
        average_ear: float | None,
        has_new_result: bool,
    ) -> PipelineUpdate:
        """
        Actualiza el pipeline con el estado actual del rostro.

        face_present indica si el rostro debe considerarse presente.
        has_new_result indica si MediaPipe entregó un resultado nuevo.
        Solo se actualizan los detectores cuando ambas condiciones son
        verdaderas, igual que en el flujo anterior.
        """

        captured_at = self._wall_clock()
        events: list[VisionEvent] = []

        if face_present:
            self._calibrator.resume()
            self._blink_detector.resume()
            self._closure_detector.resume()
            self._perclos_calculator.resume()

            if self._has_seen_face and not self._face_was_present:
                events.append(
                    VisionEvent(
                        type=VisionEventType.FACE_RECOVERED,
                        occurred_at=captured_at,
                        message="Rostro recuperado.",
                    )
                )

            self._has_seen_face = True
        else:
            self._calibrator.pause()
            self._blink_detector.pause()
            self._closure_detector.pause()
            self._perclos_calculator.pause()
            self._last_eye_state = None

            if self._face_was_present:
                events.append(
                    VisionEvent(
                        type=VisionEventType.FACE_LOST,
                        occurred_at=captured_at,
                        message="Rostro no detectado.",
                    )
                )

        self._face_was_present = face_present

        if face_present and has_new_result:
            self._update_detectors(
                average_ear=average_ear,
                captured_at=captured_at,
                events=events,
            )

        snapshot = self._build_snapshot(
            captured_at=captured_at,
            face_present=face_present,
            left_ear=left_ear,
            right_ear=right_ear,
            average_ear=average_ear,
        )

        return PipelineUpdate(
            snapshot=snapshot,
            calibration=self._build_calibration_status(),
            events=tuple(events),
        )

    def _update_detectors(
        self,
        *,
        average_ear: float | None,
        captured_at: datetime,
        events: list[VisionEvent],
    ) -> None:
        """Actualiza calibración, clasificación y detectores."""

        was_completed = self._calibrator.is_completed()

        if average_ear is not None:
            self._calibrator.update(average_ear)

        completed = self._calibrator.is_completed()
        reference_ear = self._calibrator.get_reference_ear()

        if completed and not was_completed:
            if reference_ear is None:
                events.append(
                    VisionEvent(
                        type=VisionEventType.CALIBRATION_FAILED,
                        occurred_at=captured_at,
                        message=(
                            "Calibración finalizada sin muestras válidas."
                        ),
                    )
                )
            else:
                events.append(
                    VisionEvent(
                        type=VisionEventType.CALIBRATION_COMPLETED,
                        occurred_at=captured_at,
                        message="Calibración completada.",
                    )
                )

        if reference_ear is None:
            return

        if self._classifier.get_reference_ear() is None:
            self._classifier.set_reference_ear(reference_ear)

        if average_ear is None:
            return

        eye_state = self._classifier.classify(average_ear)
        self._last_eye_state = eye_state

        self._blink_detector.update(eye_state)
        self._perclos_calculator.update(eye_state)
        prolonged_event = self._closure_detector.update(eye_state)

        if prolonged_event:
            duration = self._closure_detector.get_current_closed_duration()

            if duration is None:
                duration = (
                    self._closure_detector.get_last_prolonged_duration()
                )

            if duration is None:
                duration = 0.0

            events.append(
                VisionEvent(
                    type=VisionEventType.PROLONGED_CLOSURE,
                    occurred_at=captured_at,
                    message="Cierre prolongado detectado.",
                    duration_seconds=duration,
                )
            )

        if self._blink_detector.is_blink():
            events.append(
                VisionEvent(
                    type=VisionEventType.BLINK,
                    occurred_at=captured_at,
                    message="Parpadeo detectado.",
                    duration_seconds=(
                        self._blink_detector.get_last_closed_duration()
                    ),
                )
            )

    def _build_snapshot(
        self,
        *,
        captured_at: datetime,
        face_present: bool,
        left_ear: float | None,
        right_ear: float | None,
        average_ear: float | None,
    ) -> MetricsSnapshot:
        """Construye la instantánea de métricas."""

        if face_present:
            left_value = _finite_or_none(left_ear)
            right_value = _finite_or_none(right_ear)
            average_value = _finite_or_none(average_ear)
            eye_state = self._last_eye_state
        else:
            left_value = None
            right_value = None
            average_value = None
            eye_state = None

        return MetricsSnapshot(
            captured_at=captured_at,
            elapsed_seconds=(
                self._perclos_calculator.get_observation_duration()
            ),
            face_present=face_present,
            left_ear=left_value,
            right_ear=right_value,
            average_ear=average_value,
            eye_state=eye_state,
            blink_count=self._blink_detector.get_blink_count(),
            last_closed_duration=(
                self._blink_detector.get_last_closed_duration()
            ),
            mean_closed_duration=(
                self._blink_detector.get_average_closed_duration()
            ),
            blink_rate_per_minute=(
                self._blink_detector.get_blink_rate_per_minute()
            ),
            time_since_last_blink=(
                self._blink_detector.get_time_since_last_blink()
            ),
            current_closed_duration=(
                self._closure_detector.get_current_closed_duration()
            ),
            prolonged_closure_count=(
                self._closure_detector.get_prolonged_count()
            ),
            prolonged_active=self._closure_detector.is_prolonged(),
            perclos=self._perclos_calculator.get_perclos(),
            perclos_window_seconds=(
                self._perclos_calculator.get_window_seconds()
            ),
            paused=self._blink_detector.is_paused(),
        )

    def _build_calibration_status(self) -> CalibrationStatus:
        """Construye el estado actual de la calibración."""

        return CalibrationStatus(
            completed=self._calibrator.is_completed(),
            paused=self._calibrator.is_paused(),
            progress=self._calibrator.get_progress(),
            sample_count=self._calibrator.get_sample_count(),
            current_ear=self._calibrator.get_current_ear(),
            reference_ear=self._calibrator.get_reference_ear(),
            eye_threshold=self._classifier.get_threshold(),
        )
