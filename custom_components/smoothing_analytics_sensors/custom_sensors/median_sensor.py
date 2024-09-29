import logging
import statistics
from datetime import datetime

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.restore_state import RestoreEntity

from ..const import DEFAULT_MEDIAN_SIZE, DOMAIN, ICON, NAME
from ..entity import SmoothingAnalyticsEntity

_LOGGER = logging.getLogger(__name__)


class MedianSensor(SmoothingAnalyticsEntity, RestoreEntity):
    """Median filtered sensor with persistent state and device support, based on unique_id."""

    # Define the attributes of the entity
    _attr_icon = ICON
    _attr_has_entity_name = True

    def __init__(self, input_unique_id, sampling_size, sensor_hash, config_entry):
        super().__init__(config_entry)
        self._input_unique_id = input_unique_id
        self._sampling_size = sampling_size
        self._sensor_hash = sensor_hash
        self._state = None
        self._data_points = []
        self._last_updated = None
        self._update_count = 0
        self._last_update_time = None
        self._input_entity_id = None
        self._unit_of_measurement = None
        self._device_class = None
        self._config_entry = config_entry
        self._unique_id = f"sas_median_{sensor_hash}"

    def _update_settings(self):
        """Fetch updated settings from config_entry options."""
        self._sampling_size = self._config_entry.options.get(
            "median_sampling_size", DEFAULT_MEDIAN_SIZE
        )

        # Log updated settings
        _LOGGER.debug(f"Updated Median settings: sampling_size={self._sampling_size}")

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
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def device_class(self):
        return self._device_class

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""

        # Calculate the time since the last update
        time_since_last_update = 0
        if self._last_update_time:
            try:
                # Calculate time difference
                time_since_last_update = (datetime.now() - self._last_update_time).total_seconds()
            except TypeError:
                _LOGGER.error("Error calculating time_since_last_update. Check if _last_update_time is set correctly.")
                time_since_last_update = 0

        # Calculate the number of data points
        data_points_count = len(self._data_points)

        # Calculate the number of missing data points
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

        # Ensure settings are reloaded if config is changed.
        self._update_settings()

        # Get the current time
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
                f"Sensor {self._input_entity_id} not ready or not found. Skipping median sensor update."
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

        # Add the input value to the data points in the beginning
        self._data_points.insert(0, input_value)

        # Ensure we only keep the last `sampling_size` data points, trim if needed
        if len(self._data_points) - self._sampling_size > 0:
            self._data_points = self._data_points[self._sampling_size:]
        else:
            _LOGGER.error(f"Invalid calculation for excess_points: {excess_points}")

        # Calculate the median if we have enough data points
        if len(self._data_points) >= self._sampling_size:
            self._state = round(statistics.median(self._data_points), 2)
            self._last_updated = now.isoformat()
            self._last_update_time = datetime.now()

        # Log the data points for debugging purposes
        _LOGGER.debug(
            f"Updated MedianSensor with input_entity_id: {self._input_entity_id}, "
            f"input_value: {input_value}, data_points: {self._data_points}"
        )

        # Update count and last update time
        self._update_count += 1

    async def _resolve_input_entity_id(self):
        """Resolve the entity_id from the unique_id using entity_registry."""

        # Resolve the entity_id from the unique_id
        registry = er.async_get(self.hass)

        # Fetch the entity_id from the unique_id
        entry = registry.async_get_entity_id("sensor", DOMAIN, self._input_unique_id)

        # Log the resolved entity_id for debugging purposes
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
                self._data_points = old_state.attributes.get("data_points", []) or []
            except (ValueError, TypeError):
                _LOGGER.warning(
                    f"Could not restore state for {self._unique_id}, invalid value: {old_state.state}"
                )
                self._state = None
                self._data_points = []
            self._last_updated = old_state.attributes.get("last_updated", None)
            self._update_count = old_state.attributes.get("update_count", 0)
            self._last_update_time = old_state.attributes.get("last_update_time", 0)
        else:
            _LOGGER.info(
                f"No previous state found for {self._unique_id}, starting fresh."
            )
