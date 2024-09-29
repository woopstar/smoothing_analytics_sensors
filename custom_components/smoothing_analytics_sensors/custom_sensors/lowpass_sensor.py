import logging
from datetime import datetime

from homeassistant.helpers.restore_state import RestoreEntity

from ..const import DOMAIN, ICON, NAME, VERSION
from ..entity import SmoothingAnalyticsEntity

_LOGGER = logging.getLogger(__name__)


def lowpass_filter(current_value, previous_value, time_constant):
    """Apply a lowpass filter to smooth out fast fluctuations."""
    alpha = time_constant / (time_constant + 1)
    return alpha * current_value + (1 - alpha) * previous_value


class LowpassSensor(SmoothingAnalyticsEntity, RestoreEntity):
    """Lowpass filtered sensor with persistent state, precision of 2 decimal places, and device support."""

    _attr_icon = ICON
    _attr_has_entity_name = True

    def __init__(
        self, input_sensor, time_constant, sensor_hash, config_entry, update_interval
    ):
        # Kald super med config_entry for at sikre korrekt initialisering
        super().__init__(config_entry)
        self._input_sensor = input_sensor
        self._time_constant = time_constant
        self._sensor_hash = sensor_hash
        self._state = None
        self._previous_value = 0  # Store the previous value for filtering
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
    def device_info(self):
        """Return device information for the Lowpass Sensor."""
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": self.config_entry.data.get(
                "device_name", "Smoothing Analytics Device"
            ),
            "model": VERSION,
            "manufacturer": NAME,
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
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
            "raw_input": self._previous_value,
            "update_interval": self._update_interval,
        }

    async def async_update(self):
        # Check if enough time has passed since the last update based on the update interval
        now = datetime.now()
        if (
            self._last_update_time
            and (now - self._last_update_time).total_seconds() < self._update_interval
        ):
            return  # Skip the update if the interval hasn't passed

        input_state = self.hass.states.get(self._input_sensor)
        if input_state is None:
            _LOGGER.warning(f"Sensor {self._input_sensor} not found.")
            return
        try:
            current_value = float(input_state.state)
        except ValueError:
            return

        # Fetch unit_of_measurement and device_class from the input sensor
        self._unit_of_measurement = input_state.attributes.get("unit_of_measurement")
        self._device_class = input_state.attributes.get("device_class")

        # Apply lowpass filter
        self._state = round(
            lowpass_filter(current_value, self._previous_value, self._time_constant), 2
        )

        self._previous_value = current_value
        self._last_updated = now.isoformat()

        # Update count and last update time
        self._update_count += 1
        self._last_update_time = now

    async def async_added_to_hass(self):
        """Handle the sensor being added to Home Assistant."""
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
                self._previous_value = 0  # Reset to 0 if the state is not valid
            self._last_updated = old_state.attributes.get("last_updated", None)
            self._update_count = old_state.attributes.get("update_count", 0)
        else:
            _LOGGER.info(
                f"No previous state found for {self._unique_id}, starting fresh."
            )
