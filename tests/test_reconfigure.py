"""Tests for the reconfigure step that swaps the input sensor."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

from custom_components.smoothing_analytics_sensors.const import DOMAIN

OLD_INPUT = "sensor.grid_power"
NEW_INPUT = "sensor.house_load"
STAGES = ("lowpass", "median", "ema")


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Add a loaded-ready entry for the old input."""
    hass.states.async_set(OLD_INPUT, "10")
    hass.states.async_set(NEW_INPUT, "500")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Grid power",
        version=2,
        unique_id=OLD_INPUT,
        data={
            "input_sensor": OLD_INPUT,
            "device_name": "Grid power",
            "lowpass_time_constant": 2,
            "median_sampling_size": 1,
            "desired_time_to_95": 20,
        },
    )
    entry.add_to_hass(hass)
    return entry


def sas_entities(hass: HomeAssistant, entry: MockConfigEntry) -> dict[str, str]:
    """Map unique_id to entity_id for the entry's SAS entities."""
    return {
        e.unique_id: e.entity_id
        for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    }


async def reconfigure(hass: HomeAssistant, entry: MockConfigEntry, input_sensor: str):
    """Run the reconfigure step with a new input sensor."""
    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"input_sensor": input_sensor}
    )
    await hass.async_block_till_done()
    return result


async def test_reconfigure_swaps_input_and_keeps_entities(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """A new input keeps entity IDs and unique IDs, and the stack follows it."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    before = sas_entities(hass, config_entry)

    result = await reconfigure(hass, config_entry, NEW_INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    assert sas_entities(hass, config_entry) == before
    assert config_entry.data["input_sensor"] == NEW_INPUT
    assert config_entry.data["hash_source"] == OLD_INPUT
    assert config_entry.unique_id == NEW_INPUT

    hass.states.async_set(NEW_INPUT, "600")
    await hass.async_block_till_done()
    lowpass_id = next(
        eid for uid, eid in before.items() if uid.startswith("sas_lowpass")
    )
    lowpass = hass.states.get(lowpass_id)
    assert lowpass.attributes["input_sensor"] == NEW_INPUT
    assert float(lowpass.state) > 10

    # The old input no longer drives the filter
    value = lowpass.state
    hass.states.async_set(OLD_INPUT, "-1000")
    await hass.async_block_till_done()
    assert hass.states.get(lowpass_id).state == value


async def test_reconfigure_twice_keeps_first_hash(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """A second reconfigure keeps the unique IDs from the very first input."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    before = sas_entities(hass, config_entry)

    await reconfigure(hass, config_entry, NEW_INPUT)
    hass.states.async_set("sensor.third", "1")
    await reconfigure(hass, config_entry, "sensor.third")

    assert config_entry.data["hash_source"] == OLD_INPUT
    assert sas_entities(hass, config_entry) == before


async def test_reconfigure_to_input_of_other_entry_aborts(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """The new input must not already have its own entry."""
    MockConfigEntry(
        domain=DOMAIN, version=2, unique_id=NEW_INPUT, data={"input_sensor": NEW_INPUT}
    ).add_to_hass(hass)
    result = await reconfigure(hass, config_entry, NEW_INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert config_entry.data["input_sensor"] == OLD_INPUT


async def test_reconfigure_rejects_non_numeric_input(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """A text sensor shows invalid_sensor and changes nothing."""
    hass.states.async_set("sensor.mode", "eco")
    result = await reconfigure(hass, config_entry, "sensor.mode")
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"input_sensor": "invalid_sensor"}
    assert config_entry.data["input_sensor"] == OLD_INPUT


async def test_reconfigure_form_defaults_to_current_input(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """The form starts with the current input sensor."""
    result = await config_entry.start_reconfigure_flow(hass)
    key = next(iter(result["data_schema"].schema))
    assert key.default() == OLD_INPUT
