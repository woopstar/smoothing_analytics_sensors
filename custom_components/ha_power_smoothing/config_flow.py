import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.core import callback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Standard values
DEFAULT_LOW_PASS = 15
DEFAULT_MEDIAN_SIZE = 15
DEFAULT_EMA_WINDOW = 300
MIN_EMA_WINDOW = 60
MAX_EMA_WINDOW = 3600

# Schema for configuration
def get_config_schema(user_input: dict[str, Any] | None) -> vol.Schema:
    """Return the schema for config."""
    _LOGGER.debug(f"Building schema with user_input: {user_input}")
    return vol.Schema(
        {
            vol.Required(
                "input_sensor", default=user_input.get("input_sensor", "")
            ): cv.entity_id,
            vol.Optional(
                "lowpass_time_constant", default=user_input.get("lowpass_time_constant", DEFAULT_LOW_PASS)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
            vol.Optional(
                "median_sampling_size", default=user_input.get("median_sampling_size", DEFAULT_MEDIAN_SIZE)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
            vol.Optional(
                "ema_smoothing_window", default=user_input.get("ema_smoothing_window", DEFAULT_EMA_WINDOW)
            ): vol.All(vol.Coerce(int), vol.Range(min=MIN_EMA_WINDOW, max=MAX_EMA_WINDOW)),
        }
    )


class PowerSmoothingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Power Sensor Smoothing."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self._data = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return PowerSmoothingOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        """Handle the initial step."""
        _LOGGER.debug(f"Starting user step with input: {user_input}")
        self._errors = {}

        if user_input is not None:
            _LOGGER.debug(f"User input received: {user_input}")
            try:
                # Validate and store data
                self._data = user_input
                return self.async_create_entry(title="Power Sensor Smoothing", data=self._data)
            except Exception as e:
                _LOGGER.error(f"Error during validation: {e}")
                self._errors["base"] = "validation_error"

        # Show the config form
        return self.async_show_form(
            step_id="user",
            data_schema=get_config_schema(user_input or {}),
            errors=self._errors,
        )


class PowerSmoothingOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Power Sensor Smoothing."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        """Handle options step."""
        if user_input is not None:
            _LOGGER.debug(f"Options step input: {user_input}")
            return self.async_create_entry(title=self.config_entry.title, data=user_input)

        # Show options form with current values
        return self.async_show_form(
            step_id="init",
            data_schema=get_config_schema(self.config_entry.options),
        )
