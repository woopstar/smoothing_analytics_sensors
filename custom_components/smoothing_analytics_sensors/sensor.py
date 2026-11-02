import logging

from homeassistant.helpers import entity_registry as er

from .const import (
    DEFAULT_EMA_DESIRED_TIME_TO_95,
    DEFAULT_LOW_PASS,
    DEFAULT_MEDIAN_SIZE,
)
from .custom_sensors.ema_sensor import EmaSensor
from .custom_sensors.lowpass_sensor import LowpassSensor
from .custom_sensors.median_sensor import MedianSensor
from .utils.misc import generate_md5_hash, get_config_value

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Smoothing Analytics sensors from a config entry."""
    config = config_entry.data

    # The hash and unique IDs come from the input entity_id at creation time.
    # The current entity_id is resolved from the registry id, so a renamed
    # input keeps working after a restart.
    original_input_sensor = config.get("input_sensor")
    input_sensor = original_input_sensor
    if input_entity_uuid := config.get("input_entity_uuid"):
        input_sensor = (
            er.async_resolve_entity_id(er.async_get(hass), input_entity_uuid)
            or original_input_sensor
        )

    lowpass_time_constant = get_config_value(
        config_entry, "lowpass_time_constant", DEFAULT_LOW_PASS
    )

    median_sampling_size = get_config_value(
        config_entry, "median_sampling_size", DEFAULT_MEDIAN_SIZE
    )

    desired_time_to_95 = get_config_value(
        config_entry, "desired_time_to_95", DEFAULT_EMA_DESIRED_TIME_TO_95
    )

    # Generate a unique hash based on the input sensor
    sensor_hash = generate_md5_hash(original_input_sensor)

    # Median and EMA find their upstream stage by its unique_id
    lowpass_unique_id = f"sas_lowpass_{sensor_hash}"
    median_unique_id = f"sas_median_{sensor_hash}"

    # Create the lowpass from the input sensor
    lowpass_sensor = LowpassSensor(
        input_sensor, lowpass_time_constant, sensor_hash, config_entry
    )

    # Create the median, and ema sensors using the unique IDs
    median_sensor = MedianSensor(
        lowpass_unique_id, median_sampling_size, sensor_hash, config_entry
    )

    ema_sensor = EmaSensor(
        median_unique_id, desired_time_to_95, sensor_hash, config_entry
    )

    # Keep the stages on the entry for diagnostics
    sensors = [lowpass_sensor, median_sensor, ema_sensor]
    config_entry.runtime_data = sensors

    # Add sensors to Home Assistant
    async_add_entities(sensors)
