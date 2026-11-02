"""Tests for the config flow."""

from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

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


async def _submit(hass: HomeAssistant, input_sensor: str):
    """Run the user step for an input sensor without setting the entry up."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "custom_components.smoothing_analytics_sensors.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"input_sensor": input_sensor, "device_name": "Grid"}
        )
        await hass.async_block_till_done()
    return result


async def test_same_input_twice_aborts(hass: HomeAssistant) -> None:
    """A second entry for the same input sensor is refused."""
    assert (await _submit(hass, "sensor.grid_power"))[
        "type"
    ] is FlowResultType.CREATE_ENTRY
    result = await _submit(hass, "sensor.grid_power")
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_renamed_input_is_still_a_duplicate(hass: HomeAssistant) -> None:
    """The registry id recognizes an input that was renamed after setup."""
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "sensor", "test", "grid", suggested_object_id="grid_power"
    )
    assert (await _submit(hass, "sensor.grid_power"))[
        "type"
    ] is FlowResultType.CREATE_ENTRY
    registry.async_update_entity(
        "sensor.grid_power", new_entity_id="sensor.house_power"
    )

    result = await _submit(hass, "sensor.house_power")
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_entry_without_unique_id_blocks_duplicate(hass: HomeAssistant) -> None:
    """Entries created before the check are matched on their input sensor."""
    MockConfigEntry(
        domain=DOMAIN, version=2, data={"input_sensor": "sensor.grid_power"}
    ).add_to_hass(hass)
    result = await _submit(hass, "sensor.grid_power")
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_other_input_is_allowed(hass: HomeAssistant) -> None:
    """Different input sensors each get their own entry."""
    assert (await _submit(hass, "sensor.grid_power"))[
        "type"
    ] is FlowResultType.CREATE_ENTRY
    assert (await _submit(hass, "sensor.house_load"))[
        "type"
    ] is FlowResultType.CREATE_ENTRY
