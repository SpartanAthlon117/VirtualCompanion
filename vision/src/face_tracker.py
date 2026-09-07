import cv2
import mediapipe as mp


MODEL_PATH = "vision/models/face_landmarker.task"
WINDOW_NAME = "Virtual Companion - Face Tracking"


def create_face_landmarker():
    base_options = mp.tasks.BaseOptions(
        model_asset_path=MODEL_PATH
    )

    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
    )

    return mp.tasks.vision.FaceLandmarker.create_from_options(options)


def main():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: No se pudo abrir la cámara.")
        return

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    try:
        with create_face_landmarker() as landmarker:
            print("Face Landmarker iniciado correctamente.")
            print("Presiona 'q' o ESC para salir.")
            print("También puedes cerrar la ventana con X.")

            frame_timestamp_ms = 0

            while True:
                success, frame = camera.read()

                if not success:
                    print("ERROR: No se pudo obtener un frame de la cámara.")
                    break

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb_frame,
                )

                result = landmarker.detect_for_video(
                    mp_image,
                    frame_timestamp_ms,
                )

                frame_timestamp_ms += 33

                if result.face_landmarks:
                    for face_landmarks in result.face_landmarks:
                        for landmark in face_landmarks:
                            x = int(landmark.x * frame.shape[1])
                            y = int(landmark.y * frame.shape[0])

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

                cv2.imshow(WINDOW_NAME, frame)

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q") or key == 27:
                    print("Solicitud de salida recibida.")
                    break

                if cv2.getWindowProperty(
                    WINDOW_NAME,
                    cv2.WND_PROP_VISIBLE
                ) < 1:
                    print("Ventana cerrada por el usuario.")
                    break

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Cámara liberada correctamente.")


if __name__ == "__main__":
    main()