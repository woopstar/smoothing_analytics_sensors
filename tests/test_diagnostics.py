"""Tests for config entry diagnostics."""

import pytest
from freezegun.api import FrozenDateTimeFactory
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from homeassistant.core import HomeAssistant

from custom_components.smoothing_analytics_sensors.const import DOMAIN
from custom_components.smoothing_analytics_sensors.diagnostics import (
    async_get_config_entry_diagnostics,
)

INPUT_SENSOR = "sensor.grid_power"
DATA = {
    "input_sensor": INPUT_SENSOR,
    "device_name": "Grid power",
    "lowpass_time_constant": 2,
    "median_sampling_size": 3,
    "desired_time_to_95": 20,
}


async def test_diagnostics(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    """Diagnostics show settings, the median window, Δt, alpha and inputs."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Grid power",
        version=2,
        data=DATA,
        options={"desired_time_to_95": 30},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    for value in ("10", "20", "20.0", "30"):
        freezer.tick(5)
        hass.states.async_set(INPUT_SENSOR, value)
        await hass.async_block_till_done()

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["entry"]["data"] == DATA
    assert result["entry"]["options"] == {"desired_time_to_95": 30}
    assert result["entry"]["version"] == 2

    sensors = result["sensors"]
    assert set(sensors) == {"lowpass", "median", "ema"}
    assert sensors["lowpass"]["input_entity_id"] == INPUT_SENSOR
    assert sensors["lowpass"]["update_interval"] == pytest.approx(5)
    assert sensors["median"]["input_entity_id"] == sensors["lowpass"]["entity_id"]
    assert len(sensors["median"]["attributes"]["data_points"]) == 3
    assert sensors["ema"]["input_entity_id"] == sensors["median"]["entity_id"]
    assert 0 < sensors["ema"]["attributes"]["alpha"] <= 1
    assert sensors["ema"]["attributes"]["desired_time_to_95"] == 30
    for sensor in sensors.values():
        assert sensor["available"] is True
        assert sensor["value"] is not None


async def test_diagnostics_download(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Home Assistant finds the platform and serves the download."""
    entry = MockConfigEntry(domain=DOMAIN, title="Grid power", version=2, data=DATA)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await get_diagnostics_for_config_entry(hass, hass_client, entry)
    assert set(result["sensors"]) == {"lowpass", "median", "ema"}
