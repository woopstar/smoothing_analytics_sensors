"""Tests for setup, reload and listener cleanup."""

from collections import Counter
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant

from custom_components.smoothing_analytics_sensors.const import DOMAIN
from custom_components.smoothing_analytics_sensors.custom_sensors.ema_sensor import (
    EmaSensor,
)
from custom_components.smoothing_analytics_sensors.custom_sensors.lowpass_sensor import (
    LowpassSensor,
)
from custom_components.smoothing_analytics_sensors.custom_sensors.median_sensor import (
    MedianSensor,
)

INPUT_SENSOR = "sensor.grid_power"
SENSOR_CLASSES = (LowpassSensor, MedianSensor, EmaSensor)


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Add a config entry for the input sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Grid power",
        data={
            "input_sensor": INPUT_SENSOR,
            "device_name": "Grid power",
            "lowpass_time_constant": 15,
            "median_sampling_size": 15,
            "desired_time_to_95": 120,
        },
    )
    entry.add_to_hass(hass)
    return entry


async def test_reload_leaves_one_listener_per_entity(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """After a reload each sensor handles an upstream change exactly once."""
    calls: Counter[str] = Counter()

    def counting(cls):
        original = cls._handle_update

        async def wrapper(self, event):
            calls[cls.__name__] += 1
            await original(self, event)

        return wrapper

    hass.states.async_set(INPUT_SENSOR, "10")

    with (
        patch.object(LowpassSensor, "_handle_update", counting(LowpassSensor)),
        patch.object(MedianSensor, "_handle_update", counting(MedianSensor)),
        patch.object(EmaSensor, "_handle_update", counting(EmaSensor)),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert await hass.config_entries.async_reload(config_entry.entry_id)
        await hass.async_block_till_done()

        calls.clear()
        hass.states.async_set(INPUT_SENSOR, "20")
        await hass.async_block_till_done()

    assert calls == {cls.__name__: 1 for cls in SENSOR_CLASSES}
    assert "is not added" not in caplog.text


async def test_unload_removes_listeners(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """After unload no sensor reacts to upstream changes."""
    calls: Counter[str] = Counter()

    async def record(self, event):
        calls[type(self).__name__] += 1

    hass.states.async_set(INPUT_SENSOR, "10")

    with (
        patch.object(LowpassSensor, "_handle_update", record),
        patch.object(MedianSensor, "_handle_update", record),
        patch.object(EmaSensor, "_handle_update", record),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()

        calls.clear()
        hass.states.async_set(INPUT_SENSOR, "20")
        await hass.async_block_till_done()

    assert not calls
