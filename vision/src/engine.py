"""Motor de captura y detección facial sin dependencia de la interfaz."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import cv2
import mediapipe as mp
import numpy as np

from config.settings import AppSettings, CameraSettings
from vision.src.face_metrics import eye_aspect_ratio
from vision.src.face_presence import is_face_present
from vision.src.metrics_pipeline import MetricsPipeline
from vision.src.models import PipelineUpdate


logger = logging.getLogger(__name__)


# Landmarks de los ojos utilizados para calcular EAR.
LEFT_EYE_POINTS = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_POINTS = [362, 385, 387, 263, 373, 380]


class VisionEngineError(RuntimeError):
    """Error controlado del motor de visión."""


class CameraOpenError(VisionEngineError):
    """No fue posible abrir la cámara."""


class CameraReadError(VisionEngineError):
    """No fue posible leer un frame de la cámara."""


@dataclass(frozen=True)
class EngineFrame:
    """Frame procesado junto con su actualización de métricas."""

    frame: np.ndarray
    landmarks: tuple[tuple[float, float], ...]
    update: PipelineUpdate
    # Indica si MediaPipe entregó un resultado nuevo para este frame.
    has_new_result: bool


@dataclass
class _LatestLandmarkResult:
    """Último resultado compartido entre MediaPipe y el hilo principal."""

    face_detected: bool = False
    result_received_at: float | None = None
    result_id: int = 0
    left_ear: float = 0.0
    right_ear: float = 0.0
    average_ear: float = 0.0
    landmarks: tuple[tuple[float, float], ...] = ()


def create_face_landmarker(
    model_path: Path,
    result_callback: Callable[..., None],
):
    """Crea el Face Landmarker de MediaPipe en modo LIVE_STREAM."""

    if not model_path.exists():
        raise FileNotFoundError(
            "No se encontró el modelo de MediaPipe en "
            f"{model_path}. Descárgalo desde la URL oficial "
            "indicada en la documentación."
        )

    base_options = mp.tasks.BaseOptions(
        model_asset_path=str(model_path)
    )

    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
        num_faces=1,
        result_callback=result_callback,
    )

    return mp.tasks.vision.FaceLandmarker.create_from_options(options)


def _open_camera(settings: CameraSettings):
    """Abre la cámara configurada y solicita la resolución indicada."""

    camera = cv2.VideoCapture(settings.index)

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, settings.width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.height)

    if not camera.isOpened():
        camera.release()
        raise CameraOpenError(
            "No se pudo abrir la cámara. Comprueba que no esté "
            "siendo utilizada por otra aplicación."
        )

    return camera


class VisionEngine:
    """
    Sesión síncrona de captura, inferencia y cálculo de métricas.

    El motor no dibuja ni conoce la interfaz. El consumidor debe
    llamar a start(), step() y stop(). En la integración web, step()
    se ejecutará dentro de un hilo de trabajo.
    """

    def __init__(
        self,
        settings: AppSettings,
        *,
        camera_factory: Callable[[CameraSettings], Any] | None = None,
        landmarker_factory: (
            Callable[[Path, Callable[..., None]], Any] | None
        ) = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._settings = settings
        self._camera_factory = camera_factory or _open_camera
        self._landmarker_factory = (
            landmarker_factory or create_face_landmarker
        )
        self._clock = clock or time.monotonic

        self._pipeline = MetricsPipeline(settings)

        self._camera: Any | None = None
        self._landmarker: Any | None = None
        self._running = False

        self._result_lock = threading.Lock()
        self._latest_result = _LatestLandmarkResult()

        self._last_result_id = 0
        self._last_timestamp_ms = 0
        self._landmark_error_reported = False

    @property
    def is_running(self) -> bool:
        """Indica si el motor está iniciado."""

        return self._running

    def start(self) -> None:
        """Abre la cámara, carga el modelo e inicia la calibración."""

        if self._running:
            return

        camera = self._camera_factory(self._settings.camera)

        try:
            landmarker = self._landmarker_factory(
                self._settings.vision.model_path,
                self._on_face_landmarker_result,
            )
        except Exception:
            camera.release()
            raise

        self._camera = camera
        self._landmarker = landmarker
        self._last_result_id = 0
        self._last_timestamp_ms = 0
        self._landmark_error_reported = False

        with self._result_lock:
            self._latest_result = _LatestLandmarkResult()

        self._pipeline.start_calibration()
        self._running = True

    def step(self) -> EngineFrame:
        """
        Procesa un frame y devuelve el estado visual actualizado.

        No espera a que MediaPipe termine la inferencia; utiliza el
        último resultado asíncrono disponible, igual que el flujo
        anterior.
        """

        if not self._running or self._camera is None:
            raise VisionEngineError(
                "El motor de visión no está iniciado."
            )

        success, frame = self._camera.read()

        if not success or frame is None:
            raise CameraReadError(
                "No se pudo obtener un frame de la cámara."
            )

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB,
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame,
        )

        timestamp_ms = int(self._clock() * 1000)

        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1

        self._last_timestamp_ms = timestamp_ms

        self._landmarker.detect_async(
            mp_image,
            timestamp_ms,
        )

        with self._result_lock:
            result_id = self._latest_result.result_id
            face_detected = self._latest_result.face_detected
            result_received_at = (
                self._latest_result.result_received_at
            )
            left_ear = self._latest_result.left_ear
            right_ear = self._latest_result.right_ear
            average_ear = self._latest_result.average_ear
            landmarks = self._latest_result.landmarks

        now = self._clock()

        face_present = is_face_present(
            face_detected,
            result_received_at,
            now,
            timeout_seconds=(
                self._settings.face.loss_timeout_seconds
            ),
        )

        new_result = result_id != self._last_result_id

        if new_result:
            self._last_result_id = result_id

        update = self._pipeline.update(
            face_present=face_present,
            left_ear=left_ear,
            right_ear=right_ear,
            average_ear=average_ear,
            has_new_result=new_result,
        )

        return EngineFrame(
            frame=frame,
            landmarks=landmarks,
            update=update,
            has_new_result=new_result,
        )

    def restart_calibration(self) -> None:
        """Reinicia la calibración y las métricas derivadas."""

        self._pipeline.start_calibration()

    def stop(self) -> None:
        """Libera la cámara y cierra el modelo de MediaPipe."""

        if self._camera is not None:
            self._camera.release()
            self._camera = None

        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None

        self._running = False

    def __enter__(self) -> "VisionEngine":
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()

    def _on_face_landmarker_result(
        self,
        result,
        output_image,
        timestamp_ms,
    ) -> None:
        """Callback de MediaPipe para el último resultado disponible."""

        del output_image
        del timestamp_ms

        face_detected = False
        left_ear = 0.0
        right_ear = 0.0
        average_ear = 0.0
        landmarks: tuple[tuple[float, float], ...] = ()

        if result.face_landmarks:
            try:
                face = result.face_landmarks[0]

                left_eye = [
                    (face[index].x, face[index].y)
                    for index in LEFT_EYE_POINTS
                ]

                right_eye = [
                    (face[index].x, face[index].y)
                    for index in RIGHT_EYE_POINTS
                ]

                left_ear = eye_aspect_ratio(left_eye)
                right_ear = eye_aspect_ratio(right_eye)
                average_ear = (left_ear + right_ear) / 2.0

                landmarks = tuple(
                    (landmark.x, landmark.y)
                    for landmark in face
                )

                face_detected = True
                self._landmark_error_reported = False

            except (IndexError, ValueError) as error:
                # Landmarks incompletos o degenerados: se trata
                # como ausencia de rostro, no como ojos cerrados.
                face_detected = False
                left_ear = 0.0
                right_ear = 0.0
                average_ear = 0.0
                landmarks = ()

                if not self._landmark_error_reported:
                    logger.warning(
                        "Landmarks faciales inválidos: %s. "
                        "Se ignora el frame.",
                        error,
                    )
                    self._landmark_error_reported = True

        with self._result_lock:
            self._latest_result.face_detected = face_detected
            self._latest_result.left_ear = left_ear
            self._latest_result.right_ear = right_ear
            self._latest_result.average_ear = average_ear
            self._latest_result.landmarks = landmarks
            self._latest_result.result_received_at = self._clock()
            self._latest_result.result_id += 1
