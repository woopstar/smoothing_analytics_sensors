import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import selector

from .const import (
    DEFAULT_EMA_DESIRED_TIME_TO_95,
    DEFAULT_LOW_PASS,
    DEFAULT_MEDIAN_SIZE,
    DOMAIN,
    NAME,
)
from .utils.misc import get_config_value

_LOGGER = logging.getLogger(__name__)


class SmoothingAnalyticsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Smoothing Analytics Sensors."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        # If user_input is not None, the user has submitted the form
        if user_input is not None:
            if not _is_numeric_sensor(self.hass, user_input["input_sensor"]):
                errors["input_sensor"] = "invalid_sensor"
            else:
                # Remember the registry id so the input can be renamed later
                data = _normalize(user_input)
                entry = er.async_get(self.hass).async_get(data["input_sensor"])
                if entry is not None:
                    data["input_entity_uuid"] = entry.id

                # One entry per input sensor. The unique_id is the registry id
                # when there is one, so a renamed input is still recognized.
                # Entries created before this check have no unique_id and are
                # matched on their data.
                await self.async_set_unique_id(
                    data.get("input_entity_uuid") or data["input_sensor"]
                )
                self._abort_if_unique_id_configured()
                self._async_abort_entries_match({"input_sensor": data["input_sensor"]})

                # Create the configuration with device_name as title
                return self.async_create_entry(
                    title=user_input.get("device_name", NAME),
                    data=data,
                )

        # Define the form schema
        data_schema = vol.Schema(
            {
                vol.Required("input_sensor"): selector(
                    {"entity": {"domain": "sensor"}}
                ),
                vol.Optional("device_name", default=NAME): str,
                **_filter_schema(
                    {
                        "lowpass_time_constant": DEFAULT_LOW_PASS,
                        "median_sampling_size": DEFAULT_MEDIAN_SIZE,
                        "desired_time_to_95": DEFAULT_EMA_DESIRED_TIME_TO_95,
                    }
                ),
            }
        )

        # Show the form to the user
        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return SmoothingAnalyticsOptionsFlow()


class SmoothingAnalyticsOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Smoothing Analytics Sensors."""

    async def async_step_init(self, user_input=None):
        """Handle options step."""
        if user_input is not None:
            # The update listener syncs the entry title with device_name
            return self.async_create_entry(data=_normalize(user_input))

        # Defaults are the current values: options first, then data
        entry = self.config_entry
        data_schema = vol.Schema(
            {
                vol.Optional(
                    "device_name",
                    default=get_config_value(entry, "device_name", entry.title),
                ): str,
                **_filter_schema(
                    {
                        key: get_config_value(entry, key, default)
                        for key, default in (
                            ("lowpass_time_constant", DEFAULT_LOW_PASS),
                            ("median_sampling_size", DEFAULT_MEDIAN_SIZE),
                            ("desired_time_to_95", DEFAULT_EMA_DESIRED_TIME_TO_95),
                        )
                    }
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)


def _is_numeric_sensor(hass, entity_id):
    """Return True if the sensor exists and has a number, or no value yet."""
    state = hass.states.get(entity_id)
    if state is None:
        return False
    if state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        return True
    try:
        float(state.state)
    except ValueError:
        return False
    return True


def _number(minimum, maximum, unit):
    """Return a number box selector."""
    return selector(
        {
            "number": {
                "min": minimum,
                "max": maximum,
                "step": 1,
                "unit_of_measurement": unit,
                "mode": "box",
            }
        }
    )


def _filter_schema(defaults):
    """Return the filter fields shared by the config and options flow."""
    return {
        vol.Optional(
            "lowpass_time_constant", default=defaults["lowpass_time_constant"]
        ): _number(1, 60, "seconds"),
        vol.Optional(
            "median_sampling_size", default=defaults["median_sampling_size"]
        ): _number(1, 60, "samples"),
        vol.Optional(
            "desired_time_to_95", default=defaults["desired_time_to_95"]
        ): _number(10, 600, "seconds"),
    }


def _normalize(user_input):
    """Store the median window as an int; the number selector returns floats."""
    data = dict(user_input)
    if "median_sampling_size" in data:
        data["median_sampling_size"] = int(data["median_sampling_size"])
    return data
