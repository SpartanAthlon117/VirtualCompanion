import cv2


def main():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: No se pudo abrir la cámara.")
        return

    print("Cámara iniciada correctamente.")
    print("Presiona 'q' para salir.")

    while True:
        success, frame = camera.read()

        if not success:
            print("ERROR: No se pudo obtener un frame de la cámara.")
            break

        cv2.imshow("Virtual Companion - Camera", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()
    print("Cámara liberada correctamente.")


if __name__ == "__main__":
    main()