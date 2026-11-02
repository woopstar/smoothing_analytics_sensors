import hashlib


def generate_md5_hash(input_sensor):
    """Generate an MD5 hash based on the input sensor's name."""
    # Used as an identifier, not for security
    return hashlib.md5(input_sensor.encode("utf-8"), usedforsecurity=False).hexdigest()


def get_config_value(config_entry, key, default_value=None):
    """Get the configuration value from options or fall back to the initial data."""
    return config_entry.options.get(key, config_entry.data.get(key, default_value))
