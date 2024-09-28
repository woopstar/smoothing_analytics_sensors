import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN

class PowerSmoothingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Power Sensor Smoothing", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("input_sensor"): cv.entity_id,
                vol.Optional("lowpass_time_constant", default=15): vol.Coerce(int),
                vol.Optional("median_sampling_size", default=15): vol.Coerce(int),
                vol.Optional("ema_smoothing_window", default=300): vol.Coerce(int)
            }),
            errors=errors
        )
