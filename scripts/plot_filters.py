"""Draw assets/visualization.png from the integration's own filter math.

The filters are loaded straight from custom_components/.../filters.py, so the
figure always matches the code. Run with matplotlib available, for example:

    uv run --no-project --with matplotlib python scripts/plot_filters.py
"""

import importlib.util
import math
import random
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
FILTERS = ROOT / "custom_components/smoothing_analytics_sensors/filters.py"
OUTPUT = ROOT / "assets/visualization.png"

# Integration defaults (const.py)
LOWPASS_TIME_CONSTANT = 15
MEDIAN_SAMPLING_SIZE = 15
DESIRED_TIME_TO_95 = 120

DURATION = 900
STEP_START, STEP_END = 300, 600


def load_filters():
    """Import filters.py without importing Home Assistant."""
    spec = importlib.util.spec_from_file_location("sas_filters", FILTERS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def raw_signal():
    """Grid power at 1 s: base load, noise, short appliance spikes and one real step."""
    rng = random.Random(4)
    spikes = set()
    for start in rng.sample(range(10, DURATION - 10), 14):
        spikes.update(range(start, start + rng.choice((1, 2, 3))))
    values = []
    for t in range(DURATION):
        value = 400 + 40 * rng.gauss(0, 1) + 60 * math.sin(t / 40)
        if STEP_START <= t < STEP_END:
            value += 1200
        if t in spikes:
            value += rng.choice((1500, 2000, -350))
        values.append(value)
    return values


def run_stack(filters, raw):
    """Feed the samples through lowpass → median → EMA like the sensors do."""
    lowpass, median, ema = [], [], []
    low = None
    window = []
    med = None
    smooth = None
    for value in raw:
        low = (
            value
            if low is None
            else filters.lowpass_filter(value, low, LOWPASS_TIME_CONSTANT, 1)
        )
        new_median, window = filters.median_filter(window, low, MEDIAN_SAMPLING_SIZE)
        if new_median is not None:
            med = new_median
            alpha = filters.calculate_alpha(DESIRED_TIME_TO_95, 1)
            smooth = med if smooth is None else filters.ema_filter(med, smooth, alpha)
        lowpass.append(low)
        median.append(med if med is not None else math.nan)
        ema.append(smooth if smooth is not None else math.nan)
    return lowpass, median, ema


def main():
    """Draw and save the figure."""
    filters = load_filters()
    raw = raw_signal()
    lowpass, median, ema = run_stack(filters, raw)
    time = range(DURATION)

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=120)
    ax.axvspan(STEP_START, STEP_END, color="#e8eef8", label="Real load change")
    ax.plot(time, raw, color="#9a9a9a", linewidth=0.8, label="Input (1 s updates)")
    ax.plot(time, lowpass, color="#2f6fd0", linewidth=1.4, label="Lowpass (τ 15 s)")
    ax.plot(time, median, color="#e08a1e", linewidth=1.4, label="Median (15 values)")
    ax.plot(time, ema, color="#2a9d55", linewidth=2.2, label="EMA (95 % in 120 s)")
    ax.set_title("Smoothing Analytics Sensors with default settings")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Power (W)")
    ax.set_xlim(0, DURATION)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", framealpha=0.95)
    fig.tight_layout()
    fig.savefig(OUTPUT)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
