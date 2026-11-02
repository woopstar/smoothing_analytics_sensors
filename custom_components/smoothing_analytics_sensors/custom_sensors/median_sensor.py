"""Median stage: moving median over the last N lowpass values."""

import logging

from ..const import DEFAULT_MEDIAN_SIZE
from ..entity import SmoothingAnalyticsSensor
from ..filters import median_filter
from ..utils.misc import get_config_value

_LOGGER = logging.getLogger(__name__)


class MedianSensor(SmoothingAnalyticsSensor):
    """Median filtered sensor with persistent state and device support, based on unique_id."""

    _type = "median"
    # Fast-changing attributes stay out of the database. Restore reads the
    # window from the restore cache, not from the recorder.
    _unrecorded_attributes = frozenset(
        {
            "data_points",
            "data_points_count",
            "last_updated",
            "missing_data_points",
            "sensor_update_interval",
        }
    )
    _name_prefix = "Median Filtered Sensor"

    def __init__(self, input_unique_id, sampling_size, sensor_hash, config_entry):
        self._sampling_size = sampling_size
        self._data_points = []
        super().__init__(sensor_hash, config_entry, input_unique_id=input_unique_id)

    def _update_settings(self):
        """Fetch updated settings from config_entry options."""
        # Older entries stored the window as a float from the number selector
        self._sampling_size = int(
            get_config_value(
                self._config_entry, "median_sampling_size", DEFAULT_MEDIAN_SIZE
            )
        )
        _LOGGER.debug("Updated Median settings: sampling_size=%s", self._sampling_size)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data_points_count = len(self._data_points)
        return {
            "data_points": self._data_points,
            "data_points_count": data_points_count,
            "input_entity_id": self._input_entity_id,
            "input_unique_id": self._input_unique_id,
            "last_updated": self._last_updated,
            "median_sampling_size": self._sampling_size,
            "missing_data_points": max(0, self._sampling_size - data_points_count),
            "sensor_hash": self._sensor_hash,
            "sensor_update_interval": self._update_interval,
            "type": "moving_median",
            "unique_id": self.unique_id,
        }

    def _apply(self, input_value):
        """Add the value to the window. The output stays until the window is full."""
        median, self._data_points = median_filter(
            self._data_points, input_value, self._sampling_size
        )
        if median is not None:
            self._state = median

    def _restore_extra(self, old_state):
        self._data_points = old_state.attributes.get("data_points", []) or []

    def _reset_extra(self):
        self._data_points = []
