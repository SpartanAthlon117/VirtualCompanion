"""Pruebas del motor de visión con cámara y landmarker falsos."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from config.settings import load_settings
from vision.src.engine import (
    CameraReadError,
    VisionEngine,
    VisionEngineError,
)


FRAME = np.zeros((48, 64, 3), dtype=np.uint8)


class FakeCamera:
    """Cámara controlada para pruebas sin hardware."""

    def __init__(self, frames):
        self.frames = list(frames)
        self.released = False
        self.properties = {}

    def set(self, prop, value):
        self.properties[prop] = value

    def isOpened(self):
        return True

    def read(self):
        if not self.frames:
            return False, None

        return True, self.frames.pop(0)

    def release(self):
        self.released = True


class FakeLandmarker:
    """Landmarker que entrega un resultado de forma inmediata."""

    def __init__(self, result):
        self.result = result
        self.callback = None
        self.closed = False
        self.calls = 0

    def detect_async(self, image, timestamp_ms):
        self.calls += 1
        self.callback(self.result, None, timestamp_ms)

    def close(self):
        self.closed = True


class SilentLandmarker:
    """Landmarker que todavía no ha entregado resultados."""

    def __init__(self):
        self.closed = False
        self.calls = 0

    def detect_async(self, image, timestamp_ms):
        self.calls += 1

    def close(self):
        self.closed = True


def make_face_result():
    """Construye un rostro sintético con EAR estable."""

    points = [
        SimpleNamespace(x=0.5, y=0.5)
        for _ in range(478)
    ]

    def set_point(index, x, y):
        points[index] = SimpleNamespace(x=x, y=y)

    # Ojo izquierdo.
    set_point(33, 0.20, 0.50)
    set_point(160, 0.225, 0.48)
    set_point(158, 0.25, 0.48)
    set_point(133, 0.30, 0.50)
    set_point(153, 0.25, 0.52)
    set_point(144, 0.225, 0.52)

    # Ojo derecho.
    set_point(362, 0.60, 0.50)
    set_point(385, 0.625, 0.48)
    set_point(387, 0.65, 0.48)
    set_point(263, 0.70, 0.50)
    set_point(373, 0.65, 0.52)
    set_point(380, 0.625, 0.52)

    return SimpleNamespace(face_landmarks=[points])


def make_engine(
    camera,
    result,
    settings=None,
):
    """Crea un motor con cámara y landmarker falsos."""

    landmarker = FakeLandmarker(result)

    def landmarker_factory(model_path, callback):
        del model_path
        landmarker.callback = callback
        return landmarker

    engine = VisionEngine(
        settings or load_settings(),
        camera_factory=lambda settings: camera,
        landmarker_factory=landmarker_factory,
    )

    return engine, landmarker


def test_step_without_face_returns_paused_snapshot():
    camera = FakeCamera([FRAME])
    engine, landmarker = make_engine(
        camera,
        SimpleNamespace(face_landmarks=[]),
    )

    engine.start()
    result = engine.step()

    assert result.frame is FRAME
    assert result.landmarks == ()
    assert result.has_new_result is True
    assert result.update.snapshot.face_present is False
    assert result.update.snapshot.paused is True

    engine.stop()

    assert camera.released is True
    assert landmarker.closed is True


def test_step_with_face_calculates_ear():
    camera = FakeCamera([FRAME])
    engine, _ = make_engine(camera, make_face_result())

    engine.start()
    result = engine.step()

    assert result.has_new_result is True
    assert result.update.snapshot.face_present is True
    assert result.update.snapshot.average_ear == pytest.approx(0.40)
    assert len(result.landmarks) == 478
    assert result.update.snapshot.eye_state is None

    engine.stop()


def test_step_without_new_result_is_marked():
    camera = FakeCamera([FRAME])
    landmarker = SilentLandmarker()
    engine = VisionEngine(
        load_settings(),
        camera_factory=lambda settings: camera,
        landmarker_factory=lambda model_path, callback: landmarker,
    )

    engine.start()
    result = engine.step()

    assert result.has_new_result is False
    assert result.update.snapshot.face_present is False

    engine.stop()


def test_camera_read_failure_raises_controlled_error():
    camera = FakeCamera([])
    engine, _ = make_engine(
        camera,
        SimpleNamespace(face_landmarks=[]),
    )

    engine.start()

    with pytest.raises(CameraReadError):
        engine.step()

    engine.stop()


def test_step_before_start_is_rejected():
    camera = FakeCamera([FRAME])
    engine, _ = make_engine(
        camera,
        SimpleNamespace(face_landmarks=[]),
    )

    with pytest.raises(VisionEngineError):
        engine.step()


def test_missing_model_releases_camera(tmp_path):
    settings = load_settings()
    settings = replace(
        settings,
        vision=replace(
            settings.vision,
            model_path=tmp_path / "missing.task",
        ),
    )
    camera = FakeCamera([FRAME])
    engine = VisionEngine(
        settings,
        camera_factory=lambda settings: camera,
    )

    with pytest.raises(FileNotFoundError, match="No se encontró"):
        engine.start()

    assert camera.released is True


def test_stop_is_idempotent():
    camera = FakeCamera([FRAME])
    engine, landmarker = make_engine(
        camera,
        SimpleNamespace(face_landmarks=[]),
    )

    engine.start()
    engine.stop()
    engine.stop()

    assert engine.is_running is False
    assert camera.released is True
    assert landmarker.closed is True
