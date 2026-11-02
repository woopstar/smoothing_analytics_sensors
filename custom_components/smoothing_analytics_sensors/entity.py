import logging

from homeassistant.components.sensor import RestoreSensor

from .const import DOMAIN, ICON, NAME
from .utils.misc import get_config_value

_LOGGER = logging.getLogger(__name__)


class SmoothingAnalyticsEntity(RestoreSensor):
    """Base class for Smoothing Analytics Entity (Device)"""

    # Define the attributes of the entity
    _attr_icon = ICON
    _attr_has_entity_name = True

    def __init__(self, config_entry):
        """Initialize the Smoothing Analytics Entity"""
        super().__init__()
        self.config_entry = config_entry

    def set_entity_id(self, platform_str, key):
        """Set the entity id"""
        entity_id = f"{platform_str}.{DOMAIN}_{key}"
        _LOGGER.debug("entity_id = %s", entity_id)
        self.entity_id = entity_id

    @property
    def device_info(self):
        """Return the device information"""
        if not self.config_entry:
            _LOGGER.warning("Config entry is missing for this entity.")
            return None

        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": get_config_value(self.config_entry, "device_name", NAME),
            "manufacturer": NAME,
        }
