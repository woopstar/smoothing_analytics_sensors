"""Unit tests for the pure filter and helper functions."""

import hashlib
from types import SimpleNamespace

import pytest

from custom_components.smoothing_analytics_sensors.custom_sensors.ema_sensor import (
    calculate_alpha,
    ema_filter,
)
from custom_components.smoothing_analytics_sensors.custom_sensors.lowpass_sensor import (
    lowpass_filter,
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


def test_ema_filter_blends_by_alpha() -> None:
    """The EMA output is alpha * x + (1 - alpha) * y."""
    assert ema_filter(10.0, 0.0, 0.25) == pytest.approx(2.5)


def test_ema_constant_input_stays_constant() -> None:
    """A steady input is a fixed point of the filter."""
    assert ema_filter(42.0, 42.0, 0.3) == pytest.approx(42.0)


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
