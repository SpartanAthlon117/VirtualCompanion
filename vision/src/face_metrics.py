import math

def euclidean_distance(point_a, point_b):
    """Calcula la distancia euclidiana entre dos puntos"""

    return math.sqrt(
        (point_a[0] - point_b[0]) ** 2
        + (point_a[1] - point_b[1]) ** 2
    )


def eye_aspect_ratio(eye_points):
    """
    Calcula el Eye Aspect Ratio (EAR).
    
    eye_points debe contener seis puntos:
    [p1, p2, p3, p4, p5, p6]
    """

    if len(eye_points) != 6:
        raise ValueError("EAR requiere exactamente 6 puntos")

    vertical_distance_1 = euclidean_distance(
        eye_points[1],
        eye_points[5],
    )

    vertical_distance_2 = euclidean_distance(
        eye_points[2],
        eye_points[4],
    )

    horizontal_distance = euclidean_distance(
        eye_points[0],
        eye_points[3],
    )

    if horizontal_distance == 0:
        raise ValueError(
            "La distancia horizontal del ojo no puede ser cero."
        )

    return (
        vertical_distance_1 + vertical_distance_2
    ) / (2.0 * horizontal_distance)