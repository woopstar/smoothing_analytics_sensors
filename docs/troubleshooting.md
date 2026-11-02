# Troubleshooting

## Enable Debug Logging

```yaml
logger:
  default: warning
  logs:
    custom_components.smoothing_analytics_sensors: debug
```

Or **Settings → Devices & services → Smoothing Analytics Sensors → Enable debug logging**.

## Common Problems

| Symptom                                            | Likely cause                                                                                        | Fix                                                                   |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Median stays `unknown`                             | Window not full yet                                                                                 | Wait for `median_sampling_size` updates. Check `missing_data_points`. |
| Median or EMA never updates                        | Upstream stage is disabled or failed to load. Median and EMA only listen to the upstream SAS sensor | Enable the upstream sensor, then reload the entry                     |
| Log: `Invalid value from sensor.x: unavailable`    | Input sensor is `unavailable` or `unknown`                                                          | Harmless. The filter skips the update.                                |
| EMA jumps past the input after a restart           | Long gap makes `α > 1`. See [Filter math](filter-math.md#large-gaps)                                | Known issue                                                           |
| Options form shows defaults, not my initial values | Options form reads only saved options                                                               | Known issue. Re-enter your values once.                               |
| Two entries for the same input sensor break        | Both entries get the same unique_ids                                                                | Use one entry per input sensor                                        |
| Energy dashboard does not offer the sensor         | Long-term statistics need `state_class`                                                             | Known issue, see open issues                                          |

## Known Issues

All findings from the November 2026 code review are tracked as GitHub issues with the label
[`review-2026-11`](https://github.com/woopstar/smoothing_analytics_sensors/issues?q=label%3Areview-2026-11).

## Report a Bug

Open an [issue](https://github.com/woopstar/smoothing_analytics_sensors/issues) with:

- Home Assistant version and SAS version
- Input sensor update interval
- Your filter settings
- Debug log covering the problem
- Attributes of the affected SAS sensor
