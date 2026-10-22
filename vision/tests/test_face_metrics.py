import pytest

from vision.src.face_metrics import (
    euclidean_distance,
    eye_aspect_ratio,
)


def test_euclidean_distance_known_triangle():
    assert euclidean_distance(
        (0.0, 0.0),
        (3.0, 4.0),
    ) == pytest.approx(5.0)

    assert euclidean_distance(
        (2.0, 2.0),
        (2.0, 2.0),
    ) == 0.0


def test_calculates_eye_aspect_ratio():
    eye_points = [
        (0.0, 0.0),
        (2.0, 3.0),
        (6.0, 3.0),
        (10.0, 0.0),
        (6.0, -3.0),
        (2.0, -3.0),
    ]

    assert eye_aspect_ratio(eye_points) == pytest.approx(0.6)


def test_uses_both_vertical_distances():
    eye_points = [
        (0.0, 0.0),
        (2.0, 3.0),
        (6.0, 2.0),
        (10.0, 0.0),
        (6.0, 0.0),
        (2.0, -3.0),
    ]

    assert eye_aspect_ratio(eye_points) == pytest.approx(0.4)


def test_closed_eye_has_zero_ear():
    eye_points = [
        (-5.0, 0.0),
        (0.0, 0.0),
        (0.0, 0.0),
        (5.0, 0.0),
        (0.0, 0.0),
        (0.0, 0.0),
    ]

    assert eye_aspect_ratio(eye_points) == pytest.approx(0.0)


def test_ear_is_scale_invariant():
    eye_points = [
        (0.0, 0.0),
        (2.0, 3.0),
        (6.0, 3.0),
        (10.0, 0.0),
        (6.0, -3.0),
        (2.0, -3.0),
    ]
    scaled_points = [
        (x * 2.5, y * 2.5)
        for x, y in eye_points
    ]

    assert eye_aspect_ratio(scaled_points) == pytest.approx(
        eye_aspect_ratio(eye_points)
    )


@pytest.mark.parametrize(
    "eye_points",
    [
        [],
        [(0.0, 0.0)] * 5,
        [(0.0, 0.0)] * 7,
    ],
)
def test_rejects_wrong_number_of_points(eye_points):
    with pytest.raises(ValueError):
        eye_aspect_ratio(eye_points)


def test_rejects_zero_horizontal_distance():
    eye_points = [
        (0.0, 0.0),
        (0.0, 1.0),
        (0.0, 1.0),
        (0.0, 0.0),
        (0.0, -1.0),
        (0.0, -1.0),
    ]

    with pytest.raises(ValueError):
        eye_aspect_ratio(eye_points)
