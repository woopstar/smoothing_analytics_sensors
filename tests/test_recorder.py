"""Tests that fast-changing attributes stay out of the recorder."""

import json
from types import SimpleNamespace

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.recorder.db_schema import StateAttributes
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.smoothing_analytics_sensors.const import DOMAIN
from custom_components.smoothing_analytics_sensors.utils.misc import (
    generate_md5_hash,
)

INPUT_SENSOR = "sensor.grid_power"
SENSOR_HASH = generate_md5_hash(INPUT_SENSOR)
UNRECORDED = {
    "lowpass": {"last_updated", "previous_value", "sensor_update_interval"},
    "median": {
        "data_points",
        "data_points_count",
        "last_updated",
        "missing_data_points",
        "sensor_update_interval",
    },
    "ema": {
        "alpha",
        "last_updated",
        "number_of_updates_needed",
        "previous_value",
        "sensor_update_interval",
    },
}
RECORDED = {
    "lowpass": {"lowpass_time_constant", "type", "unique_id"},
    "median": {"median_sampling_size", "type", "unique_id"},
    "ema": {"desired_time_to_95", "type", "unique_id"},
}


async def test_fast_changing_attributes_are_not_recorded(hass: HomeAssistant) -> None:
    """The recorder keeps parameters but drops per-update attributes."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Grid power",
        data={
            "input_sensor": INPUT_SENSOR,
            "device_name": "Grid power",
            "lowpass_time_constant": 2,
            "median_sampling_size": 1,
            "desired_time_to_95": 20,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    for value in ("10", "20", "30"):
        hass.states.async_set(INPUT_SENSOR, value)
        await hass.async_block_till_done()

    registry = er.async_get(hass)
    for stage, unrecorded in UNRECORDED.items():
        entity_id = registry.async_get_entity_id(
            "sensor", DOMAIN, f"sas_{stage}_{SENSOR_HASH}"
        )
        state = hass.states.get(entity_id)
        assert unrecorded <= set(state.attributes)

        # The same filter the recorder applies before writing attributes
        event = SimpleNamespace(data={"new_state": state})
        recorded = json.loads(
            StateAttributes.shared_attrs_bytes_from_event(event, None)  # type: ignore[arg-type]
        )
        assert not unrecorded & set(recorded)
        assert RECORDED[stage] <= set(recorded)
