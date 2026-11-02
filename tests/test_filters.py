"""Unit tests for the pure filter and helper functions."""

import hashlib
from types import SimpleNamespace

import pytest

from custom_components.smoothing_analytics_sensors.filters import (
    calculate_alpha,
    ema_filter,
    lowpass_filter,
    median_filter,
)
from custom_components.smoothing_analytics_sensors.utils.misc import (
    generate_md5_hash,
    get_config_value,
)


def test_lowpass_time_constant_one_passes_input_through() -> None:
    """A time constant of 1 gives the new value full weight."""
    assert lowpass_filter(10.0, 0.0, 1) == pytest.approx(10.0)


def test_lowpass_weights_new_value_by_inverse_time_constant() -> None:
    """The newest value gets weight 1 / time_constant."""
    assert lowpass_filter(15.0, 0.0, 15) == pytest.approx(1.0)


@pytest.mark.parametrize(("time_constant", "updates"), [(5, 14), (15, 44), (60, 179)])
def test_lowpass_step_response_matches_docs(time_constant: int, updates: int) -> None:
    """Updates to reach 95 % of a unit step match docs/filter-math.md."""
    value = 0.0
    count = 0
    while value < 0.95:
        value = lowpass_filter(1.0, value, time_constant)
        count += 1
    assert count == updates


def test_lowpass_constant_input_stays_constant() -> None:
    """A steady input is a fixed point of the filter."""
    assert lowpass_filter(-3.5, -3.5, 15) == pytest.approx(-3.5)


def test_ema_alpha_span_formula() -> None:
    """Alpha follows 2 / (N + 1) with N = time_to_95 / dt."""
    assert calculate_alpha(120, 1) == pytest.approx(2 / 121)
    assert calculate_alpha(120, 30) == pytest.approx(0.4)


@pytest.mark.parametrize("dt", [1, 60, 120, 1200, 3600, 86400])
@pytest.mark.parametrize("time_to_95", [10, 120, 600])
def test_ema_alpha_stays_in_unit_interval(time_to_95: int, dt: int) -> None:
    """Alpha is in (0, 1] for every positive dt, also after long gaps."""
    assert 0 < calculate_alpha(time_to_95, dt) <= 1


@pytest.mark.parametrize("dt", [0, -5])
def test_ema_alpha_without_elapsed_time_keeps_previous_output(dt: int) -> None:
    """dt <= 0 means no time passed, so the output does not move."""
    alpha = calculate_alpha(120, dt)
    assert alpha == 0
    assert ema_filter(200.0, 1000.0, alpha) == pytest.approx(1000.0)


@pytest.mark.parametrize(("dt", "expected"), [(120, 1.0), (1200, 1.0)])
def test_ema_alpha_clamps_at_one_from_time_to_95(dt: int, expected: float) -> None:
    """From dt = time_to_95 on, alpha is 1: the output jumps to the input."""
    assert calculate_alpha(120, dt) == pytest.approx(expected)


def test_ema_long_gap_lands_between_previous_output_and_input() -> None:
    """After a 1 h gap the EMA does not overshoot past the input."""
    output = ema_filter(200.0, 1000.0, calculate_alpha(120, 3600))
    assert 200.0 <= output <= 1000.0


def test_ema_filter_blends_by_alpha() -> None:
    """The EMA output is alpha * x + (1 - alpha) * y."""
    assert ema_filter(10.0, 0.0, 0.25) == pytest.approx(2.5)


def test_ema_constant_input_stays_constant() -> None:
    """A steady input is a fixed point of the filter."""
    assert ema_filter(42.0, 42.0, 0.3) == pytest.approx(42.0)


def test_median_is_none_until_window_full() -> None:
    """The median stays None until sampling_size values are collected."""
    median, window = median_filter([], 5.0, 3)
    assert median is None
    assert window == [5.0]
    median, window = median_filter([5.0, 1.0], 3.0, 3)
    assert median == pytest.approx(3.0)
    assert window == [5.0, 1.0, 3.0]


def test_median_window_keeps_last_values() -> None:
    """The returned window holds the last sampling_size values."""
    _, window = median_filter([1.0, 2.0, 3.0], 4.0, 3)
    assert window == [2.0, 3.0, 4.0]


def test_median_filter_does_not_mutate_input() -> None:
    """The caller's window list is left unchanged."""
    window = [1.0, 2.0]
    median_filter(window, 3.0, 2)
    assert window == [1.0, 2.0]


def test_md5_hash_of_entity_id() -> None:
    """The sensor hash is the MD5 hex digest of the input entity_id."""
    expected = hashlib.md5(b"sensor.grid_power").hexdigest()
    assert generate_md5_hash("sensor.grid_power") == expected


def test_config_value_prefers_options_then_data_then_default() -> None:
    """Options override data, data overrides the default."""
    entry = SimpleNamespace(options={"a": 1}, data={"a": 2, "b": 3})
    assert get_config_value(entry, "a", 9) == 1
    assert get_config_value(entry, "b", 9) == 3
    assert get_config_value(entry, "c", 9) == 9
