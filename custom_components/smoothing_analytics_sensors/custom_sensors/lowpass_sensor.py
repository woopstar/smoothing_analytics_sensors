"""Lowpass stage: first-order lowpass on the raw input sensor."""

import logging

from ..const import DEFAULT_LOW_PASS
from ..entity import SmoothingAnalyticsSensor
from ..filters import lowpass_filter
from ..utils.misc import get_config_value

_LOGGER = logging.getLogger(__name__)


class LowpassSensor(SmoothingAnalyticsSensor):
    """Lowpass filtered sensor with persistent state, precision of 2 decimal places, and device support."""

    _type = "lowpass"
    # Fast-changing attributes stay out of the database
    _unrecorded_attributes = frozenset(
        {"last_updated", "previous_value", "sensor_update_interval"}
    )

    def __init__(self, input_sensor, time_constant, sensor_hash, config_entry):
        self._time_constant = time_constant
        self._previous_value = None
        super().__init__(sensor_hash, config_entry, input_entity_id=input_sensor)

    def _update_settings(self):
        """Fetch updated settings from config_entry options."""
        self._time_constant = get_config_value(
            self._config_entry, "lowpass_time_constant", DEFAULT_LOW_PASS
        )
        _LOGGER.debug("Updated Lowpass settings: time_constant=%s", self._time_constant)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "input_sensor": self._input_entity_id,
            "last_updated": self._last_updated,
            "lowpass_time_constant": self._time_constant,
            "previous_value": self._previous_value,
            "sensor_hash": self._sensor_hash,
            "sensor_update_interval": self._update_interval,
            "type": "lowpass",
            "unique_id": self.unique_id,
        }

    def _apply(self, input_value):
        """Blend the input into the previous output, or pass the first value through."""
        self._previous_value = self._state
        if self._previous_value is not None:
            self._state = lowpass_filter(
                input_value,
                self._previous_value,
                self._time_constant,
                self._update_interval,
            )
        else:
            self._state = input_value

    def _restore_extra(self, old_state):
        self._previous_value = float(self._state)

    def _reset_extra(self):
        self._previous_value = None
