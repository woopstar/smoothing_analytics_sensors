"""Tests for the conversion of the pre-2.0.0 EMA window (minor version 2)."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant

from custom_components.smoothing_analytics_sensors import (
    legacy_window_to_time_to_95,
)
from custom_components.smoothing_analytics_sensors.const import DOMAIN

DATA = {
    "input_sensor": "sensor.grid_power",
    "device_name": "Grid power",
    "lowpass_time_constant": 15,
    "median_sampling_size": 15,
}


@pytest.mark.parametrize(
    ("window", "interval", "expected"),
    [
        (300, 1, 449),
        (200, 1, 300),
        (20, 1, 30),
        (20, 10, 299),
        (1, 1, 10),
        (2, 1, 10),
        (3000, 1, 600),
    ],
)
def test_legacy_window_to_time_to_95(
    window: float, interval: float, expected: int
) -> None:
    """The window maps to the time the old alpha needed for 95 %, clamped."""
    assert legacy_window_to_time_to_95(window, interval) == expected


async def setup(hass: HomeAssistant, **kwargs) -> MockConfigEntry:
    """Add a version 2.1 entry and set it up."""
    entry = MockConfigEntry(domain=DOMAIN, version=2, minor_version=1, **kwargs)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_legacy_key_converted_in_data_and_options(hass: HomeAssistant) -> None:
    """Both data and options get the converted value, the old key is gone."""
    entry = await setup(
        hass,
        data={**DATA, "ema_smoothing_window": 300.0},
        options={**DATA, "ema_smoothing_window": 200.0},
    )

    assert entry.minor_version == 2
    assert entry.data["desired_time_to_95"] == 449
    assert entry.options["desired_time_to_95"] == 300
    assert "ema_smoothing_window" not in entry.data
    assert "ema_smoothing_window" not in entry.options


async def test_existing_setting_wins_over_legacy_key(hass: HomeAssistant) -> None:
    """A stored time to 95 % is kept, and options still win over data."""
    entry = await setup(
        hass,
        data={**DATA, "ema_smoothing_window": 300.0, "update_interval": 1.0},
        options={**DATA, "desired_time_to_95": 60.0},
    )

    assert entry.data["desired_time_to_95"] == 449
    assert "ema_smoothing_window" not in entry.data
    assert entry.options["desired_time_to_95"] == 60.0
    ema = next(s for s in entry.runtime_data if s._type == "ema")
    assert ema._desired_time_to_95 == 60.0


async def test_entry_without_legacy_key_unchanged(hass: HomeAssistant) -> None:
    """Entries created since 2.0.0 only get the new minor version."""
    data = {**DATA, "desired_time_to_95": 120}
    entry = await setup(hass, data=data)

    assert entry.minor_version == 2
    assert dict(entry.data) == data
    assert dict(entry.options) == {}


async def test_ema_uses_converted_value(hass: HomeAssistant) -> None:
    """The EMA sensor reads the converted setting after migration."""
    entry = await setup(hass, data={**DATA, "ema_smoothing_window": 300.0})
    ema = next(s for s in entry.runtime_data if s._type == "ema")

    assert ema._desired_time_to_95 == 449
