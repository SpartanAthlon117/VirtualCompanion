import pytest

from vision.src.perclos import PerclosCalculator


@pytest.fixture
def clock():
    """Proporciona un reloj monotónico controlable."""

    current_time = [100.0]

    def now():
        return current_time[0]

    def advance(seconds):
        current_time[0] += seconds

    return now, advance


def make_calculator(
    clock_now,
    window_seconds=10.0,
    minimum_observation_seconds=0.0,
):
    return PerclosCalculator(
        window_seconds=window_seconds,
        minimum_observation_seconds=(
            minimum_observation_seconds
        ),
        clock=clock_now,
    )


def test_initial_state(clock):
    clock_now, _ = clock
    calculator = make_calculator(clock_now)

    assert calculator.get_perclos() is None
    assert calculator.get_observation_duration() == 0.0
    assert calculator.is_paused() is False
    assert calculator.get_window_seconds() == 10.0
    assert calculator.get_minimum_observation_seconds() == 0.0


def test_rejects_invalid_window(clock):
    clock_now, _ = clock

    with pytest.raises(ValueError):
        make_calculator(clock_now, window_seconds=0.0)

    with pytest.raises(ValueError):
        make_calculator(clock_now, window_seconds=-1.0)


def test_rejects_negative_minimum_observation(clock):
    clock_now, _ = clock

    with pytest.raises(ValueError):
        make_calculator(
            clock_now,
            minimum_observation_seconds=-0.1,
        )


def test_allows_minimum_greater_than_window(clock):
    clock_now, _ = clock
    calculator = make_calculator(
        clock_now,
        window_seconds=10.0,
        minimum_observation_seconds=20.0,
    )

    assert calculator.get_minimum_observation_seconds() == 20.0


def test_rejects_non_callable_clock():
    with pytest.raises(TypeError):
        PerclosCalculator(clock=10.0)


def test_rejects_invalid_eye_state(clock):
    clock_now, _ = clock
    calculator = make_calculator(clock_now)

    with pytest.raises(ValueError):
        calculator.update("INVALID")


def test_returns_none_before_minimum_observation(clock):
    clock_now, advance = clock
    calculator = make_calculator(
        clock_now,
        minimum_observation_seconds=5.0,
    )

    assert calculator.update(PerclosCalculator.OPEN) is None

    advance(4.0)
    assert calculator.update(PerclosCalculator.OPEN) is None

    advance(1.0)
    assert calculator.update(PerclosCalculator.OPEN) == 0.0


def test_all_open_returns_zero(clock):
    clock_now, advance = clock
    calculator = make_calculator(clock_now)

    calculator.update(PerclosCalculator.OPEN)
    advance(5.0)

    assert (
        calculator.update(PerclosCalculator.OPEN)
        == pytest.approx(0.0)
    )


def test_all_closed_returns_one(clock):
    clock_now, advance = clock
    calculator = make_calculator(clock_now)

    calculator.update(PerclosCalculator.CLOSED)
    advance(5.0)

    assert (
        calculator.update(PerclosCalculator.CLOSED)
        == pytest.approx(1.0)
    )


def test_half_closed_returns_half(clock):
    clock_now, advance = clock
    calculator = make_calculator(clock_now)

    calculator.update(PerclosCalculator.CLOSED)
    advance(5.0)
    calculator.update(PerclosCalculator.OPEN)
    advance(5.0)

    assert (
        calculator.update(PerclosCalculator.OPEN)
        == pytest.approx(0.5)
    )


def test_rolling_window_discards_old_closed_time(clock):
    clock_now, advance = clock
    calculator = make_calculator(clock_now)

    calculator.update(PerclosCalculator.CLOSED)
    advance(10.0)
    calculator.update(PerclosCalculator.OPEN)
    advance(10.0)

    assert (
        calculator.update(PerclosCalculator.OPEN)
        == pytest.approx(0.0)
    )


def test_counts_partial_closed_interval_inside_window(clock):
    clock_now, advance = clock
    calculator = make_calculator(clock_now)

    calculator.update(PerclosCalculator.CLOSED)
    advance(15.0)
    calculator.update(PerclosCalculator.OPEN)
    advance(5.0)

    assert (
        calculator.update(PerclosCalculator.OPEN)
        == pytest.approx(0.5)
    )


def test_pause_excludes_time_from_denominator(clock):
    clock_now, advance = clock
    calculator = make_calculator(clock_now, window_seconds=60.0)

    calculator.update(PerclosCalculator.CLOSED)
    advance(1.0)
    calculator.pause()
    advance(10.0)
    calculator.resume()

    calculator.update(PerclosCalculator.OPEN)
    advance(1.0)

    assert (
        calculator.update(PerclosCalculator.OPEN)
        == pytest.approx(0.5)
    )
    assert (
        calculator.get_observation_duration()
        == pytest.approx(2.0)
    )


def test_update_while_paused_returns_frozen_value(clock):
    clock_now, advance = clock
    calculator = make_calculator(clock_now)

    calculator.update(PerclosCalculator.CLOSED)
    advance(2.0)
    assert (
        calculator.update(PerclosCalculator.CLOSED)
        == pytest.approx(1.0)
    )

    calculator.pause()
    advance(5.0)

    assert (
        calculator.update(PerclosCalculator.OPEN)
        == pytest.approx(1.0)
    )
    assert (
        calculator.get_observation_duration()
        == pytest.approx(2.0)
    )

    calculator.resume()
    calculator.update(PerclosCalculator.OPEN)
    advance(1.0)
    calculator.update(PerclosCalculator.OPEN)

    assert (
        calculator.get_perclos()
        == pytest.approx(2.0 / 3.0)
    )


def test_pause_before_first_update_does_not_start_observation(clock):
    clock_now, advance = clock
    calculator = make_calculator(clock_now)

    calculator.pause()
    advance(5.0)
    calculator.resume()

    assert calculator.get_perclos() is None
    assert calculator.get_observation_duration() == 0.0

    calculator.update(PerclosCalculator.CLOSED)
    advance(5.0)

    assert (
        calculator.update(PerclosCalculator.CLOSED)
        == pytest.approx(1.0)
    )


def test_pause_and_resume_are_idempotent(clock):
    clock_now, advance = clock
    calculator = make_calculator(clock_now, window_seconds=60.0)

    calculator.update(PerclosCalculator.OPEN)
    advance(1.0)

    calculator.pause()
    calculator.pause()
    advance(10.0)
    calculator.resume()
    calculator.resume()

    advance(1.0)
    calculator.update(PerclosCalculator.OPEN)

    assert (
        calculator.get_observation_duration()
        == pytest.approx(2.0)
    )


def test_reset_clears_state(clock):
    clock_now, advance = clock
    calculator = make_calculator(clock_now)

    calculator.update(PerclosCalculator.CLOSED)
    advance(5.0)
    calculator.update(PerclosCalculator.CLOSED)

    calculator.reset()

    assert calculator.get_perclos() is None
    assert calculator.get_observation_duration() == 0.0
    assert calculator.is_paused() is False

    calculator.update(PerclosCalculator.OPEN)
    advance(5.0)

    assert (
        calculator.update(PerclosCalculator.OPEN)
        == pytest.approx(0.0)
    )


def test_minimum_observation_greater_than_window(clock):
    clock_now, advance = clock
    calculator = make_calculator(
        clock_now,
        window_seconds=10.0,
        minimum_observation_seconds=20.0,
    )

    calculator.update(PerclosCalculator.OPEN)
    advance(19.0)

    assert calculator.update(PerclosCalculator.OPEN) is None

    advance(1.0)

    assert (
        calculator.update(PerclosCalculator.OPEN)
        == pytest.approx(0.0)
    )
