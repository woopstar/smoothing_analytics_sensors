import logging
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Simpelt skema med kun ét felt
SIMPLE_SCHEMA = vol.Schema(
    {
        vol.Required("input_sensor"): cv.entity_id,  # Kun ét påkrævet felt
    }
)

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
            # Opret konfigurationsindgang uden yderligere validering
            return self.async_create_entry(title="Power Sensor Smoothing", data=user_input)

        # Vis det simple skema
        return self.async_show_form(
            step_id="user",
            data_schema=SIMPLE_SCHEMA,
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
            # Opret options-indgang uden yderligere validering
            return self.async_create_entry(title=self.config_entry.title, data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=SIMPLE_SCHEMA,
        )
