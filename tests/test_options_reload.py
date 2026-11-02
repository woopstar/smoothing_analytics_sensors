"""Tests for applying saved options."""

from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from custom_components.smoothing_analytics_sensors.const import DOMAIN

OPTIONS = {
    "device_name": "House load",
    "lowpass_time_constant": 5,
    "median_sampling_size": 7,
    "desired_time_to_95": 300,
}


async def test_saving_options_reloads_and_renames(hass: HomeAssistant) -> None:
    """Saving options reloads once and renames the entry and the device."""
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

    result = await hass.config_entries.options.async_init(entry.entry_id)
    reload = hass.config_entries.async_reload
    with patch.object(
        hass.config_entries, "async_reload", side_effect=reload
    ) as mock_reload:
        await hass.config_entries.options.async_configure(result["flow_id"], OPTIONS)
        await hass.async_block_till_done()

    assert mock_reload.call_count == 1
    assert entry.title == "House load"

    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert [device.name for device in devices] == ["House load"]

    lowpass = next(
        state
        for state in hass.states.async_all("sensor")
        if "lowpass_time_constant" in state.attributes
    )
    assert lowpass.attributes["lowpass_time_constant"] == 5
