import logging
import statistics
from datetime import datetime

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.restore_state import RestoreEntity

from ..const import DOMAIN, ICON, NAME, VERSION
from ..entity import SmoothingAnalyticsEntity

_LOGGER = logging.getLogger(__name__)


class MedianSensor(SmoothingAnalyticsEntity, RestoreEntity):
    """Median filtered sensor with persistent state and device support, based on unique_id."""

    _attr_icon = ICON
    _attr_has_entity_name = True

    def __init__(self, input_unique_id, sampling_size, sensor_hash, config_entry):
        super().__init__(config_entry)
        self._input_unique_id = input_unique_id
        self._sampling_size = sampling_size
        self._sensor_hash = sensor_hash
        self._state = None
        self._data_points = []  # Store the last N data points
        self._last_updated = None
        self._update_count = 0
        self._last_update_time = None
        self._input_entity_id = None  # To store the resolved entity_id
        self._unique_id = f"sas_median_{sensor_hash}"

    @property
    def name(self):
        return f"Median Filtered Sensor {self._sensor_hash}"

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state

    @property
    def device_info(self):
        """Return device information for the Median Sensor."""
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

        data_points_count = len(self._data_points)
        missing_data_points = max(0, self._sampling_size - data_points_count)

        return {
            "median_sampling_size": self._sampling_size,
            "input_unique_id": self._input_unique_id,
            "input_entity_id": self._input_entity_id,  # For debugging
            "unique_id": self._unique_id,
            "sensor_hash": self._sensor_hash,
            "last_updated": self._last_updated,
            "update_count": self._update_count,
            "time_since_last_update": time_since_last_update,
            "data_points_count": data_points_count,
            "missing_data_points": missing_data_points,
            "data_points": self._data_points,
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
                f"Sensor {self._input_entity_id} not ready or not found. Skipping median update."
            )
            return
        try:
            current_value = float(input_state.state)
        except ValueError:
            _LOGGER.error(
                f"Invalid value from {self._input_entity_id}: {input_state.state}"
            )
            return

        # Append the current value to the list of data points
        self._data_points.append(current_value)

        # Ensure we only keep the last `sampling_size` data points
        if len(self._data_points) > self._sampling_size:
            self._data_points.pop(0)

        # Calculate the median if we have enough data points
        if len(self._data_points) >= self._sampling_size:
            self._state = round(statistics.median(self._data_points), 2)
            self._last_updated = datetime.now().isoformat()

        # Log the data points for debugging purposes
        _LOGGER.debug(
            f"Updated MedianSensor with input_entity_id: {self._input_entity_id}, "
            f"current_value: {current_value}, data_points: {self._data_points}"
        )

        # Update count and last update time
        self._update_count += 1
        self._last_update_time = datetime.now()

    async def _resolve_input_entity_id(self):
        """Resolve the entity_id from the unique_id using entity_registry."""
        registry = er.async_get(self.hass)
        entry = registry.async_get_entity_id("sensor", DOMAIN, self._input_unique_id)

        if entry:
            self._input_entity_id = entry  # This should assign the correct entity_id
            _LOGGER.debug(
                f"Resolved entity_id for unique_id {self._input_unique_id}: {self._input_entity_id}"
            )
        else:
            _LOGGER.warning(
                f"Entity with unique_id {self._input_unique_id} not found in registry."
            )

    async def async_added_to_hass(self):
        """Handle the sensor being added to Home Assistant."""
        # Restore the previous state and data points from persistent storage
        old_state = await self.async_get_last_state()
        if old_state is not None:
            _LOGGER.info(f"Restoring state for {self._unique_id}")
            try:
                self._state = round(float(old_state.state), 2)
                self._data_points = old_state.attributes.get("data_points", []) or []
            except (ValueError, TypeError):
                _LOGGER.warning(
                    f"Could not restore state for {self._unique_id}, invalid value: {old_state.state}"
                )
                self._state = None
                self._data_points = []  # Reset data points if state is invalid
            self._last_updated = old_state.attributes.get("last_updated", None)
            self._update_count = old_state.attributes.get("update_count", 0)
        else:
            _LOGGER.info(
                f"No previous state found for {self._unique_id}, starting fresh."
            )
