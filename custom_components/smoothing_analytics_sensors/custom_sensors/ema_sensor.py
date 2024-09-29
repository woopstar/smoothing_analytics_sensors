import logging
from datetime import datetime

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.restore_state import RestoreEntity

from ..const import DOMAIN, ICON, NAME, VERSION
from ..entity import SmoothingAnalyticsEntity

_LOGGER = logging.getLogger(__name__)


def ema_filter(current_value, previous_ema, smoothing_window):
    """Apply Exponential Moving Average (EMA) filter."""
    alpha = 2 / (smoothing_window + 1)
    return alpha * current_value + (1 - alpha) * previous_ema


class EmaSensor(SmoothingAnalyticsEntity, RestoreEntity):
    """Exponential Moving Average (EMA) filtered sensor with persistent state and device support, based on unique_id."""

    _attr_icon = ICON
    _attr_has_entity_name = True

    def __init__(self, input_unique_id, smoothing_window, sensor_hash, config_entry):
        # Kald super med config_entry for at sikre korrekt initialisering
        super().__init__(config_entry)
        self._input_unique_id = input_unique_id
        self._smoothing_window = smoothing_window
        self._sensor_hash = sensor_hash
        self._state = None
        self._previous_ema = 0  # Store the previous EMA value
        self._last_updated = None
        self._update_count = 0
        self._last_update_time = None
        # self.config_entry = config_entry
        self._input_entity_id = None  # To store the resolved entity_id
        self._unique_id = f"sas_ema_{sensor_hash}"

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
    def device_info(self):
        """Return device information for the EMA Sensor."""
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
            "ema_smoothing_window": self._smoothing_window,
            "input_unique_id": self._input_unique_id,
            "input_entity_id": self._input_entity_id,  # For debugging
            "unique_id": self._unique_id,
            "sensor_hash": self._sensor_hash,
            "last_updated": self._last_updated,
            "update_count": self._update_count,
            "time_since_last_update": time_since_last_update,
            "previous_ema": self._previous_ema,  # The previous EMA value before the current update
        }

    async def async_update(self):
        """Update the sensor state based on the input sensor's value."""
        # Check if the input_entity_id has been resolved from unique_id
        if not self._input_entity_id:
            await self._resolve_input_entity_id()

        # Continue if input_entity_id is available
        if not self._input_entity_id:
            _LOGGER.warning(f"Entity with unique_id {self._input_unique_id} not found.")
            return

        input_state = self.hass.states.get(self._input_entity_id)
        if input_state is None or input_state.state is None:
            _LOGGER.warning(
                f"Sensor {self._input_entity_id} not ready or not found. Skipping EMA update."
            )
            return
        try:
            current_value = float(input_state.state)
        except ValueError:
            return

        # Apply EMA filter
        self._state = round(
            ema_filter(current_value, self._previous_ema, self._smoothing_window), 2
        )
        self._previous_ema = self._state  # Store the filtered value for next iteration
        self._last_updated = datetime.now().isoformat()

        # Update count and last update time
        self._update_count += 1
        self._last_update_time = datetime.now()

    async def _resolve_input_entity_id(self):
        """Resolve the entity_id from the unique_id using entity_registry."""
        registry = er.async_get(self.hass)
        entry = registry.async_get_entity_id("sensor", DOMAIN, self._input_unique_id)
        if entry:
            self._input_entity_id = entry
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
                self._previous_ema = float(
                    self._state
                )  # Restore the previous EMA value
            except (ValueError, TypeError):
                _LOGGER.warning(
                    f"Could not restore state for {self._unique_id}, invalid value: {old_state.state}"
                )
                self._state = None
                self._previous_ema = 0  # Reset to 0 if the state is not valid
            self._last_updated = old_state.attributes.get("last_updated", None)
            self._update_count = old_state.attributes.get("update_count", 0)
        else:
            _LOGGER.info(
                f"No previous state found for {self._unique_id}, starting fresh."
            )
