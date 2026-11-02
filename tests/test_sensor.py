"""Integration tests for the lowpass → median → EMA sensor chain."""

import math

import pytest
from freezegun.api import FrozenDateTimeFactory
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    mock_restore_cache,
)

from homeassistant.components.sensor import (
    DATA_COMPONENT as SENSOR_COMPONENT,
    SensorEntity,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import dt as dt_util

from custom_components.smoothing_analytics_sensors.const import DOMAIN, ICON
from custom_components.smoothing_analytics_sensors.filters import calculate_alpha
from custom_components.smoothing_analytics_sensors.utils.misc import (
    generate_md5_hash,
)

INPUT_SENSOR = "sensor.grid_power"
SENSOR_HASH = generate_md5_hash(INPUT_SENSOR)
STAGES = ("lowpass", "median", "ema")
POWER = {"unit_of_measurement": "W", "device_class": "power"}
# With this time constant a 1 s step gives the new value weight 1/2
HALF_PER_SECOND = 1 / math.log(2)


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Add an entry with short windows so the chain fills quickly."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Grid power",
        data={
            "input_sensor": INPUT_SENSOR,
            "device_name": "Grid power",
            "lowpass_time_constant": HALF_PER_SECOND,
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

    # 10 s later the EMA blends the new median with alpha = 1 - 0.05 ** (10/20)
    freezer.tick(10)
    await push(hass, "20")
    median_value = float(hass.states.get(ids["median"]).state)
    ema = hass.states.get(ids["ema"])
    alpha = 1 - 0.05**0.5
    assert ema.attributes["alpha"] == pytest.approx(alpha)
    assert float(ema.state) == pytest.approx(15 + alpha * (median_value - 15), abs=0.01)

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
    await push(hass, "not a number")
    assert hass.states.get(ids["lowpass"]).state == "10.0"


async def test_unavailable_input_makes_stack_unavailable(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    """An unavailable input makes every stage unavailable, without warnings."""
    ids = await setup_entry(hass, config_entry)
    for value in ("10", "20", "20.0"):
        await push(hass, value)
    lowpass_before = float(hass.states.get(ids["lowpass"]).state)

    caplog.clear()
    await push(hass, "unavailable")
    for stage in STAGES:
        assert hass.states.get(ids[stage]).state == "unavailable"
    assert not [r for r in caplog.records if r.levelname == "WARNING"]

    # Back online: the lowpass continues from its last value
    freezer.tick(1)
    await push(hass, "20")
    lowpass = float(hass.states.get(ids["lowpass"]).state)
    assert lowpass == pytest.approx((lowpass_before + 20) / 2)
    for stage in STAGES:
        assert hass.states.get(ids[stage]).state != "unavailable"


async def test_unknown_input_is_skipped_quietly(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An unknown input keeps the last value and logs no warning."""
    ids = await setup_entry(hass, config_entry)
    await push(hass, "10")
    caplog.clear()
    await push(hass, "unknown")
    assert hass.states.get(ids["lowpass"]).state == "10.0"
    assert not [r for r in caplog.records if r.levelname == "WARNING"]


async def test_starts_unavailable_with_unavailable_input(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """The lowpass is unavailable from the start if the input is."""
    hass.states.async_set(INPUT_SENSOR, "unavailable")
    ids = await setup_entry(hass, config_entry)
    assert hass.states.get(ids["lowpass"]).state == "unavailable"


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
    hass: HomeAssistant, config_entry: MockConfigEntry, freezer: FrozenDateTimeFactory
) -> None:
    """Values and the median window survive a restart."""
    ids = await preregister(hass, config_entry)
    last_updated = dt_util.utcnow().isoformat()
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

    # The next input, 1 s later, continues from the restored lowpass value
    freezer.tick(1)
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


async def test_sensors_are_not_polled(
    hass: HomeAssistant, config_entry: MockConfigEntry, freezer: FrozenDateTimeFactory
) -> None:
    """Without upstream changes no stage updates, even after 5 minutes."""
    ids = await setup_entry(hass, config_entry)
    await push(hass, "10")
    before = {stage: hass.states.get(ids[stage]) for stage in STAGES}

    for _ in range(10):
        freezer.tick(30)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    for stage in STAGES:
        state = hass.states.get(ids[stage])
        assert state.last_updated == before[stage].last_updated
        assert state.attributes == before[stage].attributes
    assert hass.states.get(ids["median"]).attributes["data_points"] == [10.0]


async def test_dst_change_keeps_positive_interval(
    hass: HomeAssistant, config_entry: MockConfigEntry, freezer: FrozenDateTimeFactory
) -> None:
    """At the autumn DST change local time goes back, the measured Δt does not."""
    await hass.config.async_set_time_zone("Europe/Copenhagen")
    # 02:58 CEST, two minutes before clocks go back to 02:00 CET
    freezer.move_to("2026-10-25T00:58:00+00:00")
    ids = await setup_entry(hass, config_entry)
    for value in ("10", "20", "20.0"):
        freezer.tick(1)
        await push(hass, value)

    freezer.tick(120)
    await push(hass, "20")

    lowpass = hass.states.get(ids["lowpass"])
    assert lowpass.attributes["sensor_update_interval"] == pytest.approx(120)
    assert dt_util.parse_datetime(lowpass.attributes["last_updated"]).tzinfo
    ema = hass.states.get(ids["ema"])
    assert ema.attributes["sensor_update_interval"] == pytest.approx(120)
    assert 0 < ema.attributes["alpha"] <= 1


async def test_restored_naive_timestamp_is_read_as_local_time(
    hass: HomeAssistant, config_entry: MockConfigEntry, freezer: FrozenDateTimeFactory
) -> None:
    """A naive last_updated from older versions is read in the HA time zone."""
    await hass.config.async_set_time_zone("Europe/Copenhagen")
    freezer.move_to("2026-11-02T10:00:00+00:00")
    ids = await preregister(hass, config_entry)
    # 10:59:00 local (CET, UTC+1) is 60 s before now
    mock_restore_cache(
        hass, [State(ids["lowpass"], "10.0", {"last_updated": "2026-11-02T10:59:00"})]
    )
    await setup_entry(hass, config_entry)

    await push(hass, "20")
    assert hass.states.get(ids["lowpass"]).attributes[
        "sensor_update_interval"
    ] == pytest.approx(60)


async def test_restore_keeps_update_interval(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """The saved sensor_update_interval is restored and drives the EMA alpha."""
    ids = await preregister(hass, config_entry)
    mock_restore_cache(
        hass,
        [
            State(ids["lowpass"], "42.5", {"sensor_update_interval": 7}),
            State(ids["ema"], "40.0", {"sensor_update_interval": 7}),
        ],
    )
    await setup_entry(hass, config_entry)

    assert hass.states.get(ids["lowpass"]).attributes["sensor_update_interval"] == 7
    ema = hass.states.get(ids["ema"]).attributes
    assert ema["sensor_update_interval"] == 7
    assert ema["alpha"] == pytest.approx(calculate_alpha(20, 7))


async def test_small_inputs_converge(
    hass: HomeAssistant, config_entry: MockConfigEntry, freezer: FrozenDateTimeFactory
) -> None:
    """Steps below the display precision are not rounded away."""
    ids = await setup_entry(hass, config_entry)
    await push(hass, "0")
    for i in range(30):
        freezer.tick(1)
        # Alternate the string so every push is a state change
        await push(hass, "0.004" if i % 2 else "0.0040")

    assert float(hass.states.get(ids["lowpass"]).state) == pytest.approx(
        0.004, rel=0.01
    )
    assert float(hass.states.get(ids["ema"]).state) > 0


async def test_display_precision_is_two_decimals(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """The UI shows 2 decimals by default."""
    ids = await setup_entry(hass, config_entry)
    registry = er.async_get(hass)
    for stage in STAGES:
        options = registry.async_get(ids[stage]).options
        assert options["sensor"]["suggested_display_precision"] == 2


async def test_meter_input_is_published_as_measurement(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A total_increasing energy input gives a measurement without device class."""
    ids = await setup_entry(hass, config_entry)
    meter = {
        "unit_of_measurement": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
    }
    for value in ("10", "11", "12"):
        hass.states.async_set(INPUT_SENSOR, value, meter)
        await hass.async_block_till_done()

    for stage in STAGES:
        attributes = hass.states.get(ids[stage]).attributes
        assert attributes["state_class"] == "measurement"
        assert attributes["unit_of_measurement"] == "kWh"
        assert "device_class" not in attributes
    assert "impossible considering device class" not in caplog.text


async def test_state_class_before_first_update(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """The state class is measurement from the start."""
    ids = await setup_entry(hass, config_entry)
    assert hass.states.get(ids["lowpass"]).attributes["state_class"] == "measurement"


async def test_median_window_holds_sampling_size_values(
    hass: HomeAssistant, config_entry: MockConfigEntry, freezer: FrozenDateTimeFactory
) -> None:
    """With a window of 3 the median of [15, 17.5, 18.75] is 17.5."""
    ids = await setup_entry(hass, config_entry)
    for value in ("10", "20", "20.0", "20"):
        freezer.tick(1)
        await push(hass, value)
    assert float(hass.states.get(ids["median"]).state) == pytest.approx(17.5)


async def test_float_window_from_older_entries_is_an_int(hass: HomeAssistant) -> None:
    """A median window stored as 3.0 by older releases is used as 3."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={"input_sensor": INPUT_SENSOR, "median_sampling_size": 3.0},
    )
    entry.add_to_hass(hass)
    ids = await setup_entry(hass, entry)
    size = hass.states.get(ids["median"]).attributes["median_sampling_size"]
    assert size == 3
    assert isinstance(size, int)


@pytest.mark.parametrize(
    ("language", "names"),
    [
        ("en", {"lowpass": "Lowpass", "median": "Median", "ema": "EMA"}),
        ("da", {"lowpass": "Lavpas", "median": "Median", "ema": "EMA"}),
    ],
)
async def test_entity_names_are_translated(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    language: str,
    names: dict[str, str],
) -> None:
    """New entries get short translated names without a hash."""
    hass.config.language = language
    ids = await setup_entry(hass, config_entry)
    for stage, name in names.items():
        assert hass.states.get(ids[stage]).attributes["friendly_name"] == (
            f"Grid power {name}"
        )
    assert ids["ema"] == "sensor.grid_power_ema"


async def test_existing_entity_ids_are_kept(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Entity IDs from older releases stay, only the display name changes."""
    registry = er.async_get(hass)
    old_id = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"sas_ema_{SENSOR_HASH}",
        suggested_object_id=f"grid_power_ema_filtered_sensor_{SENSOR_HASH}",
        config_entry=config_entry,
    ).entity_id
    ids = await setup_entry(hass, config_entry)
    assert ids["ema"] == old_id
    assert hass.states.get(old_id).attributes["friendly_name"] == "Grid power EMA"
