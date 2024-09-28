import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN

class PowerSmoothingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Power Sensor Smoothing integration."""

    VERSION = 1
    user_input = {}

    def __init__(self):
        """Initialize config flow."""
        self._errors = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        self._errors = {}

        if user_input is None:
            # If no user input, provide default values for the form.
            user_input = {
                "input_sensor": "",  # Default empty entity_id
                "lowpass_time_constant": 15,
                "median_sampling_size": 15,
                "ema_smoothing_window": 300
            }
        else:
            # Validate the input here if necessary
            if not user_input["input_sensor"]:
                self._errors["input_sensor"] = "invalid_sensor"
            else:
                # If no errors, create the entry.
                return self.async_create_entry(
                    title="Power Sensor Smoothing", data=user_input
                )

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):
        """Show the configuration form to the user."""
        schema = vol.Schema({
            vol.Required("input_sensor", default=user_input.get("input_sensor")): cv.entity_id,
            vol.Optional("lowpass_time_constant", default=user_input.get("lowpass_time_constant", 15)): vol.Coerce(int),
            vol.Optional("median_sampling_size", default=user_input.get("median_sampling_size", 15)): vol.Coerce(int),
            vol.Optional("ema_smoothing_window", default=user_input.get("ema_smoothing_window", 300)): vol.Coerce(int),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=self._errors
        )

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Power Sensor Smoothing integration."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.config_entry.title, data=user_input
            )

        return self._show_options_form()

    async def _show_options_form(self):
        """Show the options configuration form."""
        schema = vol.Schema({
            vol.Required("lowpass_time_constant", default=self.config_entry.options.get("lowpass_time_constant", 15)): vol.Coerce(int),
            vol.Required("median_sampling_size", default=self.config_entry.options.get("median_sampling_size", 15)): vol.Coerce(int),
            vol.Required("ema_smoothing_window", default=self.config_entry.options.get("ema_smoothing_window", 300)): vol.Coerce(int),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema
        )
