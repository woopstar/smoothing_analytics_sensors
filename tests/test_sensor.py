"""Integration tests for the lowpass → median → EMA sensor chain."""

from datetime import datetime

import pytest
from freezegun.api import FrozenDateTimeFactory
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache,
)

from homeassistant.components.sensor import (
    DATA_COMPONENT as SENSOR_COMPONENT,
    SensorEntity,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.smoothing_analytics_sensors.const import DOMAIN, ICON
from custom_components.smoothing_analytics_sensors.utils.misc import (
    generate_md5_hash,
)

INPUT_SENSOR = "sensor.grid_power"
SENSOR_HASH = generate_md5_hash(INPUT_SENSOR)
STAGES = ("lowpass", "median", "ema")
POWER = {"unit_of_measurement": "W", "device_class": "power"}


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Add an entry with short windows so the chain fills quickly."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Grid power",
        data={
            "input_sensor": INPUT_SENSOR,
            "device_name": "Grid power",
            "lowpass_time_constant": 2,
            "median_sampling_size": 3,
            "desired_time_to_95": 20,
        },
    )
    entry.add_to_hass(hass)
    return entry


def entity_ids(hass: HomeAssistant) -> dict[str, str]:
    """Map each stage to its entity_id through the entity registry."""
    registry = er.async_get(hass)
    ids = {
        stage: registry.async_get_entity_id(
            "sensor", DOMAIN, f"sas_{stage}_{SENSOR_HASH}"
        )
        for stage in STAGES
    }
    assert all(ids.values())
    return ids  # type: ignore[return-value]


async def setup_entry(hass: HomeAssistant, entry: MockConfigEntry) -> dict[str, str]:
    """Set up the entry and return the stage entity_ids."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entity_ids(hass)


async def push(hass: HomeAssistant, value: str) -> None:
    """Set the input sensor and let the chain settle."""
    hass.states.async_set(INPUT_SENSOR, value, POWER)
    await hass.async_block_till_done()


async def test_entities_and_device(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """One device with three sensors, each with a stable unique_id."""
    ids = await setup_entry(hass, config_entry)

    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, config_entry.entry_id)
    assert sorted(entry.unique_id for entry in entries) == sorted(
        f"sas_{stage}_{SENSOR_HASH}" for stage in STAGES
    )

    devices = dr.async_entries_for_config_entry(
        dr.async_get(hass), config_entry.entry_id
    )
    assert [device.name for device in devices] == ["Grid power"]
    assert {entry.device_id for entry in entries} == {devices[0].id}

    lowpass = hass.states.get(ids["lowpass"])
    assert lowpass is not None
    assert lowpass.attributes["icon"] == ICON
    assert lowpass.attributes["type"] == "lowpass"
    assert lowpass.attributes["input_sensor"] == INPUT_SENSOR
    median = hass.states.get(ids["median"])
    assert median is not None
    assert median.attributes["input_entity_id"] == ids["lowpass"]
    ema = hass.states.get(ids["ema"])
    assert ema is not None
    assert ema.attributes["input_entity_id"] == ids["median"]


async def test_update_chain(
    hass: HomeAssistant, config_entry: MockConfigEntry, freezer: FrozenDateTimeFactory
) -> None:
    """Input changes flow through lowpass, then median, then EMA."""
    ids = await setup_entry(hass, config_entry)

    # First sample passes through the lowpass, the median window is not full
    await push(hass, "10")
    assert hass.states.get(ids["lowpass"]).state == "10.0"
    median = hass.states.get(ids["median"])
    assert median.state == "unknown"
    assert median.attributes["missing_data_points"] == 2
    assert hass.states.get(ids["ema"]).state == "unknown"

    # Lowpass weight 1/2: 10 → 15 → 17.5. The median fills at the third value
    freezer.tick(1)
    await push(hass, "20")
    assert float(hass.states.get(ids["lowpass"]).state) == pytest.approx(15.0)
    freezer.tick(1)
    await push(hass, "20.0")
    assert float(hass.states.get(ids["lowpass"]).state) == pytest.approx(17.5)
    assert float(hass.states.get(ids["median"]).state) == pytest.approx(15.0)
    # The EMA passes its first value through
    assert float(hass.states.get(ids["ema"]).state) == pytest.approx(15.0)

    # 10 s later the EMA blends the new median with alpha = 2 / (20/10 + 1)
    freezer.tick(10)
    await push(hass, "20")
    median_value = float(hass.states.get(ids["median"]).state)
    ema = hass.states.get(ids["ema"])
    assert ema.attributes["alpha"] == pytest.approx(2 / 3)
    assert float(ema.state) == pytest.approx(15 + 2 / 3 * (median_value - 15), abs=0.01)

    for stage in STAGES:
        state = hass.states.get(ids[stage])
        assert state.attributes["unit_of_measurement"] == "W"
        assert state.attributes["device_class"] == "power"


async def test_invalid_input_is_skipped(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """A non-numeric input leaves the lowpass value unchanged."""
    ids = await setup_entry(hass, config_entry)
    await push(hass, "10")
    await push(hass, "unavailable")
    assert hass.states.get(ids["lowpass"]).state == "10.0"


async def test_input_removed_is_skipped(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Removing the input sensor leaves the lowpass value unchanged."""
    ids = await setup_entry(hass, config_entry)
    await push(hass, "10")
    hass.states.async_remove(INPUT_SENSOR)
    await hass.async_block_till_done()
    assert hass.states.get(ids["lowpass"]).state == "10.0"


async def preregister(hass: HomeAssistant, entry: MockConfigEntry) -> dict[str, str]:
    """Register the entities up front so restore states can be keyed by entity_id."""
    registry = er.async_get(hass)
    return {
        stage: registry.async_get_or_create(
            "sensor",
            DOMAIN,
            f"sas_{stage}_{SENSOR_HASH}",
            suggested_object_id=f"sas_{stage}",
            config_entry=entry,
        ).entity_id
        for stage in STAGES
    }


async def test_restore_state(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Values and the median window survive a restart."""
    ids = await preregister(hass, config_entry)
    last_updated = datetime.now().isoformat()
    mock_restore_cache(
        hass,
        [
            State(ids["lowpass"], "42.5", {"last_updated": last_updated}),
            State(
                ids["median"],
                "41.0",
                {"last_updated": last_updated, "data_points": [40.0, 41.0, 42.5]},
            ),
            State(ids["ema"], "40.0", {"last_updated": last_updated}),
        ],
    )

    await setup_entry(hass, config_entry)

    assert hass.states.get(ids["lowpass"]).state == "42.5"
    assert hass.states.get(ids["lowpass"]).attributes["previous_value"] == 42.5
    median = hass.states.get(ids["median"])
    assert median.state == "41.0"
    assert median.attributes["data_points"] == [40.0, 41.0, 42.5]
    assert hass.states.get(ids["ema"]).state == "40.0"

    # The next input continues from the restored lowpass value
    await push(hass, "50")
    assert float(hass.states.get(ids["lowpass"]).state) == pytest.approx(46.25)


async def test_restore_invalid_state_starts_fresh(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """A non-numeric restored state is dropped."""
    ids = await preregister(hass, config_entry)
    mock_restore_cache(
        hass, [State(entity_id, "unknown") for entity_id in ids.values()]
    )

    await setup_entry(hass, config_entry)

    for stage in STAGES:
        assert hass.states.get(ids[stage]).state == "unknown"
    assert hass.states.get(ids["median"]).attributes["data_points"] == []


async def test_options_flow_shows_form(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """The options flow opens on the init step."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["step_id"] == "init"


async def test_sensors_publish_state_class(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """All stages are SensorEntity and publish state_class for long-term statistics."""
    ids = await setup_entry(hass, config_entry)
    for value in ("10", "20", "20.0"):
        hass.states.async_set(
            INPUT_SENSOR, value, {**POWER, "state_class": "measurement"}
        )
        await hass.async_block_till_done()

    component = hass.data[SENSOR_COMPONENT]
    for stage in STAGES:
        entity = component.get_entity(ids[stage])
        assert isinstance(entity, SensorEntity)
        state = hass.states.get(ids[stage])
        assert state.attributes["state_class"] == "measurement"
        assert state.attributes["unit_of_measurement"] == "W"
        assert state.attributes["device_class"] == "power"


# Known bugs. strict=True turns them into failures once the issue is fixed,
# so the fix PR has to remove the marker.


@pytest.mark.xfail(strict=True, reason="#90: median uses N + 1 values")
async def test_median_window_holds_sampling_size_values(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """With a window of 3 the median of [15, 17.5, 18.75] is 17.5."""
    ids = await setup_entry(hass, config_entry)
    for value in ("10", "20", "20.0", "20"):
        await push(hass, value)
    assert float(hass.states.get(ids["median"]).state) == pytest.approx(17.5)


@pytest.mark.xfail(strict=True, reason="#68: restore reads 'update_interval'")
async def test_restore_keeps_update_interval(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """The restored update interval is the saved sensor_update_interval."""
    ids = await preregister(hass, config_entry)
    mock_restore_cache(
        hass, [State(ids["lowpass"], "42.5", {"sensor_update_interval": 30})]
    )
    await setup_entry(hass, config_entry)
    assert hass.states.get(ids["lowpass"]).attributes["sensor_update_interval"] == 30


@pytest.mark.xfail(strict=True, reason="#71: unavailable input logs a warning")
async def test_unavailable_input_logs_no_warning(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An unavailable input is normal and not worth a warning."""
    await setup_entry(hass, config_entry)
    await push(hass, "10")
    caplog.clear()
    await push(hass, "unavailable")
    assert not [r for r in caplog.records if r.levelname == "WARNING"]
