import pytest

from vision.src.eye_state import EyeStateClassifier


def test_initial_state():
    classifier = EyeStateClassifier()

    assert classifier.threshold_factor == pytest.approx(0.70)
    assert classifier.get_reference_ear() is None
    assert classifier.get_threshold() is None


@pytest.mark.parametrize("factor", [0.0, 1.0, -0.1, 1.1])
def test_rejects_invalid_threshold_factor(factor):
    with pytest.raises(ValueError):
        EyeStateClassifier(threshold_factor=factor)


def test_sets_reference_and_threshold():
    classifier = EyeStateClassifier()
    classifier.set_reference_ear(0.30)

    assert classifier.get_reference_ear() == pytest.approx(0.30)
    assert classifier.get_threshold() == pytest.approx(0.21)


def test_custom_threshold_factor():
    classifier = EyeStateClassifier(threshold_factor=0.5)
    classifier.set_reference_ear(0.40)

    assert classifier.threshold_factor == pytest.approx(0.5)
    assert classifier.get_threshold() == pytest.approx(0.20)


@pytest.mark.parametrize("reference", [None, 0.0, -0.1])
def test_rejects_invalid_reference(reference):
    classifier = EyeStateClassifier()

    with pytest.raises(ValueError):
        classifier.set_reference_ear(reference)


def test_classify_requires_reference():
    classifier = EyeStateClassifier()

    with pytest.raises(RuntimeError):
        classifier.classify(0.30)


def test_classify_rejects_none():
    classifier = EyeStateClassifier()
    classifier.set_reference_ear(0.30)

    with pytest.raises(ValueError):
        classifier.classify(None)


def test_classifies_around_threshold():
    classifier = EyeStateClassifier()
    classifier.set_reference_ear(0.30)
    threshold = classifier.get_threshold()

    assert (
        classifier.classify(threshold - 0.01)
        == EyeStateClassifier.CLOSED
    )
    assert classifier.classify(threshold) == EyeStateClassifier.OPEN
    assert (
        classifier.classify(threshold + 0.01)
        == EyeStateClassifier.OPEN
    )


def test_updates_threshold_with_new_reference():
    classifier = EyeStateClassifier()
    classifier.set_reference_ear(0.30)
    classifier.set_reference_ear(0.40)

    assert classifier.get_reference_ear() == pytest.approx(0.40)
    assert classifier.get_threshold() == pytest.approx(0.28)
