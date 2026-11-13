"""Adaptador CLI de desarrollo para el motor de visión."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.logging_setup import configure_logging
from config.settings import AppSettings, load_settings
from vision.src.engine import VisionEngine, VisionEngineError
from vision.src.models import (
    CalibrationStatus,
    MetricsSnapshot,
    VisionEvent,
    VisionEventType,
)
from vision.src.overlay_metrics import build_metrics_lines, format_perclos


WINDOW_NAME = "Virtual Companion - Face Tracking"

# Intervalo mínimo entre líneas DEBUG para no inundar la consola.
DEBUG_PRINT_INTERVAL_SECONDS = 1.0


def main() -> None:
    """Ejecuta el seguimiento facial con overlay de desarrollo."""

    settings = load_settings()
    logger = configure_logging(settings.logging)
    engine = VisionEngine(settings)
    started = False
    last_debug_elapsed: float | None = None

    try:
        engine.start()
        started = True

        logger.info(
            "Sesión iniciada. Modelo=%s Cámara=%d Resolución=%dx%d",
            settings.vision.model_path.name,
            settings.camera.index,
            settings.camera.width,
            settings.camera.height,
        )

        print("Face landmarker iniciado correctamente.")
        print("Modo: LIVE_STREAM")
        print("Presiona 'q' o ESC para salir.")
        print("También puedes cerrar la ventana con X.")
        print("Calibración EAR iniciada.")

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

        while True:
            engine_frame = engine.step()
            frame = engine_frame.frame
            update = engine_frame.update

            for event in update.events:
                _log_event(logger, event)

                if event.duration_seconds is None:
                    print(f"EVENTO | {event.message}")
                else:
                    print(
                        f"EVENTO | {event.message} "
                        f"Duración: {event.duration_seconds:.3f}s"
                    )

            # Sin rostro, el evento FACE_LOST ya informa de la pausa.
            if (
                engine_frame.has_new_result
                and update.snapshot.face_present
            ):
                elapsed = update.snapshot.elapsed_seconds

                if _debug_is_due(elapsed, last_debug_elapsed):
                    _print_debug_update(
                        update.snapshot,
                        update.calibration,
                    )
                    last_debug_elapsed = elapsed

            _draw_face_status(
                frame,
                update.snapshot,
                engine_frame.landmarks,
            )
            _draw_calibration_and_metrics(
                frame,
                settings,
                update.snapshot,
                update.calibration,
            )

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == 27:
                print("Solicitud de salida recibida.")
                break

            if cv2.getWindowProperty(
                WINDOW_NAME,
                cv2.WND_PROP_VISIBLE,
            ) < 1:
                print("Ventana cerrada por el usuario.")
                break

    except (FileNotFoundError, VisionEngineError) as error:
        logger.error("Error durante la sesión: %s", error)
        print(f"ERROR: {error}")

    finally:
        engine.stop()
        cv2.destroyAllWindows()

        if started:
            logger.info("Sesión finalizada. Cámara liberada.")
            print("Cámara liberada correctamente.")


def _draw_face_status(
    frame,
    snapshot: MetricsSnapshot,
    landmarks: tuple[tuple[float, float], ...],
) -> None:
    """Dibuja landmarks, rostro y valores EAR."""

    if snapshot.face_present:
        for x_normalized, y_normalized in landmarks:
            x = int(x_normalized * frame.shape[1])
            y = int(y_normalized * frame.shape[0])
            cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

        cv2.putText(
            frame,
            "Rostro detectado",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        cv2.putText(
            frame,
            f"EAR izquierdo: {_format_ear(snapshot.left_ear)}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"EAR derecho: {_format_ear(snapshot.right_ear)}",
            (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"EAR promedio: {_format_ear(snapshot.average_ear)}",
            (20, 135),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
    else:
        cv2.putText(
            frame,
            "Rostro no detectado",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
        )


def _draw_calibration_and_metrics(
    frame,
    settings: AppSettings,
    snapshot: MetricsSnapshot,
    calibration: CalibrationStatus,
) -> None:
    """Dibuja el estado de calibración o las métricas activas."""

    if not calibration.completed:
        progress = calibration.progress * 100

        if snapshot.face_present:
            calibration_title = "CALIBRANDO EAR..."
            calibration_help = "Ojos abiertos, por favor"
            calibration_color = (0, 255, 255)
        else:
            calibration_title = "CALIBRACION EN PAUSA"
            calibration_help = "Acerca el rostro a la camara"
            calibration_color = (0, 0, 255)

        cv2.putText(
            frame,
            calibration_title,
            (20, 170),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            calibration_color,
            2,
        )

        cv2.putText(
            frame,
            calibration_help,
            (20, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"Progreso: {progress:.0f}%",
            (20, 230),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"Muestras: {calibration.sample_count}",
            (20, 260),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        if calibration.current_ear is not None:
            cv2.putText(
                frame,
                f"EAR actual: {calibration.current_ear:.3f}",
                (20, 290),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

        return

    reference_ear = calibration.reference_ear

    if reference_ear is None:
        cv2.putText(
            frame,
            "Calibracion sin muestras validas",
            (20, 170),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )

        cv2.putText(
            frame,
            "Reinicia la aplicacion para calibrar",
            (20, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )

        return

    cv2.putText(
        frame,
        f"EAR referencia: {reference_ear:.3f}",
        (20, 170),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
    )

    if snapshot.face_present and snapshot.eye_state is not None:
        cv2.putText(
            frame,
            f"Ojos: {snapshot.eye_state}",
            (20, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

    if calibration.eye_threshold is None:
        return

    metrics_lines = build_metrics_lines(
        blink_count=snapshot.blink_count,
        last_closed_duration=snapshot.last_closed_duration,
        average_closed_duration=snapshot.mean_closed_duration,
        blink_rate_per_minute=snapshot.blink_rate_per_minute,
        time_since_last_blink=snapshot.time_since_last_blink,
        paused=snapshot.paused,
        current_closed_duration=snapshot.current_closed_duration,
        prolonged_closure_count=snapshot.prolonged_closure_count,
        prolonged_threshold_seconds=(
            settings.prolonged_closure.threshold_seconds
        ),
        prolonged_active=snapshot.prolonged_active,
        perclos=snapshot.perclos,
        perclos_window_seconds=snapshot.perclos_window_seconds,
    )

    metrics_start_y = 220
    metrics_line_height = 26

    for index, text in enumerate(metrics_lines):
        is_status_line = index == len(metrics_lines) - 1

        if is_status_line:
            color = (
                (0, 255, 255)
                if snapshot.paused
                else (0, 255, 0)
            )
        elif (
            snapshot.prolonged_active
            and text.startswith("Cierre actual:")
        ):
            color = (0, 0, 255)
        else:
            color = (255, 255, 255)

        cv2.putText(
            frame,
            text,
            (
                20,
                metrics_start_y + index * metrics_line_height,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )


def _log_event(logger: logging.Logger, event: VisionEvent) -> None:
    """Registra un evento con el nivel adecuado en el archivo de log."""

    level = (
        logging.WARNING
        if event.type == VisionEventType.CALIBRATION_FAILED
        else logging.INFO
    )

    if event.duration_seconds is None:
        logger.log(level, "%s", event.message)
    else:
        logger.log(
            level,
            "%s Duración: %.3f s",
            event.message,
            event.duration_seconds,
        )


def _debug_is_due(
    elapsed: float,
    last_printed: float | None,
) -> bool:
    """
    Indica si toca imprimir la línea DEBUG.

    Se imprime como máximo una línea por intervalo. Si el tiempo de
    observación retrocede (por ejemplo, tras reiniciar la observación),
    se vuelve a imprimir de inmediato.
    """

    if last_printed is None:
        return True

    if elapsed < last_printed:
        return True

    return elapsed - last_printed >= DEBUG_PRINT_INTERVAL_SECONDS


def _print_debug_update(
    snapshot: MetricsSnapshot,
    calibration: CalibrationStatus,
) -> None:
    """Imprime un resumen de depuración por cada intervalo."""

    print(
        "DEBUG | "
        f"Observacion PERCLOS: {snapshot.elapsed_seconds:.2f}s | "
        f"EAR: {_format_ear(snapshot.average_ear)} | "
        f"Completada: {calibration.completed} | "
        f"Muestras: {calibration.sample_count} | "
        f"Ojos: {snapshot.eye_state} | "
        f"Parpadeos: {snapshot.blink_count} | "
        f"PERCLOS: {format_perclos(snapshot.perclos)}"
    )


def _format_ear(value: float | None) -> str:
    """Formatea un valor EAR para el overlay."""

    if value is None:
        return "--"

    return f"{value:.3f}"


if __name__ == "__main__":
    main()
