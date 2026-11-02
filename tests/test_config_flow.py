"""Tests for the config flow."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

from custom_components.smoothing_analytics_sensors.const import DOMAIN


async def test_user_step_creates_entry(hass: HomeAssistant) -> None:
    """Submitting the user step creates an entry titled after the device name."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.smoothing_analytics_sensors.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "input_sensor": "sensor.grid_power",
                "device_name": "Grid power",
                "lowpass_time_constant": 15,
                "median_sampling_size": 15,
                "desired_time_to_95": 120,
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Grid power"
    assert result["data"]["input_sensor"] == "sensor.grid_power"


async def test_user_step_stores_input_registry_id(hass: HomeAssistant) -> None:
    """A registered input sensor is stored with its registry id."""
    registry_entry = er.async_get(hass).async_get_or_create(
        "sensor", "test", "grid", suggested_object_id="grid_power"
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "custom_components.smoothing_analytics_sensors.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"input_sensor": registry_entry.entity_id, "device_name": "Grid power"},
        )
        await hass.async_block_till_done()
    assert result["data"]["input_entity_uuid"] == registry_entry.id
    assert result["result"].version == 2
