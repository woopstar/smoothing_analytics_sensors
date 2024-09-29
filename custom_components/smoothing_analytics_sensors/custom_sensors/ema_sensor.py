import logging
from datetime import datetime

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.restore_state import RestoreEntity

from ..const import DOMAIN, ICON, NAME
from ..entity import SmoothingAnalyticsEntity

_LOGGER = logging.getLogger(__name__)

def calculate_alpha(smoothing_window):
    """Calculate alpha for Exponential Moving Average (EMA)"""
    return 2 / (smoothing_window + 1)


def ema_filter(input_value, previous_value, alpha):
    """Apply Exponential Moving Average (EMA) filter using the given alpha"""
    return alpha * input_value + (1 - alpha) * previous_value


class EmaSensor(SmoothingAnalyticsEntity, RestoreEntity):
    """Exponential Moving Average (EMA) filtered sensor with persistent state and device support, based on unique_id."""

    # Define the attributes of the entity
    _attr_icon = ICON
    _attr_has_entity_name = True

    def __init__(self, input_unique_id, smoothing_window, sensor_hash, config_entry):
        super().__init__(config_entry)
        self._input_unique_id = input_unique_id
        self._smoothing_window = smoothing_window
        self._sensor_hash = sensor_hash
        self._state = None
        self._previous_value = 0
        self._last_updated = None
        self._update_count = 0
        self._last_update_time = None
        self._input_entity_id = None
        self._unit_of_measurement = None
        self._device_class = None
        self._unique_id = f"sas_ema_{sensor_hash}"

        # Calculate alpha once and store it
        self._alpha = calculate_alpha(self._smoothing_window)

    @property
    def name(self):
        return f"EMA Filtered Sensor {self._sensor_hash}"

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
            "ema_smoothing_window": self._smoothing_window,
            "input_unique_id": self._input_unique_id,
            "input_entity_id": self._input_entity_id,
            "unique_id": self._unique_id,
            "sensor_hash": self._sensor_hash,
            "last_updated": self._last_updated,
            "update_count": self._update_count,
            "time_since_last_update": time_since_last_update,
            "previous_value": self._previous_value,
            "alpha": self._alpha,
        }

    async def async_update(self):
        """Update the sensor state based on the input sensor's value."""

        now = datetime.now()

        # Check if the input_entity_id has been resolved from unique_id
        if not self._input_entity_id:
            await self._resolve_input_entity_id()

        # Continue if input_entity_id is available
        if not self._input_entity_id:
            _LOGGER.warning(f"Entity with unique_id {self._input_unique_id} not found.")
            return

        # Fetch the current value from the input sensor
        input_state = self.hass.states.get(self._input_entity_id)
        if input_state is None or input_state.state is None:
            _LOGGER.warning(
                f"Sensor {self._input_entity_id} not ready or not found. Skipping EMA sensor update."
            )
            return
        try:
            input_value = float(input_state.state)
        except ValueError:
            _LOGGER.error(
                f"Invalid value from {self._input_entity_id}: {input_state.state}"
            )
            return

        # Fetch unit_of_measurement and device_class from the input sensor
        self._unit_of_measurement = input_state.attributes.get("unit_of_measurement")
        self._device_class = input_state.attributes.get("device_class")

        # Apply EMA filter using pre-calculated alpha
        self._state = round(
            ema_filter(input_value, self._previous_value, self._alpha), 2
        )

        # Update the previous value and last updated time
        self._previous_value = input_value
        self._last_updated = now.isoformat()

        # Update count and last update time
        self._update_count += 1
        self._last_update_time = now

    async def _resolve_input_entity_id(self):
        """Resolve the entity_id from the unique_id using entity_registry."""

        # Resolve the entity_id from the unique_id
        registry = er.async_get(self.hass)

        # Resolve the entity_id from the unique_id
        entry = registry.async_get_entity_id("sensor", DOMAIN, self._input_unique_id)

        # Store the resolved entity_id
        if entry:
            self._input_entity_id = entry

            _LOGGER.debug(
                f"Resolved entity_id for unique_id {self._input_unique_id}: {self._input_entity_id}"
            )
        else:
            _LOGGER.warning(
                f"Entity with unique_id {self._input_unique_id} not found in registry."
            )

    async def async_added_to_hass(self):
        """Handle the sensor being added to Home Assistant."""

        # Restore the previous state from persistent storage
        old_state = await self.async_get_last_state()

        if old_state is not None:
            _LOGGER.info(f"Restoring state for {self._unique_id}")

            try:
                self._state = round(float(old_state.state), 2)
                self._previous_value = float(self._state)
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
