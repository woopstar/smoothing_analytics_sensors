# Troubleshooting

## Enable Debug Logging

```yaml
logger:
  default: warning
  logs:
    custom_components.smoothing_analytics_sensors: debug
```

Or **Settings → Devices & services → Smoothing Analytics Sensors → Enable debug logging**.

## Download Diagnostics

**Settings → Devices & services → Smoothing Analytics Sensors → ⋮ → Download diagnostics**.

The file holds the entry settings and, per stage, the value, the resolved input, the last `Δt`,
the median window and the EMA alpha. Attach it to a bug report.

## Common Problems

| Symptom                                            | Likely cause                                                                                        | Fix                                                                   |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Median stays `unknown`                             | Window not full yet                                                                                 | Wait for `median_sampling_size` updates. Check `missing_data_points`. |
| Median or EMA never updates                        | Upstream stage is disabled or failed to load. Median and EMA only listen to the upstream SAS sensor | Enable the upstream sensor, then reload the entry                     |
| SAS sensors show `unavailable`                     | The input sensor is `unavailable`. The whole stack follows it                                       | Fix the input. The filters continue from their last value             |
| Options form shows defaults, not my initial values | Options form reads only saved options                                                               | Known issue. Re-enter your values once.                               |
| Setup says the input sensor is already configured  | SAS allows one entry per input sensor                                                               | Change the existing entry under Configure instead                     |

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
