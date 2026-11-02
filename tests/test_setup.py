"""Tests for config entry setup and unload."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.smoothing_analytics_sensors import sensor
from custom_components.smoothing_analytics_sensors.const import DOMAIN


async def test_setup_and_unload_entry(hass: HomeAssistant) -> None:
    """An entry sets up three sensors and unloads cleanly."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Grid power",
        data={
            "input_sensor": "sensor.grid_power",
            "device_name": "Grid power",
            "lowpass_time_constant": 15,
            "median_sampling_size": 15,
            "desired_time_to_95": 120,
        },
    )
    entry.add_to_hass(hass)
    hass.states.async_set("sensor.grid_power", "10")

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert len(hass.states.async_entity_ids("sensor")) == 4

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert DOMAIN not in hass.data
    assert not hasattr(sensor, "async_unload_entry")


async def test_setup_gives_old_entry_a_unique_id(hass: HomeAssistant) -> None:
    """An entry from before the duplicate check gets its unique_id at setup."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=2, data={"input_sensor": "sensor.grid_power"}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.unique_id == "sensor.grid_power"


async def test_setup_skips_unique_id_already_in_use(hass: HomeAssistant) -> None:
    """Of two old duplicate entries only the first gets the unique_id."""
    first = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id="sensor.grid_power",
        data={"input_sensor": "sensor.grid_power"},
    )
    second = MockConfigEntry(
        domain=DOMAIN, version=2, data={"input_sensor": "sensor.grid_power"}
    )
    first.add_to_hass(hass)
    second.add_to_hass(hass)
    await hass.config_entries.async_setup(second.entry_id)
    await hass.async_block_till_done()
    assert second.unique_id is None
