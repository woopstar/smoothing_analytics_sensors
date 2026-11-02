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


def _defaults(schema) -> dict:
    """Map each field of a form schema to its default value."""
    return {str(key): key.default() for key in schema.schema if hasattr(key, "default")}


def _ranges(schema) -> dict:
    """Map each number field of a form schema to its (min, max)."""
    ranges = {}
    for key, value in schema.schema.items():
        config = getattr(value, "config", {})
        if "min" in config:
            ranges[str(key)] = (config["min"], config["max"])
    return ranges


async def test_options_form_shows_current_values(hass: HomeAssistant) -> None:
    """The options form starts from the values chosen at setup, not built-in defaults."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Grid power",
        version=2,
        data={
            "input_sensor": "sensor.grid_power",
            "device_name": "Grid power",
            "lowpass_time_constant": 5,
            "median_sampling_size": 7,
            "desired_time_to_95": 300,
        },
        options={"desired_time_to_95": 240},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert _defaults(result["data_schema"]) == {
        "device_name": "Grid power",
        "lowpass_time_constant": 5,
        "median_sampling_size": 7,
        "desired_time_to_95": 240,
    }

    with patch(
        "custom_components.smoothing_analytics_sensors.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "device_name": "Grid power",
                "lowpass_time_constant": 5.0,
                "median_sampling_size": 9.0,
                "desired_time_to_95": 240.0,
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["median_sampling_size"] == 9
    assert isinstance(entry.options["median_sampling_size"], int)


async def test_config_and_options_flow_use_the_same_ranges(hass: HomeAssistant) -> None:
    """Both flows offer the same limits for every filter parameter."""
    user = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    entry = MockConfigEntry(
        domain=DOMAIN, version=2, data={"input_sensor": "sensor.grid_power"}
    )
    entry.add_to_hass(hass)
    options = await hass.config_entries.options.async_init(entry.entry_id)

    ranges = _ranges(user["data_schema"])
    assert ranges == _ranges(options["data_schema"])
    assert ranges["desired_time_to_95"] == (10, 600)


async def test_user_step_stores_median_window_as_int(hass: HomeAssistant) -> None:
    """The number selector returns floats; the window is stored as an int."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "custom_components.smoothing_analytics_sensors.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"input_sensor": "sensor.grid_power", "median_sampling_size": 15.0},
        )
    assert result["data"]["median_sampling_size"] == 15
    assert isinstance(result["data"]["median_sampling_size"], int)
