import cv2
import mediapipe as mp
import threading
import time

from face_metrics import eye_aspect_ratio
from ear_calibrator import EARCalibrator
# Incorporación de la clase EyeStateClassifier
# para el control de los ojos.
from eye_state import EyeStateClassifier


MODEL_PATH = "vision/models/face_landmarker.task"
WINDOW_NAME = "Virtual Companion - Face Tracking"

# Landmarks de los ojos utilizados para calcular EAR.
LEFT_EYE_POINTS = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_POINTS = [362, 385, 387, 263, 373, 380]


def create_face_landmarker(result_callback):
    base_options = mp.tasks.BaseOptions(
        model_asset_path=MODEL_PATH
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

    def on_face_landmarker_result(
        result,
        output_image,
        timestamp_ms,
    ):
        del output_image
        del timestamp_ms

        face_detected = False
        left_ear = 0.0
        right_ear = 0.0
        average_ear = 0.0
        landmarks = []

        if result.face_landmarks:
            face_detected = True

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

        # Actualizar el último resultado disponible.
        with result_lock:
            latest_result["face_detected"] = face_detected
            latest_result["left_ear"] = left_ear
            latest_result["right_ear"] = right_ear
            latest_result["average_ear"] = average_ear
            latest_result["landmarks"] = landmarks

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
                    face_detected = (
                        latest_result["face_detected"]
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

                # ============================================================
                # ACTUALIZAR CALIBRACIÓN
                # ============================================================
                if face_detected:
                    elapsed = (
                        time.monotonic() - calibration_start
                    )

                    calibrator.update(average_ear)

                    eye_state = None

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

                    print(
                        f"DEBUG | "
                        f"Tiempo: {elapsed:.2f}s | "
                        f"EAR: {average_ear:.3f} | "
                        f"Completada: {calibrator.is_completed()} | "
                        f"Muestras: {calibrator.get_sample_count()} | "
                        f"Ojos: {eye_state}"
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
                        f"EAR: {current_ear}"
                    )

                    cv2.putText(
                        frame,
                        "CALIBRANDO EAR...",
                        (20, 170),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 255),
                        2,
                    )

                    cv2.putText(
                        frame,
                        "Mantén los ojos abiertos por favor",
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

                        if eye_state is not None:
                            cv2.putText(
                                frame,
                                f"Ojos: {eye_state}",
                                (20, 165),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (255, 255, 255),
                                2,
                            )

                # ============================================================
                # MOSTRAR ESTADO DEL ROSTRO
                # ============================================================

                if face_detected:
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