"""Tests for the config flow."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

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
