"""EMA stage: exponential moving average over the median values."""

import logging

from ..const import DEFAULT_EMA_DESIRED_TIME_TO_95
from ..entity import SmoothingAnalyticsSensor
from ..filters import calculate_alpha, ema_filter
from ..utils.misc import get_config_value

_LOGGER = logging.getLogger(__name__)


class EmaSensor(SmoothingAnalyticsSensor):
    """Exponential Moving Average (EMA) filtered sensor with persistent state and device support, based on unique_id."""

    _type = "ema"
    # Fast-changing attributes stay out of the database
    _unrecorded_attributes = frozenset(
        {
            "alpha",
            "last_updated",
            "number_of_updates_needed",
            "previous_value",
            "sensor_update_interval",
        }
    )

    def __init__(self, input_unique_id, desired_time_to_95, sensor_hash, config_entry):
        self._desired_time_to_95 = desired_time_to_95
        self._previous_value = None
        super().__init__(sensor_hash, config_entry, input_unique_id=input_unique_id)

    def _update_settings(self):
        """Fetch updated settings and recalculate alpha from the last update interval."""
        self._desired_time_to_95 = get_config_value(
            self._config_entry, "desired_time_to_95", DEFAULT_EMA_DESIRED_TIME_TO_95
        )
        self._alpha = calculate_alpha(self._desired_time_to_95, self._update_interval)
        _LOGGER.debug(
            "Updated EMA settings: desired_time_to_95=%s, update_interval=%s, alpha=%s",
            self._desired_time_to_95,
            self._update_interval,
            self._alpha,
        )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "alpha": self._alpha,
            "desired_time_to_95": self._desired_time_to_95,
            "input_entity_id": self._input_entity_id,
            "input_unique_id": self._input_unique_id,
            "last_updated": self._last_updated,
            "number_of_updates_needed": self._desired_time_to_95
            / self._update_interval,
            "previous_value": self._previous_value,
            "sensor_hash": self._sensor_hash,
            "sensor_update_interval": self._update_interval,
            "type": "ema",
            "unique_id": self.unique_id,
        }

    def _apply(self, input_value):
        """Blend the input with alpha, or pass the first value through."""
        self._previous_value = self._state
        if self._previous_value is not None:
            self._state = ema_filter(input_value, self._previous_value, self._alpha)
        else:
            self._state = input_value

    def _restore_extra(self, old_state):
        self._previous_value = float(self._state)

    def _reset_extra(self):
        self._previous_value = None
