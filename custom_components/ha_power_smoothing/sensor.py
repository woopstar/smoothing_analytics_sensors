import uuid
from homeassistant.helpers.entity import Entity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    input_sensor = entry.data["input_sensor"]
    lowpass_time_constant = entry.options.get("lowpass_time_constant", 15)
    median_sampling_size = entry.options.get("median_sampling_size", 15)
    ema_smoothing_window = entry.options.get("ema_smoothing_window", 300)

    async_add_entities([
        LowpassSensor(input_sensor, lowpass_time_constant),
        MedianSensor(input_sensor, median_sampling_size),
        EmaSensor(input_sensor, ema_smoothing_window)
    ])

class LowpassSensor(Entity):
    def __init__(self, input_sensor, time_constant):
        self._input_sensor = input_sensor
        self._time_constant = time_constant
        self._state = None
        self._unique_id = str(uuid.uuid4())

    @property
    def name(self):
        return f"Lowpass Filtered {self._input_sensor}"

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state

    async def async_update(self):
        input_state = self.hass.states.get(self._input_sensor).state
        # Lowpass filter logic here
        self._state = lowpass_filter(input_state, self._time_constant)

class MedianSensor(Entity):
    def __init__(self, input_sensor, sampling_size):
        self._input_sensor = input_sensor
        self._sampling_size = sampling_size
        self._state = None
        self._unique_id = str(uuid.uuid4())

    @property
    def name(self):
        return f"Median Filtered {self._input_sensor}"

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state

    async def async_update(self):
        input_state = self.hass.states.get(self._input_sensor).state
        # Median filter logic here
        self._state = median_filter(input_state, self._sampling_size)

class EmaSensor(Entity):
    def __init__(self, input_sensor, smoothing_window):
        self._input_sensor = input_sensor
        self._smoothing_window = smoothing_window
        self._state = None
        self._unique_id = str(uuid.uuid4())

    @property
    def name(self):
        return f"EMA Filtered {self._input_sensor}"

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state

    async def async_update(self):
        input_state = self.hass.states.get(self._input_sensor).state
        # EMA filter logic here
        self._state = ema_filter(input_state, self._smoothing_window)
