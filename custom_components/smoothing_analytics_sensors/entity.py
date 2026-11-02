"""Shared base sensor: input, restore, subscription and device info."""

import logging

from homeassistant.components.sensor import RestoreSensor
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import DOMAIN, ICON, NAME
from .utils.misc import get_config_value

_LOGGER = logging.getLogger(__name__)


class SmoothingAnalyticsSensor(RestoreSensor):
    """Base class for one stage of the smoothing stack.

    Subclasses set `_type` and `_name_prefix` and implement `_apply`. The input
    is either a fixed entity_id (lowpass) or the unique_id of the upstream SAS
    stage, resolved through the entity registry (median, EMA).
    """

    _attr_icon = ICON
    _attr_has_entity_name = True
    # Event-driven: a stage only updates when its upstream changes state
    _attr_should_poll = False

    _type: str
    _name_prefix: str

    def __init__(
        self,
        sensor_hash,
        config_entry,
        input_entity_id=None,
        input_unique_id=None,
    ):
        """Initialize the stage."""
        super().__init__()
        self.config_entry = config_entry
        self._config_entry = config_entry
        self._sensor_hash = sensor_hash
        self._input_entity_id = input_entity_id
        self._input_unique_id = input_unique_id
        self._attr_unique_id = f"sas_{self._type}_{sensor_hash}"
        self._state = None
        self._last_updated = None
        self._unit_of_measurement = None
        self._device_class = None
        self._state_class = None
        self._update_interval = 1
        self._update_settings()

    def _update_settings(self):
        """Fetch updated settings from the config entry."""

    def _apply(self, input_value):
        """Feed one input value into the filter and update `self._state`."""
        raise NotImplementedError

    def _restore_extra(self, old_state):
        """Restore stage-specific values after the state was restored."""

    def _reset_extra(self):
        """Reset stage-specific values when the restored state is invalid."""

    @property
    def name(self):
        return f"{self._name_prefix} {self._sensor_hash}"

    @property
    def native_value(self):
        return self._state

    @property
    def native_unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def device_class(self):
        return self._device_class

    @property
    def state_class(self):
        return self._state_class

    @property
    def device_info(self):
        """Return the device information"""
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": get_config_value(self.config_entry, "device_name", NAME),
            "manufacturer": NAME,
        }

    def _resolve_input_entity_id(self):
        """Resolve the upstream entity_id from its unique_id if not known yet."""
        if self._input_entity_id or not self._input_unique_id:
            return self._input_entity_id

        entity_id = er.async_get(self.hass).async_get_entity_id(
            "sensor", DOMAIN, self._input_unique_id
        )
        if entity_id:
            self._input_entity_id = entity_id
            _LOGGER.debug(
                "Resolved entity_id for unique_id %s: %s",
                self._input_unique_id,
                entity_id,
            )
        else:
            _LOGGER.warning(
                "Entity with unique_id %s not found in registry",
                self._input_unique_id,
            )
        return self._input_entity_id

    async def _handle_update(self, event):
        """Handle the sensor state update (for both manual and state change)."""
        now = dt_util.utcnow()

        # Calculate the update interval to be used. UTC has no DST jumps.
        # Older versions stored naive local timestamps; as_utc reads those as
        # Home Assistant's time zone.
        last_updated = (
            dt_util.parse_datetime(self._last_updated) if self._last_updated else None
        )
        if last_updated is not None:
            self._update_interval = (now - dt_util.as_utc(last_updated)).total_seconds()

        # Ensure settings are reloaded if config is changed
        self._update_settings()

        input_entity_id = self._resolve_input_entity_id()
        if not input_entity_id:
            return

        input_state = self.hass.states.get(input_entity_id)
        if input_state is None:
            _LOGGER.warning(
                "Sensor %s not found. Skipping %s update", input_entity_id, self._type
            )
            return
        try:
            input_value = float(input_state.state)
        except ValueError:
            _LOGGER.warning(
                "Invalid value from %s: %s", input_entity_id, input_state.state
            )
            return

        # Follow unit, device class and state class of the input
        self._unit_of_measurement = input_state.attributes.get("unit_of_measurement")
        self._device_class = input_state.attributes.get("device_class")
        self._state_class = input_state.attributes.get("state_class")

        self._apply(input_value)

        self._last_updated = now.isoformat()
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Restore the last state and start listening to the input."""
        old_state = await self.async_get_last_state()

        if old_state is not None:
            _LOGGER.info("Restoring state for %s", self.unique_id)
            try:
                self._state = round(float(old_state.state), 2)
                self._restore_extra(old_state)
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Could not restore state for %s, invalid value: %s",
                    self.unique_id,
                    old_state.state,
                )
                self._state = None
                self._reset_extra()

            self._last_updated = old_state.attributes.get("last_updated", None)
            self._update_interval = old_state.attributes.get(
                "sensor_update_interval", 1
            )
            # Recalculate derived settings (EMA alpha) from the restored interval
            self._update_settings()
        else:
            _LOGGER.info(
                "No previous state found for %s, starting fresh", self.unique_id
            )

        input_entity_id = self._resolve_input_entity_id()
        if not input_entity_id:
            _LOGGER.warning(
                "No input for %s. Unable to track state changes", self.unique_id
            )
            return

        _LOGGER.info(
            "Starting to track state changes for entity_id %s", input_entity_id
        )
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [input_entity_id], self._handle_update
            )
        )
