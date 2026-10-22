import cv2
import mediapipe as mp
import threading
import time

from pathlib import Path

from face_metrics import eye_aspect_ratio
from face_presence import is_face_present
from ear_calibrator import EARCalibrator
# Incorporación de la clase EyeStateClassifier
# para el control de los ojos.
from eye_state import EyeStateClassifier
from blink_detector import BlinkDetector
from overlay_metrics import build_metrics_lines


MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "face_landmarker.task"
)
WINDOW_NAME = "Virtual Companion - Face Tracking"

# Landmarks de los ojos utilizados para calcular EAR.
LEFT_EYE_POINTS = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_POINTS = [362, 385, 387, 263, 373, 380]


def create_face_landmarker(result_callback):
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "No se encontró el modelo de MediaPipe en "
            f"{MODEL_PATH}. Descárgalo desde la URL oficial "
            "indicada en la documentación."
        )

    base_options = mp.tasks.BaseOptions(
        model_asset_path=str(MODEL_PATH)
    )

    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
        num_faces=1,
        result_callback=result_callback,
    )

    return mp.tasks.vision.FaceLandmarker.create_from_options(options)


def main():
    camera = cv2.VideoCapture(0)

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not camera.isOpened():
        print("ERROR: No se pudo abrir la cámara.")
        return

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    # Estado compartido entre el callback de MediaPipe
    # y el hilo principal.
    latest_result = {
        "face_detected": False,
        "result_received_at": None,
        "result_id": 0,
        "left_ear": 0.0,
        "right_ear": 0.0,
        "average_ear": 0.0,
        "landmarks": [],
    }

    result_lock = threading.Lock()

    calibrator = EARCalibrator(
        duration_seconds=5.0,
        stabilization_seconds=1.0,
        minimum_ear=0.15,
    )

    eye_classifier = EyeStateClassifier(
        threshold_factor=0.70,
    )

    blink_detector = BlinkDetector()

    landmark_error_reported = False

    def on_face_landmarker_result(
        result,
        output_image,
        timestamp_ms,
    ):
        nonlocal landmark_error_reported
        del output_image
        del timestamp_ms

        face_detected = False
        left_ear = 0.0
        right_ear = 0.0
        average_ear = 0.0
        landmarks = []

        if result.face_landmarks:
            try:
                # Obtener el primer rostro detectado.
                face = result.face_landmarks[0]

                # Obtener los seis puntos necesarios
                # para cada ojo.
                left_eye = [
                    (
                        face[index].x,
                        face[index].y,
                    )
                    for index in LEFT_EYE_POINTS
                ]

                right_eye = [
                    (
                        face[index].x,
                        face[index].y,
                    )
                    for index in RIGHT_EYE_POINTS
                ]

                # Calcular EAR de ambos ojos.
                left_ear = eye_aspect_ratio(left_eye)
                right_ear = eye_aspect_ratio(right_eye)

                # EAR promedio.
                average_ear = (
                    left_ear + right_ear
                ) / 2.0

                # Copiar los landmarks como datos simples.
                landmarks = [
                    (
                        landmark.x,
                        landmark.y,
                    )
                    for landmark in face
                ]

                face_detected = True
                landmark_error_reported = False

            except (IndexError, ValueError) as error:
                # Landmarks incompletos o degenerados: se trata
                # como ausencia de rostro, no como ojos cerrados.
                face_detected = False
                left_ear = 0.0
                right_ear = 0.0
                average_ear = 0.0
                landmarks = []

                if not landmark_error_reported:
                    print(
                        "ADVERTENCIA | Landmarks faciales inválidos: "
                        f"{error}. Se ignora el frame."
                    )
                    landmark_error_reported = True

        # Actualizar el último resultado disponible.
        with result_lock:
            latest_result["face_detected"] = face_detected
            latest_result["left_ear"] = left_ear
            latest_result["right_ear"] = right_ear
            latest_result["average_ear"] = average_ear
            latest_result["landmarks"] = landmarks
            latest_result["result_received_at"] = time.monotonic()
            latest_result["result_id"] += 1

    try:
        with create_face_landmarker(
            on_face_landmarker_result
        ) as landmarker:

            print(
                "Face landmarker iniciado correctamente."
            )
            print("Modo: LIVE_STREAM")
            print("Presiona 'q' o ESC para salir.")
            print(
                "También puedes cerrar la ventana con X."
            )

            calibrator.start()

            print("Calibración EAR iniciada.")

            calibration_start = time.monotonic()

            last_timestamp_ms = 0
            face_was_present = False
            last_result_id = 0
            last_eye_state = None

            while True:
                success, frame = camera.read()

                if not success:
                    print(
                        "ERROR: No se pudo obtener "
                        "un frame de la cámara."
                    )
                    break

                rgb_frame = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2RGB,
                )

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb_frame,
                )

                # Timestamp real.
                timestamp_ms = (
                    time.monotonic_ns() // 1_000_000
                )

                # MediaPipe requiere timestamps crecientes.
                if timestamp_ms <= last_timestamp_ms:
                    timestamp_ms = (
                        last_timestamp_ms + 1
                    )

                last_timestamp_ms = timestamp_ms

                # En LIVE_STREAM esta llamada no espera
                # a que termine la inferencia.
                landmarker.detect_async(
                    mp_image,
                    timestamp_ms,
                )

                # Obtener el último resultado disponible.
                with result_lock:
                    result_id = latest_result["result_id"]

                    face_detected = (
                        latest_result["face_detected"]
                    )

                    result_received_at = (
                        latest_result["result_received_at"]
                    )

                    left_ear = (
                        latest_result["left_ear"]
                    )

                    right_ear = (
                        latest_result["right_ear"]
                    )

                    average_ear = (
                        latest_result["average_ear"]
                    )

                    landmarks = (
                        latest_result["landmarks"].copy()
                    )

                now = time.monotonic()

                face_present = is_face_present(
                    face_detected,
                    result_received_at,
                    now,
                )

                new_result = result_id != last_result_id
                if new_result:
                    last_result_id = result_id

                # Pausar o reanudar los componentes temporales
                # según la presencia real del rostro.
                if face_present:
                    calibrator.resume()
                    blink_detector.resume()
                else:
                    calibrator.pause()
                    blink_detector.pause()
                    last_eye_state = None

                if face_present and not face_was_present:
                    print(
                        "Rostro detectado. "
                        "Reanudando calibración y detección."
                    )
                elif not face_present and face_was_present:
                    print(
                        "Rostro no detectado. "
                        "Pausando calibración y detección."
                    )

                face_was_present = face_present

                # ============================================================
                # ACTUALIZAR CALIBRACIÓN
                # ============================================================
                eye_state = None

                if face_present and new_result:
                    elapsed = (
                        time.monotonic() - calibration_start
                    )

                    calibrator.update(average_ear)

                    if calibrator.is_completed():
                        reference_ear = calibrator.get_reference_ear()

                        if (
                            eye_classifier.get_reference_ear()
                            is None
                            and reference_ear is not None
                        ):
                            eye_classifier.set_reference_ear(
                                reference_ear,
                            )

                        if eye_classifier.get_reference_ear() is not None:
                            eye_state = eye_classifier.classify(
                                average_ear,
                            )

                            blink_detector.update(eye_state)
                            last_eye_state = eye_state

                            if blink_detector.is_blink():
                                closed_duration = (
                                    blink_detector.get_last_closed_duration()
                                )

                                print(
                                    f"EVENTO | Parpadeo detectado | "
                                    f"Duración cierre: {closed_duration:.3f}s"
                                )

                    print(
                        f"DEBUG | "
                        f"Tiempo: {elapsed:.2f}s | "
                        f"EAR: {average_ear:.3f} | "
                        f"Completada: {calibrator.is_completed()} | "
                        f"Muestras: {calibrator.get_sample_count()} | "
                        f"Ojos: {eye_state} | "
                        f"Parpadeos: {blink_detector.get_blink_count()}"
                    )

                # ============================================================
                # MOSTRAR ESTADO DE CALIBRACIÓN
                # ============================================================

                if not calibrator.is_completed():

                    progress = (
                        calibrator.get_progress()
                        * 100
                    )

                    sample_count = (
                        calibrator.get_sample_count()
                    )

                    current_ear = (
                        calibrator.get_current_ear()
                    )

                    print(
                        f"CALIBRANDO | "
                        f"Progreso: {progress:.0f}% | "
                        f"Muestras: {sample_count} | "
                        f"Pausada: {calibrator.is_paused()} | "
                        f"EAR: {current_ear}"
                    )

                    if face_present:
                        calibration_title = "CALIBRANDO EAR..."
                        calibration_help = (
                            "Ojos abiertos, por favor"
                        )
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
                        f"Muestras: {sample_count}",
                        (20, 260),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2,
                    )

                    if current_ear is not None:
                        cv2.putText(
                            frame,
                            f"EAR actual: {current_ear:.3f}",
                            (20, 290),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (255, 255, 255),
                            2,
                        )
                else:
                    reference_ear = (
                        calibrator.get_reference_ear()
                    )

                    if reference_ear is not None:
                        cv2.putText(
                            frame,
                            f"EAR referencia: "
                            f"{reference_ear:.3f}",
                            (20, 170),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 255, 0),
                            2,
                        )

                        if face_present and last_eye_state is not None:
                            cv2.putText(
                                frame,
                                f"Ojos: {last_eye_state}",
                                (20, 200),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7,
                                (255, 255, 255),
                                2,
                            )

                        if eye_classifier.get_reference_ear() is not None:
                            blink_count = blink_detector.get_blink_count()
                            last_closed_duration = (
                                blink_detector.get_last_closed_duration()
                            )
                            average_closed_duration = (
                                blink_detector.get_average_closed_duration()
                            )
                            blink_rate_per_minute = (
                                blink_detector.get_blink_rate_per_minute()
                            )
                            time_since_last_blink = (
                                blink_detector.get_time_since_last_blink()
                            )
                            metrics_paused = blink_detector.is_paused()

                            metrics_lines = build_metrics_lines(
                                blink_count=blink_count,
                                last_closed_duration=(
                                    last_closed_duration
                                ),
                                average_closed_duration=(
                                    average_closed_duration
                                ),
                                blink_rate_per_minute=(
                                    blink_rate_per_minute
                                ),
                                time_since_last_blink=(
                                    time_since_last_blink
                                ),
                                paused=metrics_paused,
                            )

                            metrics_start_y = 240
                            metrics_line_height = 30

                            for index, text in enumerate(
                                metrics_lines
                            ):
                                is_status_line = (
                                    index
                                    == len(metrics_lines) - 1
                                )

                                if is_status_line:
                                    color = (
                                        (0, 255, 255)
                                        if metrics_paused
                                        else (0, 255, 0)
                                    )
                                else:
                                    color = (255, 255, 255)

                                cv2.putText(
                                    frame,
                                    text,
                                    (
                                        20,
                                        metrics_start_y
                                        + index
                                        * metrics_line_height,
                                    ),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.6,
                                    color,
                                    2,
                                )
                    else:
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

                # ============================================================
                # MOSTRAR ESTADO DEL ROSTRO
                # ============================================================

                if face_present:
                    # Dibujar los landmarks del rostro.
                    for (
                        x_normalized,
                        y_normalized,
                    ) in landmarks:

                        x = int(
                            x_normalized
                            * frame.shape[1]
                        )

                        y = int(
                            y_normalized
                            * frame.shape[0]
                        )

                        cv2.circle(
                            frame,
                            (x, y),
                            1,
                            (0, 255, 0),
                            -1,
                        )

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
                        f"EAR izquierdo: {left_ear:.3f}",
                        (20, 75),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2,
                    )

                    cv2.putText(
                        frame,
                        f"EAR derecho: {right_ear:.3f}",
                        (20, 105),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2,
                    )

                    cv2.putText(
                        frame,
                        f"EAR promedio: {average_ear:.3f}",
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

                cv2.imshow(
                    WINDOW_NAME,
                    frame,
                )

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q") or key == 27:
                    print(
                        "Solicitud de salida recibida."
                    )
                    break

                if cv2.getWindowProperty(
                    WINDOW_NAME,
                    cv2.WND_PROP_VISIBLE,
                ) < 1:
                    print(
                        "Ventana cerrada por el usuario."
                    )
                    break

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Cámara liberada correctamente.")


if __name__ == "__main__":
    main()