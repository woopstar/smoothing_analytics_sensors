# Smoothing Analytics Sensors

The **Smoothing Analytics Sensors** integration is designed to smooth out short-term data spikes from any input sensor. It works by applying a series of filters (lowpass, moving median, and EMA) to the raw sensor data, ensuring that brief but significant changes do not heavily impact the final sensor reading.

## Derived from the Huawei Solar Battery Optimization Project

This integration was inspired by and derived from the [Huawei Solar Battery Optimization Project](https://github.com/heinoskov/huawei_solar_battery_optimization), which was developed to optimize battery usage and maximize self-consumption in solar systems. While that project focuses on managing Huawei solar batteries, this integration adapts the smoothing techniques from it to handle any type of fluctuating sensor data, whether related to energy or other measurements.

---

## Sensor Stacking

The sensors in this integration work in a sequential stack, where each filter is applied to the result of the previous one:
1. **Lowpass Filter**: First, applied to the raw sensor data.
2. **Moving Median Filter**: Then, applied to the lowpass-filtered data.
3. **EMA (Exponential Moving Average) Filter**: Finally, applied to the median-filtered data.

This approach ensures that each filter progressively smooths out noise, short-term fluctuations, and outliers from the data.

### Available Sensors

This integration provides three main sensor types:
1. **Lowpass filter sensor** – applied directly to the raw input data.
2. **Moving median sensor** – applied to the lowpass-filtered data.
3. **EMA (Exponential Moving Average) sensor** – applied to the median-filtered data.

---

### Why an SMA Sensor Was Not Used

- An **SMA (Simple Moving Average)** sensor averages a set number of recent data points in a fixed window. While it smooths data, it gives equal weight to all points in the window.
- The SMA sensor was not chosen for this integration because it reacts slower to trends compared to the EMA and lacks the spike-handling robustness of the moving median filter.
- The EMA sensor was chosen instead because it gives more weight to recent data, making it more responsive to changes in real-world data such as power consumption, temperature, or other sensor data.

---

### Summary

The **EMA sensor** was preferred for this setup because it responds quickly to data trends, giving more importance to recent points. Together with the **lowpass filter** and **moving median**, it forms a reliable solution for smoothing out data spikes while preserving long-term trends.

---

### Strategy

1. **Lowpass Filter**: Applies first to the raw sensor data to remove rapid fluctuations or spikes.
2. **Moving Median Filter**: Further smooths the lowpass-filtered data to handle remaining extreme outliers.
3. **EMA Sensor**: Final smoothing step using an Exponential Moving Average to prioritize recent data points and track long-term trends.

---

### Key Parameters

- **Lowpass Filter**: The default time constant is 15 seconds to smooth out fast fluctuations.
- **Moving Median**: The default window size is 15 data points to filter extreme outliers.
- **EMA**: The default smoothing window is 300 seconds (5 minutes), ensuring only sustained changes affect the sensor readings.

---

## Sensor Explanations

### 1. Lowpass Filtered Sensor

The lowpass filter is applied to the raw sensor data and is used to remove short-term spikes and fluctuations. The time constant controls how quickly it reacts to changes.

- **Purpose**: Smooths out rapid spikes from the raw data.
- **Time Constant**: 15 seconds. A higher value smooths more but reacts slower.
- **Rationale**: A 15-second time constant is ideal for handling short spikes from appliances while responding to longer-term changes.

---

### 2. Moving Median Filtered Sensor

The moving median filter is applied to the lowpass-filtered data to remove any remaining outliers. The median is more resistant to extreme values than the mean, making it effective for eliminating short-term spikes.

- **Purpose**: Removes extreme outliers in the lowpass-filtered data.
- **Sampling Size**: 15 data points. The median of the last 15 points is calculated.
- **Rationale**: Prevents extreme spikes from heavily influencing the final reading.

---

### 3. EMA (Exponential Moving Average) Filtered Sensor

The final smoothing step applies an Exponential Moving Average to the median-filtered data. This gives more weight to recent data points, making the sensor responsive to long-term trends while filtering out short-term noise.

- **Purpose**: Applies final smoothing, focusing on recent data trends.
- **Smoothing Window**: 300 seconds (5 minutes).
- **Alpha Calculation**:
  Alpha is calculated using the following formula:
  ```
  alpha = 2 / (smoothing_window_seconds + 1)
  ```

- **Rationale**: Ensures the sensor reacts slowly to spikes while capturing long-term trends.

---

## Installation

### Method 1: HACS (Home Assistant Community Store)
1. In HACS, go to **Integrations**.
2. Click the three dots in the top-right corner, and select **Custom repositories**.
3. Add this repository URL and select **Integration** as the category:
   `https://github.com/woopstar/smoothing_analytics_sensors`
4. Click **Add**.
5. The integration will now appear in HACS under the **Integrations** section. Click **Install**.
6. Restart Home Assistant.

---

### Method 2: Manual Installation

1. Copy the `smoothing_analytics_sensors` folder to your `custom_components` folder in your Home Assistant configuration.
2. Restart Home Assistant.
3. Add the integration via the Home Assistant integrations page and configure your settings.

---

### Configuration

In the configuration flow, you can customize:
- **Input Sensor**: The raw sensor to be smoothed.
- **Lowpass Time Constant**: Controls how quickly the lowpass filter smooths data (default: 15 seconds).
- **Median Sampling Size**: Defines how many data points are used for the median calculation (default: 15).
- **EMA Smoothing Window**: Defines the window for calculating the EMA (default: 300 seconds).
- **Update Interval**: Defines how often the sensor updates (default: 5 seconds).

---

### Conclusion

**Smoothing Analytics Sensors** provides a flexible, reliable way to smooth data, making it especially useful for real-time monitoring environments. The combination of lowpass, median, and exponential moving average filtering ensures that both short-term fluctuations and long-term trends are accurately tracked.
