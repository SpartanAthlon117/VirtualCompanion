"""
Utilidades para determinar si el rostro debe considerarse presente
a partir del último resultado de MediaPipe.
"""


FACE_LOSS_TIMEOUT_SECONDS = 0.5


def is_face_present(
    face_detected,
    result_received_at,
    now,
    timeout_seconds=FACE_LOSS_TIMEOUT_SECONDS,
):
    """
    Indica si el rostro debe considerarse presente.

    Un rostro se considera presente solo si MediaPipe lo detectó
    y el último resultado es reciente. La ausencia de resultados
    nuevos no se interpreta como ojos cerrados.

    result_received_at y now deben estar en la misma escala
    temporal (por ejemplo, time.monotonic()).
    """

    if timeout_seconds <= 0:
        raise ValueError(
            "timeout_seconds debe ser mayor que cero."
        )

    if not face_detected or result_received_at is None:
        return False

    return (now - result_received_at) <= timeout_seconds
