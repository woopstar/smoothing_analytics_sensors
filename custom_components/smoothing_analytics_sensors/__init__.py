import math

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .utils.misc import get_config_value

PLATFORMS: list[Platform] = [Platform.SENSOR]

# Releases before 2.0.0 stored the EMA setting as a window of N samples
LEGACY_EMA_KEY = "ema_smoothing_window"
EMA_KEY = "desired_time_to_95"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smoothing Analytics Sensors from a config entry."""
    _async_set_missing_unique_id(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


def _async_set_missing_unique_id(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Give entries created before the duplicate check their unique_id."""
    if entry.unique_id is not None:
        return
    unique_id = entry.data.get("input_entity_uuid") or entry.data["input_sensor"]
    if any(
        other.unique_id == unique_id
        for other in hass.config_entries.async_entries(DOMAIN)
    ):
        return
    hass.config_entries.async_update_entry(entry, unique_id=unique_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries."""
    if entry.version > 2:
        return False

    if entry.version == 1:
        # Version 2 stores the registry id of the input sensor, so a rename of
        # the input keeps the entry working
        data = dict(entry.data)
        registry_entry = er.async_get(hass).async_get(data["input_sensor"])
        if registry_entry is not None:
            data["input_entity_uuid"] = registry_entry.id
        hass.config_entries.async_update_entry(entry, data=data, version=2)

    if entry.version == 2 and entry.minor_version < 2:
        # Minor version 2 converts the pre-2.0.0 EMA window, which every
        # release since 2.0.0 has ignored in favour of the default
        interval = float(entry.data.get("update_interval") or 1)
        hass.config_entries.async_update_entry(
            entry,
            data=_convert_legacy_ema(entry.data, interval),
            options=_convert_legacy_ema(entry.options, interval),
            minor_version=2,
        )

    return True


def _convert_legacy_ema(settings, update_interval: float) -> dict:
    """Replace a legacy EMA window with the matching time to reach 95 %."""
    settings = dict(settings)
    window = settings.pop(LEGACY_EMA_KEY, None)
    if window is not None and EMA_KEY not in settings:
        settings[EMA_KEY] = legacy_window_to_time_to_95(window, update_interval)
    return settings


def legacy_window_to_time_to_95(window: float, update_interval: float) -> int:
    """Seconds an EMA with alpha = 2 / (N + 1) needs to reach 95 %.

    Clamped to the 10-600 s range of the config flow.
    """
    alpha = 2 / (float(window) + 1)
    if alpha >= 1:
        return 10
    samples = math.log(0.05) / math.log(1 - alpha)
    return max(10, min(600, round(samples * update_interval)))


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply saved options: sync the title, then reload the entry."""
    title = get_config_value(entry, "device_name", entry.title)
    if title != entry.title:
        # A title change calls this listener again, which then reloads
        hass.config_entries.async_update_entry(entry, title=title)
        return
    await hass.config_entries.async_reload(entry.entry_id)
