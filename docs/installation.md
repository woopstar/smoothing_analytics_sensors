# Installation

## Requirements

| Item           | Value                                      |
| -------------- | ------------------------------------------ |
| Home Assistant | 2024.11.0 or newer (see `hacs.json`)       |
| Input sensor   | Any `sensor.*` entity with a numeric state |

## HACS (Recommended)

1. Open **HACS → Integrations**.
2. Open the menu (three dots) → **Custom repositories**.
3. Add `https://github.com/woopstar/smoothing_analytics_sensors` with category **Integration**.
4. Search for **Smoothing Analytics Sensors** and click **Download**.
5. Restart Home Assistant.

## Manual

1. Download `smoothing_analytics_sensors.zip` from the
   [latest release](https://github.com/woopstar/smoothing_analytics_sensors/releases/latest).
2. Unzip into `config/custom_components/smoothing_analytics_sensors/`.
3. Restart Home Assistant.

## Add an Entry

1. **Settings → Devices & services → Add integration**.
2. Search for **Smoothing Analytics Sensors**.
3. Pick the input sensor and filter parameters. See [Configuration](configuration.md).

Add one entry per sensor you want to smooth.

## Remove

1. **Settings → Devices & services → Smoothing Analytics Sensors**.
2. Open the entry menu → **Delete**.
3. Remove the integration in HACS if you no longer need it.
