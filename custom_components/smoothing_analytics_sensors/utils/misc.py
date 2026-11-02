import hashlib

from homeassistant.helpers import entity_registry as er


def generate_md5_hash(input_sensor):
    """Generate an MD5 hash based on the input sensor's name."""
    # Used as an identifier, not for security
    return hashlib.md5(input_sensor.encode("utf-8"), usedforsecurity=False).hexdigest()


def get_config_value(config_entry, key, default_value=None):
    """Get the configuration value from options or fall back to the initial data."""
    return config_entry.options.get(key, config_entry.data.get(key, default_value))


def current_input_sensor(hass, config_entry):
    """Return the input's current entity_id, following renames via its registry id."""
    input_sensor = config_entry.data.get("input_sensor")
    if input_entity_uuid := config_entry.data.get("input_entity_uuid"):
        return (
            er.async_resolve_entity_id(er.async_get(hass), input_entity_uuid)
            or input_sensor
        )
    return input_sensor
