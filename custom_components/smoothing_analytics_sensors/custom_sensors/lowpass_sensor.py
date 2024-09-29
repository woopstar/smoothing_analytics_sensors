import logging
from datetime import datetime

from homeassistant.helpers.restore_state import RestoreEntity

from ..const import DOMAIN, ICON, NAME
from ..entity import SmoothingAnalyticsEntity

_LOGGER = logging.getLogger(__name__)


def lowpass_filter(input_value, previous_value, time_constant):
    """Apply a lowpass filter to smooth out fast fluctuations."""
    alpha = time_constant / (time_constant + 1)
    return alpha * input_value + (1 - alpha) * previous_value


class LowpassSensor(SmoothingAnalyticsEntity, RestoreEntity):
    """Lowpass filtered sensor with persistent state, precision of 2 decimal places, and device support."""

    # Define the attributes of the entity
    _attr_icon = ICON
    _attr_has_entity_name = True

    def __init__(
        self, input_sensor, time_constant, sensor_hash, config_entry, update_interval
    ):
        super().__init__(config_entry)
        self._input_sensor = input_sensor
        self._time_constant = time_constant
        self._sensor_hash = sensor_hash
        self._state = None
        self._previous_value = 0
        self._update_count = 0
        self._last_update_time = None
        self._last_updated = None
        self._update_interval = update_interval
        self._unit_of_measurement = None
        self._device_class = None
        self._unique_id = f"sas_lowpass_{sensor_hash}"

    @property
    def name(self):
        return f"Lowpass Filtered Sensor {self._sensor_hash}"

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def device_class(self):
        return self._device_class

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""

        # Calculate the time since the last update
        time_since_last_update = None
        if self._last_update_time:
            time_since_last_update = (
                datetime.now() - self._last_update_time
            ).total_seconds()

        return {
            "lowpass_time_constant": self._time_constant,
            "input_sensor": self._input_sensor,
            "unique_id": self._unique_id,
            "sensor_hash": self._sensor_hash,
            "last_updated": self._last_updated,
            "update_count": self._update_count,
            "time_since_last_update": time_since_last_update,
            "previous_value": self._previous_value,
            "update_interval": self._update_interval,
        }

    async def async_update(self):
        """Update the sensor state based on the input sensor's value."""

        now = datetime.now()

        # Check if enough time has passed since the last update based on the update interval
        if (
            self._last_update_time
            and (now - self._last_update_time).total_seconds() < self._update_interval
        ):
            return  # Skip the update if the interval hasn't passed

        # Fetch the current value from the input sensor
        input_state = self.hass.states.get(self._input_sensor)
        if input_state is None:
            _LOGGER.warning(f"Sensor {self._input_sensor} not found.")
            return
        try:
            input_value = float(input_state.state)
        except ValueError:
            _LOGGER.error(
                f"Invalid value from {self._input_sensor}: {input_state.state}"
            )
            return

        # Fetch unit_of_measurement and device_class from the input sensor
        self._unit_of_measurement = input_state.attributes.get("unit_of_measurement")
        self._device_class = input_state.attributes.get("device_class")

        # Apply lowpass filter
        self._state = round(
            lowpass_filter(input_value, self._previous_value, self._time_constant), 2
        )

        # Log detailed information about the update
        _LOGGER.debug(f"Input value: {input_value}, Previous lowpass value: {self._previous_value}")
        _LOGGER.debug(f"New lowpass value: {self._state}")

        # Update the previous lowpass value to the new lowpass value
        self._previous_value = self._state

        # Update the last updated time
        self._last_updated = now.isoformat()

        # Update count and last update time
        self._update_count += 1
        self._last_update_time = now

    async def async_added_to_hass(self):
        """Handle the sensor being added to Home Assistant."""

        # Restore the previous state if available
        old_state = await self.async_get_last_state()
        if old_state is not None:
            _LOGGER.info(f"Restoring state for {self._unique_id}")
            try:
                self._state = round(float(old_state.state), 2)
                self._previous_value = float(self._state)  # Restore the previous value
            except (ValueError, TypeError):
                _LOGGER.warning(
                    f"Could not restore state for {self._unique_id}, invalid value: {old_state.state}"
                )
                self._state = None
                self._previous_value = 0
            self._last_updated = old_state.attributes.get("last_updated", None)
            self._update_count = old_state.attributes.get("update_count", 0)
        else:
            _LOGGER.info(
                f"No previous state found for {self._unique_id}, starting fresh."
            )
