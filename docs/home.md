# Smoothing Analytics Sensors

Smoothing Analytics Sensors (SAS) is a Home Assistant integration that turns one noisy numeric
sensor into three smoothed sensors:

```
input sensor ──► Lowpass ──► Moving median ──► EMA
```

Each stage filters the output of the previous one. Use the EMA sensor when you want a stable value
for automations, dashboards or energy decisions. Use the lowpass or median sensor when you need a
faster reaction.

SAS was extracted from the smoothing logic in
[HSEM](https://github.com/woopstar/hsem) and the
[Huawei Solar Battery Optimization project](https://github.com/heinoskov/huawei-solar-battery-optimizations).

## Start Here

| You want to…                      | Read                                      |
| --------------------------------- | ----------------------------------------- |
| Install SAS                       | [Installation](installation.md)           |
| Pick filter settings              | [Configuration](configuration.md)         |
| Know which entities you get       | [Sensors reference](sensors-reference.md) |
| Understand the formulas           | [Filter math](filter-math.md)             |
| Fix a sensor that stays `unknown` | [Troubleshooting](troubleshooting.md)     |
| Contribute                        | [Development](development.md)             |

## Typical Use Cases

- Grid import/export power that spikes when a kettle or heat pump starts
- Solar production on cloudy days
- House load used as input to battery or EV charging decisions
- Temperature or humidity sensors with jitter

## Quick Facts

| Item                 | Value                               |
| -------------------- | ----------------------------------- |
| Domain               | `smoothing_analytics_sensors`       |
| Setup                | UI config flow, one entry per input |
| Platforms            | `sensor`                            |
| Sensors per entry    | 3 (lowpass, median, EMA)            |
| Runtime dependencies | None                                |
| Languages            | English, Danish                     |
