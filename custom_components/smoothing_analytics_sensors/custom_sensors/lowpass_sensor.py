import logging
from datetime import datetime

from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.event import async_track_state_change

from ..const import DEFAULT_LOW_PASS, DOMAIN, ICON, NAME
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

    def __init__(self, input_sensor, time_constant, sensor_hash, config_entry):
        super().__init__(config_entry)
        self._input_sensor = input_sensor
        self._time_constant = time_constant
        self._sensor_hash = sensor_hash
        self._state = None
        self._previous_value = None
        self._update_count = 0
        self._last_updated = None
        self._unit_of_measurement = None
        self._device_class = None
        self._config_entry = config_entry
        self._unique_id = f"sas_lowpass_{sensor_hash}"
        self._update_interval = 1

        # If options flow is used to change the sampling size, it will override
        self._update_settings()

    def _update_settings(self):
        """Fetch updated settings from config_entry options."""
        self._time_constant = self._config_entry.options.get(
            "lowpass_time_constant", DEFAULT_LOW_PASS
        )

        # Log updated settings
        _LOGGER.debug(f"Updated Lowpass settings: time_constant={self._time_constant}")

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

        return {
            "lowpass_time_constant": self._time_constant,
            "sensor_update_interval": self._update_interval,
            "input_sensor": self._input_sensor,
            "unique_id": self._unique_id,
            "sensor_hash": self._sensor_hash,
            "last_updated": self._last_updated,
            "update_count": self._update_count,
            "previous_value": self._previous_value,
        }

    async def _handle_update(self, entity_id=None, old_state=None, new_state=None):
        """Handle the sensor state update (for both manual and state change)."""

        # Get the current time
        now = datetime.now()

        # Calculate the update interval to be used
        if self._last_updated is not None:
            self._update_interval = (now - datetime.fromisoformat(self._last_updated)).total_seconds()

        # Ensure settings are reloaded if config is changed.
        self._update_settings()

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

        # Update the previous lowpass value to the new lowpass value
        self._previous_value = self._state

        # Apply lowpass filter when we have a previous value
        if self._previous_value is not None:
            self._state = round(
                lowpass_filter(input_value, self._previous_value, self._time_constant),
                2,
            )
        else:
            self._state = input_value

        # Update count and last update time
        self._update_count += 1
        self._last_updated = now.isoformat()

        # Trigger an update in Home Assistant
        self.async_write_ha_state()

    async def async_update(self):
        """Manually trigger the sensor update."""
        await self._handle_update()

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
                self._previous_value = None

            self._last_updated = old_state.attributes.get("last_updated", None)
            self._update_interval = old_state.attributes.get("update_interval", 1)
            self._update_count = old_state.attributes.get("update_count", 0)
        else:
            _LOGGER.info(
                f"No previous state found for {self._unique_id}, starting fresh."
            )

        # Start listening for state changes of the input sensor
        if self._input_sensor:
            _LOGGER.info(f"Starting to track state changes for entity_id {self._input_sensor}")
            async_track_state_change(
                self.hass, self._input_sensor, self._handle_update
            )
        else:
            _LOGGER.error(f"Failed to track state changes, input_sensor is not resolved.")
