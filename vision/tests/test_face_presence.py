import pytest

from vision.src.face_presence import (
    FACE_LOSS_TIMEOUT_SECONDS,
    is_face_present,
)


def test_detects_face_with_recent_result():
    assert is_face_present(True, 100.0, 100.0) is True


def test_detects_face_at_timeout_boundary():
    assert (
        is_face_present(
            True,
            100.0,
            100.0 + FACE_LOSS_TIMEOUT_SECONDS,
        )
        is True
    )


def test_rejects_stale_result():
    assert (
        is_face_present(
            True,
            100.0,
            100.0 + FACE_LOSS_TIMEOUT_SECONDS + 0.01,
        )
        is False
    )


def test_rejects_when_face_is_not_detected():
    assert is_face_present(False, 100.0, 100.0) is False


def test_rejects_when_no_result_has_arrived():
    assert is_face_present(True, None, 100.0) is False


@pytest.mark.parametrize("timeout", [0, -1.0])
def test_rejects_invalid_timeout(timeout):
    with pytest.raises(ValueError):
        is_face_present(
            True,
            100.0,
            100.0,
            timeout_seconds=timeout,
        )
