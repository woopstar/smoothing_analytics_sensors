import hashlib
import logging

from .const import DOMAIN
from .custom_sensors.ema_sensor import EmaSensor
from .custom_sensors.lowpass_sensor import LowpassSensor
from .custom_sensors.median_sensor import MedianSensor

_LOGGER = logging.getLogger(__name__)


def generate_md5_hash(input_sensor):
    """Generate an MD5 hash based on the input sensor's name."""
    return hashlib.md5(input_sensor.encode("utf-8")).hexdigest()


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Smoothing Analytics sensors from a config entry."""
    config = config_entry.data

    # Extract configuration parameters
    input_sensor = config.get("input_sensor")
    lowpass_time_constant = config.get("lowpass_time_constant", 15)
    median_sampling_size = config.get("median_sampling_size", 15)
    ema_smoothing_window = config.get("ema_smoothing_window", 300)
    update_interval = config.get("update_interval", 1)

    # Generate a unique hash based on the input sensor
    sensor_hash = generate_md5_hash(input_sensor)

    # Unique input IDs for median and EMA sensors for stacking purposes
    median_unique_id = f"sas_lowpass_{sensor_hash}"
    ema_unique_id = f"sas_median_{sensor_hash}"

    # Create the lowpass, median, and ema sensors using the unique IDs
    lowpass_sensor = LowpassSensor(
        input_sensor, lowpass_time_constant, sensor_hash, config_entry, update_interval
    )
    median_sensor = MedianSensor(
        median_unique_id, median_sampling_size, sensor_hash, config_entry
    )
    ema_sensor = EmaSensor(
        ema_unique_id, ema_smoothing_window, sensor_hash, config_entry
    )

    # Add sensors to Home Assistant
    async_add_entities([lowpass_sensor, median_sensor, ema_sensor])

    # Store reference to the platform to handle unloads later
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][config_entry.entry_id] = async_add_entities


async def async_unload_entry(hass, entry):
    """Handle unloading of an entry."""
    platform = hass.data[DOMAIN].get(entry.entry_id)
    if platform:
        return await platform.async_remove_entry(entry)
    return False
