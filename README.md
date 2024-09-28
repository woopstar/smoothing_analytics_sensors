# Power Smoothing Integration

The goal of this integration is to smooth out short-term, high-power spikes (such as those caused by vacuum cleaners, coffee machines, ovens, etc.), ensuring that brief but significant power consumption does not heavily impact the final sensor reading. The raw power sensor updates every second.

### Available Sensors

This integration works by combining the following sensors:
1. Raw power sensor (external source)
2. Lowpass filter sensor
3. Moving median sensor
4. EMA (Exponential Moving Average) sensor

### Why an SMA Sensor Was Not Used

- An **SMA (Simple Moving Average)** sensor calculates the average of a set number of recent data points in a fixed window. While this can smooth data, it gives equal weight to all data points in the window.
- We did not use an SMA sensor in this case because it reacts slower to new trends compared to an EMA, and the moving median filter provides better handling of short-term spikes or outliers.
- Unlike the EMA, the SMA doesn't prioritize recent data over older data, which can make it less responsive to changes in power consumption over time. This is important when dealing with fluctuating power usage in a home environment, where rapid response to changes is useful.

### Summary

The EMA sensor was preferred for this setup because it reacts faster to trends and provides more weight to recent data points. Combined with a lowpass filter and moving median, it provides a robust way to smooth short-term power spikes while still capturing long-term trends.

### Strategy

1. **Lowpass Filter**: First, we apply a lowpass filter to the raw data to remove very short, rapid fluctuations (spikes) that may occur from appliances such as a vacuum cleaner.
2. **Moving Median Filter**: Then, we use a moving median filter to further smooth any remaining extreme values, as the median is more resistant to outliers than the mean.
3. **EMA Sensor**: Finally, we apply an Exponential Moving Average (EMA) sensor, which dynamically calculates an exponential moving average. This provides an even smoother result, especially useful for long-term trends, while allowing you to adjust how quickly the sensor responds to changes by setting a smoothing window.

### Structure and Behavior

This structure ensures that short-term fluctuations (e.g., under 5 minutes) have minimal influence on the final sensor reading, while allowing the system to still track long-term changes in power consumption.

### Key Parameters

- **Lowpass Filter**: A time constant of 15 seconds is used to smooth out fast, short-term fluctuations.
- **Moving Median**: A window size of 15 seconds (sampling 15 data points) is used to remove extreme outliers.
- **EMA**: The alpha value is dynamically calculated based on a smoothing window of 5 minutes (300 seconds), meaning that only changes lasting longer than 5 minutes will significantly affect the sensor.

## Sensor Explanations

### 1. Lowpass Filtered Sensor

The lowpass filter is used to remove short-term fluctuations and spikes from the raw data. The time constant determines how quickly the filter responds to changes. A higher time constant makes the sensor respond slower, smoothing the data more. 

- **Purpose**: The lowpass filter removes fast, short-term fluctuations from the raw data.
- **Time Constant**: Set to 15 seconds. This controls how fast the filter reacts to changes. A higher value smooths the data more but delays the sensor's reaction to real changes.
- **Rationale**: A 15-second time constant smooths out short spikes from devices like vacuum cleaners or coffee machines without losing the ability to respond to more prolonged changes.

### 2. Moving Median Filtered Sensor

The moving median filter is used to smooth out any remaining extreme spikes from the lowpass-filtered data. Unlike a moving average, the median is more resistant to outliers, making it effective at removing brief, extreme spikes, such as from a vacuum cleaner or coffee machine.

- **Purpose**: The moving median filter smooths the data by eliminating extreme outliers. It is especially useful after the lowpass filter to handle remaining spikes.
- **Sampling Size**: Set to 15 seconds. The median will be calculated over the last 15 data points.
- **Rationale**: Using the median of the last 15 seconds prevents extreme spikes, such as those caused by short-term events (e.g., a coffee machine), from affecting the overall reading too much.

### 3. Flexible EMA (Exponential Moving Average) Filtered Sensor

The final sensor in the chain applies an Exponential Moving Average (EMA) filter on the median-filtered data. The alpha value determines how quickly the EMA responds to new data. A lower alpha value results in a smoother sensor that reacts slower to changes. This EMA implementation allows dynamic adjustment by using a smoothing window (in seconds).

- **Purpose**: The EMA sensor applies an Exponential Moving Average to smooth the data further. It responds more quickly to longer-term trends than the median filter but remains resistant to short-term spikes.
- **Smoothing Window**: Set to 300 seconds (5 minutes). The EMA will only react to changes that last longer than this period.
- **Alpha Calculation**: The alpha is dynamically calculated using the formula:  
  \[
  \alpha = \frac{2}{\text{smoothing\_window\_seconds} + 1}
  \]
- **Rationale**: A 5-minute window ensures that the sensor reacts slowly to spikes, effectively ignoring short-term peaks. The dynamic alpha calculation makes it easy to adjust the window size to control how responsive the sensor is.

## Installation

1. Copy the `ha_power_smoothing` folder to your `custom_components` folder in your Home Assistant configuration.
2. Restart Home Assistant.
3. Add the integration via the Home Assistant integrations page and configure your settings.

## Configuration

In the configuration flow, you will be able to select the following options:
- **Input Sensor**: The raw power sensor to be smoothed.
- **Lowpass Time Constant**: Defines how quickly the lowpass filter smooths out fluctuations (default: 15 seconds).
- **Median Sampling Size**: Defines how many data points are considered for the median calculation (default: 15).
- **EMA Smoothing Window**: Defines the window for calculating the EMA (default: 300 seconds).

## Conclusion

This integration provides a robust method for smoothing short-term spikes in power consumption while maintaining responsiveness to long-term changes. The combination of lowpass filtering, median filtering, and exponential moving average allows for a flexible, customizable, and reliable solution for power monitoring.
