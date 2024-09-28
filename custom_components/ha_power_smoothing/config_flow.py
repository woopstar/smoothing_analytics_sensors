import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Default and minimum values for settings
DEFAULT_LOW_PASS = 15
DEFAULT_MEDIAN_SIZE = 15
DEFAULT_EMA_WINDOW = 300
MIN_EMA_WINDOW = 60  # Minimum smoothing window for EMA
MAX_EMA_WINDOW = 3600  # Maximum smoothing window for EMA

def get_config_schema(user_input: dict[str, Any] | None) -> vol.Schema:
    """Return the config schema for user input."""
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
    """Config flow for Power Sensor Smoothing integration."""

    VERSION = 1

    def __init__(self):
        """Initialize config flow."""
        self._errors = {}
        self._data = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow handler."""
        return PowerSmoothingOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the user config flow."""
        self._errors = {}

        if user_input is not None:
            # Validate and create the config entry
            self._data = user_input
            return self.async_create_entry(title="Power Sensor Smoothing", data=self._data)

        # Show the config form
        return self.async_show_form(
            step_id="user",
            data_schema=get_config_schema(user_input or {}),
            errors=self._errors,
        )


class PowerSmoothingOptionsFlow(config_entries.OptionsFlow):
    """Options flow to handle the configuration options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options step."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.config_entry.title, data=user_input
            )

        # Show options form with current values
        return self.async_show_form(
            step_id="init",
            data_schema=get_config_schema(self.config_entry.options),
        )
