"""Diagnostics for Smoothing Analytics Sensors."""

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return settings and the internal state of each filter stage."""
    sensors = getattr(entry, "runtime_data", None) or []
    return {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "sensors": {sensor._type: sensor.diagnostics() for sensor in sensors},
    }
