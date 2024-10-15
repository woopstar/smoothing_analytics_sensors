# Smoothing Analytics Sensors

[![Current Release](https://img.shields.io/github/release/woopstar/smoothing_analytics_sensors/all.svg?style=plastic)](https://github.com/woopstar/smoothing_analytics_sensors/releases) [![Github All Releases](https://img.shields.io/github/downloads/woopstar/smoothing_analytics_sensors/total.svg?style=plastic)](https://github.com/woopstar/smoothing_analytics_sensors/releases)

![Smoothing Analytics Sensors](assets/icon.png)

The **Smoothing Analytics Sensors** integration is designed to smooth out short-term data spikes from any input sensor. It works by applying a series of filters (lowpass, moving median, and EMA) to the raw sensor data, ensuring that brief but significant changes do not heavily impact the final sensor reading.

## Derived from the Huawei Solar Battery Optimization Project

This integration was inspired by and derived from the [Huawei Solar Battery Optimization Project](https://github.com/heinoskov/huawei-solar-battery-optimizations), which was developed to optimize battery usage and maximize self-consumption in solar systems. While that project focuses on managing Huawei solar batteries, this integration adapts the smoothing techniques from it to handle any type of fluctuating sensor data, whether related to energy or other measurements.

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

### Why an SMA Sensor was not used

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
- **Alpha Calculation**: Alpha is calculated using the following formula:

  ```yaml
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
- **EMA Desired Time to Reach 95% (seconds)**: Defines the time for the EMA sensor to reach 95% of the value from the input sensor EMA (default: 120 seconds).

The EMA Desired Time to Reach 95% (seconds) parameter specifies how long it takes for the Exponential Moving Average (EMA) sensor to adjust and reach 95% of the input sensor’s value, based on the changes in input data. The default value of 120 seconds means that the EMA sensor will smooth the data in a way that it will adjust to 95% of the input sensor’s value within 120 seconds.

This time is influenced by the update interval of the input sensor, and the formula we use for calculating the smoothing factor (alpha) ensures that within the desired time (e.g., 120 seconds), the EMA sensor will have captured 95% of the input sensor’s value.

---

### Visualizing the Filters

Below is a conceptual visualization of how the filters work on real-world data:

1. **Raw Data:** Highly fluctuating sensor readings, such as spikes from appliance usage.
2. **Lowpass Filtered Data:** Short-term fluctuations are removed, but some outliers may remain.
3. **Moving Median Filtered Data:** Outliers are smoothed out, leaving a more stable trend.
4. **EMA Filtered Data:** The final smooth output, which reacts faster to real trends while ignoring short-term noise.

By applying these filters in a stack, the integration progressively cleans up the data and delivers a smoother and more actionable sensor reading.

![Visualization of Raw Data, Lowpass, Median, and EMA Filters](assets/visualization.png)

1. **Raw Data** (gray, dashed line): This is the highly fluctuating input, including spikes and noise.
2. **Lowpass Filtered Data** (blue): The first filter smooths out short-term fluctuations but some outliers remain.
3. **Moving Median Filtered Data** (orange): This filter eliminates extreme outliers, creating a more stable trend.
4. **EMA Filtered Data** (green): The final output is very smooth, reacting to long-term trends while ignoring short-term noise.

The following python code was used to create the visualization:

```python
import numpy as np
import matplotlib.pyplot as plt

# Create synthetic raw data with fluctuations and spikes
np.random.seed(0)
time = np.arange(0, 100, 1)
raw_data = np.sin(time * 0.2) + np.random.normal(0, 0.5, len(time)) + (np.random.choice([0, 3], size=len(time), p=[0.95, 0.05]))

# Apply Lowpass Filter
 def lowpass_filter(data, time_constant=15):
     filtered_data = np.zeros_like(data)
     filtered_data[0] = data[0]

     # Calculate coefficients A and B based on the time constant
     B = 1.0 / time_constant
     A = 1.0 - B

     # Apply lowpass filter across the dataset
     for t in range(1, len(data)):
         filtered_data[t] = A * filtered_data[t - 1] + B * data[t]

     return filtered_data

 lowpass_data = lowpass_filter(raw_data)

# Apply Moving Median Filter
def moving_median_filter(data, window_size=15):
    filtered_data = np.zeros_like(data)
    for t in range(len(data)):
        filtered_data[t] = np.median(data[max(0, t - window_size + 1):t + 1])
    return filtered_data

median_data = moving_median_filter(lowpass_data, window_size=5)

# Apply EMA Filter
def ema_filter(data, alpha=0.1):
    ema_data = np.zeros_like(data)
    ema_data[0] = data[0]
    for t in range(1, len(data)):
        ema_data[t] = alpha * data[t] + (1 - alpha) * ema_data[t - 1]
    return ema_data

ema_data = ema_filter(median_data, alpha=0.1)

# Plotting the results
plt.figure(figsize=(10, 6))
plt.plot(time, raw_data, label="Raw Data", color="grey", alpha=0.7, linestyle="--")
plt.plot(time, lowpass_data, label="Lowpass Filtered Data", color="blue", linewidth=1.5)
plt.plot(time, median_data, label="Moving Median Filtered Data", color="orange", linewidth=1.5)
plt.plot(time, ema_data, label="EMA Filtered Data", color="green", linewidth=2)

plt.title("Visualization of Raw Data, Lowpass, Median, and EMA Filters")
plt.xlabel("Time")
plt.ylabel("Sensor Value")
plt.legend()
plt.grid(True)
plt.tight_layout()

# Show the plot
plt.show()
```

---

**Smoothing Analytics Sensors** provides a flexible, reliable way to smooth data, making it especially useful for real-time monitoring environments. The combination of lowpass, median, and exponential moving average filtering ensures that both short-term fluctuations and long-term trends are accurately tracked.
