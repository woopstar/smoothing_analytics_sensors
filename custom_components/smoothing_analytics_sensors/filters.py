"""Pure filter math for the lowpass, median and EMA stages."""

import statistics


def lowpass_filter(current_value, previous_value, time_constant):
    """Apply a lowpass filter to smooth out fast fluctuations"""
    B = 1.0 / time_constant
    A = 1.0 - B

    return A * previous_value + B * current_value


def median_filter(data_points, value, sampling_size):
    """Add a value to the window and return (median or None, new window).

    The median is None until the window holds sampling_size values.
    """
    # Keep only the last `sampling_size` values, also when a restored window
    # is longer than a smaller window set in the options
    new_data_points = [*data_points, value][-int(sampling_size) :]

    median = None
    if len(new_data_points) >= sampling_size:
        median = statistics.median(new_data_points)

    return median, new_data_points


def calculate_alpha(desired_time_to_95, update_interval):
    """Calculate alpha for Exponential Moving Average (EMA) based on smoothing window and update interval."""

    # No time has passed (or the clock went back): keep the previous output
    if update_interval <= 0:
        return 0.0

    # Exact time-based coefficient: after desired_time_to_95 seconds the
    # remaining distance is 5 %, whatever the update rate. Always below 1, so
    # long gaps cannot overshoot.
    return 1.0 - 0.05 ** (update_interval / desired_time_to_95)


def ema_filter(value, previous_value, alpha):
    """Apply Exponential Moving Average (EMA) filter using the given alpha"""
    return alpha * value + (1 - alpha) * previous_value
