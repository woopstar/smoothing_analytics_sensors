"""Shared base sensor: input, restore, subscription and device info."""

import logging

from homeassistant.components.sensor import (
    DEVICE_CLASS_STATE_CLASSES,
    RestoreSensor,
    SensorStateClass,
)
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    async_track_entity_registry_updated_event,
    async_track_state_change_event,
)
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
    # A smoothed value is always a measurement, also for a meter input
    _attr_state_class = SensorStateClass.MEASUREMENT
    # Full precision internally, 2 decimals in the UI. Rounding inside the
    # recursion would lock small inputs at 0.
    _attr_suggested_display_precision = 2

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
        self._update_interval = 1
        self._unsub_input = []
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

    def diagnostics(self):
        """Return the internal state for config entry diagnostics."""
        return {
            "entity_id": self.entity_id,
            "unique_id": self.unique_id,
            "available": self.available,
            "value": self._state,
            "input_entity_id": self._input_entity_id,
            "input_unique_id": self._input_unique_id,
            "last_updated": self._last_updated,
            "update_interval": self._update_interval,
            "unit_of_measurement": self._unit_of_measurement,
            "device_class": self._device_class,
            "attributes": self.extra_state_attributes,
        }

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
            _LOGGER.debug(
                "Entity with unique_id %s not found in registry",
                self._input_unique_id,
            )
        return self._input_entity_id

    def _set_available(self, available):
        """Follow the input's availability. Log only on a transition."""
        if available == self._attr_available:
            return False
        self._attr_available = available
        _LOGGER.debug(
            "%s is %s", self.unique_id, "available" if available else "unavailable"
        )
        return True

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
            _LOGGER.debug(
                "Sensor %s not found. Skipping %s update", input_entity_id, self._type
            )
            return

        # Unavailable input makes this stage unavailable, which the next stage
        # follows. Unknown (for example a median whose window is not full yet)
        # is skipped and keeps the last value.
        if input_state.state == STATE_UNAVAILABLE:
            if self._set_available(False):
                self.async_write_ha_state()
            return
        if input_state.state == STATE_UNKNOWN:
            _LOGGER.debug("Input %s is unknown. Skipping update", input_entity_id)
            return

        try:
            input_value = float(input_state.state)
        except ValueError:
            _LOGGER.warning(
                "Invalid value from %s: %s", input_entity_id, input_state.state
            )
            return

        # Follow unit and device class of the input. A device class that does
        # not allow a measurement (energy, gas, water, ...) is dropped.
        self._unit_of_measurement = input_state.attributes.get("unit_of_measurement")
        device_class = input_state.attributes.get("device_class")
        allowed = DEVICE_CLASS_STATE_CLASSES.get(device_class)
        if allowed is not None and SensorStateClass.MEASUREMENT not in allowed:
            _LOGGER.debug(
                "Input %s has device class %s, which allows no measurement. "
                "Publishing %s without a device class",
                input_entity_id,
                device_class,
                self.unique_id,
            )
            device_class = None
        self._device_class = device_class

        self._set_available(True)
        self._apply(input_value)

        self._last_updated = now.isoformat()
        self.async_write_ha_state()

    @callback
    def _async_track_input(self, entity_id):
        """Listen to state changes and renames of the input."""
        self._async_untrack_input()
        _LOGGER.debug("Starting to track state changes for entity_id %s", entity_id)
        self._unsub_input = [
            async_track_state_change_event(self.hass, [entity_id], self._handle_update),
            async_track_entity_registry_updated_event(
                self.hass, entity_id, self._async_input_registry_updated
            ),
        ]

    @callback
    def _async_untrack_input(self):
        """Stop listening to the input."""
        while self._unsub_input:
            self._unsub_input.pop()()

    @callback
    def _async_input_registry_updated(self, event):
        """Follow the input to its new entity_id after a rename."""
        data = event.data
        if data["action"] != "update" or "old_entity_id" not in data:
            return
        _LOGGER.debug(
            "Input of %s renamed from %s to %s",
            self.unique_id,
            data["old_entity_id"],
            data["entity_id"],
        )
        self._input_entity_id = data["entity_id"]
        self._async_track_input(self._input_entity_id)
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Restore the last state and start listening to the input."""
        old_state = await self.async_get_last_state()

        if old_state is not None:
            _LOGGER.debug("Restoring state for %s", self.unique_id)
            try:
                self._state = float(old_state.state)
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
            _LOGGER.debug(
                "No previous state found for %s, starting fresh", self.unique_id
            )

        input_entity_id = self._resolve_input_entity_id()
        if not input_entity_id:
            _LOGGER.warning(
                "No input for %s. Unable to track state changes", self.unique_id
            )
            return

        self._async_track_input(input_entity_id)
        self.async_on_remove(self._async_untrack_input)

        # Start unavailable if the input already is
        input_state = self.hass.states.get(input_entity_id)
        if input_state is not None and input_state.state == STATE_UNAVAILABLE:
            self._attr_available = False
