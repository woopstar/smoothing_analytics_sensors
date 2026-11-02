from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .utils.misc import get_config_value

PLATFORMS: list[Platform] = [Platform.SENSOR]


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

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply saved options: sync the title, then reload the entry."""
    title = get_config_value(entry, "device_name", entry.title)
    if title != entry.title:
        # A title change calls this listener again, which then reloads
        hass.config_entries.async_update_entry(entry, title=title)
        return
    await hass.config_entries.async_reload(entry.entry_id)
