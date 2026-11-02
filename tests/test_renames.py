"""Tests for renamed input and stage entities, and the v1 → v2 migration."""

import math

import pytest
from freezegun.api import FrozenDateTimeFactory
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.smoothing_analytics_sensors.const import DOMAIN
from custom_components.smoothing_analytics_sensors.utils.misc import (
    generate_md5_hash,
)

INPUT_SENSOR = "sensor.grid_power"
RENAMED_INPUT = "sensor.house_power"
SENSOR_HASH = generate_md5_hash(INPUT_SENSOR)
STAGES = ("lowpass", "median", "ema")
DATA = {
    "input_sensor": INPUT_SENSOR,
    "device_name": "Grid power",
    # A 1 s step gives the new value weight 1/2
    "lowpass_time_constant": 1 / math.log(2),
    "median_sampling_size": 1,
    "desired_time_to_95": 20,
}


@pytest.fixture
def input_registry_entry(hass: HomeAssistant) -> er.RegistryEntry:
    """Register the input sensor, as a real integration would."""
    return er.async_get(hass).async_get_or_create(
        "sensor", "test", "grid", suggested_object_id="grid_power"
    )


@pytest.fixture
def config_entry(
    hass: HomeAssistant, input_registry_entry: er.RegistryEntry
) -> MockConfigEntry:
    """Add a version 1 entry, as created by releases before the migration."""
    entry = MockConfigEntry(domain=DOMAIN, title="Grid power", version=1, data=DATA)
    entry.add_to_hass(hass)
    return entry


def stage_ids(hass: HomeAssistant) -> dict[str, str]:
    """Map each stage to its current entity_id."""
    registry = er.async_get(hass)
    return {
        stage: registry.async_get_entity_id(  # type: ignore[misc]
            "sensor", DOMAIN, f"sas_{stage}_{SENSOR_HASH}"
        )
        for stage in STAGES
    }


async def push(hass: HomeAssistant, entity_id: str, value: str) -> None:
    """Set an input state and let the chain settle."""
    hass.states.async_set(entity_id, value)
    await hass.async_block_till_done()


async def test_migration_stores_input_registry_id(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    input_registry_entry: er.RegistryEntry,
) -> None:
    """A version 1 entry gets the input's registry id and keeps its unique IDs."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.version == 2
    assert config_entry.data["input_entity_uuid"] == input_registry_entry.id
    assert config_entry.data["input_sensor"] == INPUT_SENSOR
    assert all(stage_ids(hass).values())


async def test_migration_without_registry_entry(hass: HomeAssistant) -> None:
    """An input without a registry entry migrates without a registry id."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data={**DATA, "input_sensor": "sensor.no_registry"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.version == 2
    assert "input_entity_uuid" not in entry.data


async def test_future_version_is_not_loaded(hass: HomeAssistant) -> None:
    """An entry from a newer release is refused, not misread."""
    entry = MockConfigEntry(domain=DOMAIN, version=3, data=DATA)
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)


async def test_input_rename_while_running(
    hass: HomeAssistant, config_entry: MockConfigEntry, freezer: FrozenDateTimeFactory
) -> None:
    """The lowpass follows a renamed input without a reload."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    await push(hass, INPUT_SENSOR, "10")

    er.async_get(hass).async_update_entity(INPUT_SENSOR, new_entity_id=RENAMED_INPUT)
    await hass.async_block_till_done()
    freezer.tick(1)
    await push(hass, RENAMED_INPUT, "20")

    lowpass = hass.states.get(stage_ids(hass)["lowpass"])
    assert float(lowpass.state) == pytest.approx(15.0)
    assert lowpass.attributes["input_sensor"] == RENAMED_INPUT


async def test_input_rename_survives_restart(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """After a rename and a reload the entry uses the new input entity_id."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    ids_before = stage_ids(hass)

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    er.async_get(hass).async_update_entity(INPUT_SENSOR, new_entity_id=RENAMED_INPUT)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert stage_ids(hass) == ids_before
    await push(hass, RENAMED_INPUT, "10")
    lowpass = hass.states.get(ids_before["lowpass"])
    assert lowpass.state == "10.0"
    assert lowpass.attributes["input_sensor"] == RENAMED_INPUT


@pytest.mark.parametrize("renamed_stage", ["lowpass", "median"])
async def test_stage_rename_keeps_stack_working(
    hass: HomeAssistant, config_entry: MockConfigEntry, renamed_stage: str
) -> None:
    """Renaming a SAS stage keeps the next stage updating."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    await push(hass, INPUT_SENSOR, "10")

    new_entity_id = f"sensor.renamed_{renamed_stage}"
    er.async_get(hass).async_update_entity(
        stage_ids(hass)[renamed_stage], new_entity_id=new_entity_id
    )
    await hass.async_block_till_done()
    await push(hass, INPUT_SENSOR, "20")

    ids = stage_ids(hass)
    assert ids[renamed_stage] == new_entity_id
    # Both downstream stages moved up from 10 after the rename
    assert float(hass.states.get(ids["median"]).state) > 10
    assert float(hass.states.get(ids["ema"]).state) > 10
