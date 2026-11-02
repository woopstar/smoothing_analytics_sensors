# Sensors Reference

Each config entry creates one device and three sensors.

## Entities

| Stage   | Name (en / da)       | unique_id            | Input                       |
| ------- | -------------------- | -------------------- | --------------------------- |
| Lowpass | `Lowpass` / `Lavpas` | `sas_lowpass_<hash>` | The configured input sensor |
| Median  | `Median` / `Median`  | `sas_median_<hash>`  | The lowpass sensor          |
| EMA     | `EMA` / `EMA`        | `sas_ema_<hash>`     | The median sensor           |

`<hash>` is the MD5 hex digest of the input sensor's `entity_id` at creation, for example
`sensor.grid_power`.

Home Assistant shows the device name plus the stage name, for example "Grid power EMA", and
generates entity IDs such as `sensor.grid_power_ema` for new entries. Entries created by older
releases keep their entity IDs (`…_ema_filtered_sensor_3f2a…`). Only the display name changes.
Rename them in the UI if you like.
Renaming does not break the stack. Each stage follows a renamed input or upstream stage right away,
without a restart. The unique IDs do not change.

## Unit, Device Class and State Class

All stages are Home Assistant `SensorEntity` sensors. Each stage copies `unit_of_measurement` and
`device_class` from its input on every update. Before the first update they are empty.

The state class is always `measurement`, also when the input is a meter (`total` or
`total_increasing`). A smoothed value is not a meter reading, and filter lag would look like
resets in the statistics. Device classes that do not allow `measurement` (`energy`, `gas`,
`water`, `volume`, `monetary`, ...) are dropped. The unit is kept.

With a `state_class` the sensor gets long-term statistics and can be used in statistics cards.
Because the unit and device class are standard, Home Assistant also converts units (for example
°C to °F) to match your unit system.

## Attributes

Attributes that change on every update are not stored in the recorder database. They are still
visible in the UI and restored after a restart.

| Stage   | Not recorded                                                                                        |
| ------- | --------------------------------------------------------------------------------------------------- |
| Lowpass | `last_updated`, `previous_value`, `sensor_update_interval`                                          |
| Median  | `data_points`, `data_points_count`, `last_updated`, `missing_data_points`, `sensor_update_interval` |
| EMA     | `alpha`, `last_updated`, `number_of_updates_needed`, `previous_value`, `sensor_update_interval`     |

### Lowpass

| Attribute                | Meaning                              |
| ------------------------ | ------------------------------------ |
| `input_sensor`           | Input entity_id                      |
| `last_updated`           | UTC ISO timestamp of the last update |
| `lowpass_time_constant`  | Active time constant                 |
| `previous_value`         | Output before the last update        |
| `sensor_hash`            | MD5 of the input entity_id           |
| `sensor_update_interval` | Seconds between the last two updates |
| `type`                   | `lowpass`                            |
| `unique_id`              | Entity unique_id                     |

### Median

| Attribute                | Meaning                              |
| ------------------------ | ------------------------------------ |
| `data_points`            | Current window values                |
| `data_points_count`      | Values in the window                 |
| `input_entity_id`        | Resolved lowpass entity_id           |
| `input_unique_id`        | Lowpass unique_id                    |
| `last_updated`           | UTC ISO timestamp of the last update |
| `median_sampling_size`   | Window size N                        |
| `missing_data_points`    | N minus values in the window         |
| `sensor_hash`            | MD5 of the input entity_id           |
| `sensor_update_interval` | Seconds between the last two updates |
| `type`                   | `moving_median`                      |
| `unique_id`              | Entity unique_id                     |

### EMA

| Attribute                  | Meaning                              |
| -------------------------- | ------------------------------------ |
| `alpha`                    | Coefficient used in the last update  |
| `desired_time_to_95`       | Active setting                       |
| `input_entity_id`          | Resolved median entity_id            |
| `input_unique_id`          | Median unique_id                     |
| `last_updated`             | UTC ISO timestamp of the last update |
| `number_of_updates_needed` | `desired_time_to_95 / Δt`            |
| `previous_value`           | Output before the last update        |
| `sensor_hash`              | MD5 of the input entity_id           |
| `sensor_update_interval`   | Seconds between the last two updates |
| `type`                     | `ema`                                |
| `unique_id`                | Entity unique_id                     |

## Device

| Field        | Value                                       |
| ------------ | ------------------------------------------- |
| Name         | `device_name` from the config flow          |
| Manufacturer | `Smoothing Analytics Sensors`               |
| Identifier   | `(smoothing_analytics_sensors, <entry_id>)` |
