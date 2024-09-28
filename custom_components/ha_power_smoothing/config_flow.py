import logging
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import selector
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class PowerSmoothingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Power Sensor Smoothing."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        _LOGGER.debug(f"Starting user step with input: {user_input}")
        self._errors = {}

        if user_input is not None:
            # Opret konfigurationsindgang uden brug af voluptuous
            return self.async_create_entry(title="Power Sensor Smoothing", data=user_input)

        # Brug Home Assistant selectors i stedet for voluptuous
        data_schema = {
            "input_sensor": selector({"entity": {"domain": "sensor"}}),
            "lowpass_time_constant": selector({"number": {"min": 1, "max": 60, "unit_of_measurement": "s"}}),
            "median_sampling_size": selector({"number": {"min": 1, "max": 60, "unit_of_measurement": "samples"}}),
            "ema_smoothing_window": selector({"number": {"min": 60, "max": 3600, "unit_of_measurement": "s"}}),
        }

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=self._errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return PowerSmoothingOptionsFlow(config_entry)


class PowerSmoothingOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Power Sensor Smoothing."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options step."""
        if user_input is not None:
            # Opret options-indgang uden brug af voluptuous
            return self.async_create_entry(title=self.config_entry.title, data=user_input)

        # Brug Home Assistant selectors for options
        data_schema = {
            "lowpass_time_constant": selector({"number": {"min": 1, "max": 60, "unit_of_measurement": "s"}}),
            "median_sampling_size": selector({"number": {"min": 1, "max": 60, "unit_of_measurement": "samples"}}),
            "ema_smoothing_window": selector({"number": {"min": 60, "max": 3600, "unit_of_measurement": "s"}}),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
