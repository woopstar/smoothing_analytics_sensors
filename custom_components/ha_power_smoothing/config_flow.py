from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import selector
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
            # Default values for the form
            user_input = {
                "input_sensor": "",
                "lowpass_time_constant": 15,
                "median_sampling_size": 15,
                "ema_smoothing_window": 300
            }
        else:
            # Basic validation
            if not user_input["input_sensor"]:
                self._errors["input_sensor"] = "invalid_sensor"
            else:
                # Create the entry with validated input
                return self.async_create_entry(
                    title="Power Sensor Smoothing", data=user_input
                )

        return self._show_config_form(user_input)

    def _show_config_form(self, user_input):
        """Show the configuration form to the user."""
        data_schema = {
            "input_sensor": selector({
                "entity": {"domain": "sensor"}
            }),
            "lowpass_time_constant": selector({
                "number": {
                    "min": 1,
                    "max": 60,
                    "unit_of_measurement": "s",
                    "mode": "box",
                    "step": 1
                }
            }),
            "median_sampling_size": selector({
                "number": {
                    "min": 1,
                    "max": 60,
                    "unit_of_measurement": "samples",
                    "mode": "box",
                    "step": 1
                }
            }),
            "ema_smoothing_window": selector({
                "number": {
                    "min": 60,
                    "max": 3600,
                    "unit_of_measurement": "s",
                    "mode": "box",
                    "step": 60
                }
            })
        }

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_defaults_to_schema(data_schema, user_input),
            errors=self._errors
        )

    def add_defaults_to_schema(self, schema, user_input):
        """Helper method to add default values to the schema."""
        for key, value in user_input.items():
            schema[key]["default"] = value
        return schema


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

    def _show_options_form(self):
        """Show the options configuration form."""
        data_schema = {
            "lowpass_time_constant": selector({
                "number": {
                    "min": 1,
                    "max": 60,
                    "unit_of_measurement": "s",
                    "mode": "box",
                    "step": 1
                }
            }),
            "median_sampling_size": selector({
                "number": {
                    "min": 1,
                    "max": 60,
                    "unit_of_measurement": "samples",
                    "mode": "box",
                    "step": 1
                }
            }),
            "ema_smoothing_window": selector({
                "number": {
                    "min": 60,
                    "max": 3600,
                    "unit_of_measurement": "s",
                    "mode": "box",
                    "step": 60
                }
            })
        }

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_defaults_to_schema(data_schema, self.config_entry.options)
        )
