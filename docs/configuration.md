# Configuration

SAS is configured in the UI. There is no YAML configuration.

## Config Flow (Add Entry)

| Field                          | Key                     | Default                       | Range      | Unit (UI) |
| ------------------------------ | ----------------------- | ----------------------------- | ---------- | --------- |
| Input Sensor                   | `input_sensor`          | —                             | any sensor | —         |
| Name                           | `device_name`           | `Smoothing Analytics Sensors` | text       | —         |
| Lowpass Time Constant          | `lowpass_time_constant` | 15                            | 1–60       | seconds   |
| Median Sampling Size           | `median_sampling_size`  | 15                            | 1–60       | samples   |
| EMA Desired Time to Reach 95 % | `desired_time_to_95`    | 120                           | 10–600     | seconds   |

The name becomes the config entry title and the device name.

The input sensor must exist and have a numeric value, or no value yet (`unavailable`, `unknown`).
Otherwise the form shows "Choose a sensor that exists and has a numeric value".

SAS allows one entry per input sensor. Adding the same sensor again stops with "already configured".

## Options Flow (Configure)

**Settings → Devices & services → Smoothing Analytics Sensors → Configure** lets you change:

| Field                          | Key                     | Range  |
| ------------------------------ | ----------------------- | ------ |
| Name                           | `device_name`           | text   |
| Lowpass Time Constant          | `lowpass_time_constant` | 1–60   |
| Median Sampling Size           | `median_sampling_size`  | 1–60   |
| EMA Desired Time to Reach 95 % | `desired_time_to_95`    | 10–600 |

The form starts with the current values. Ranges are the same as in the config flow.

Renaming the input sensor's entity_id is fine: SAS stores its registry id and follows the rename.

### When Options Take Effect

Saving the form reloads the entry. New parameters apply right away. A new name updates the
entry title and the device name. The sensors keep their restored values across the reload.

## Change the Input Sensor (Reconfigure)

**Settings → Devices & services → Smoothing Analytics Sensors → ⋮ → Reconfigure** lets you pick a
new input sensor. The SAS entities keep their entity IDs, unique IDs and history. The filters
continue from their last values and move toward the new input. The new input must not already
have its own SAS entry.

## Parameter Guide

### Lowpass Time Constant

Weight of the newest value is `1 / time_constant`. The parameter counts **updates**, not seconds.
See [Filter math](filter-math.md#lowpass).

| Value | Effect                                         |
| ----- | ---------------------------------------------- |
| 1     | No smoothing. Output equals input.             |
| 5     | Light smoothing                                |
| 15    | Default. 95 % of a step after about 45 updates |
| 60    | Heavy smoothing, slow reaction                 |

### Median Sampling Size

Number of recent lowpass values in the median window. Larger windows remove longer spikes but add
delay. A spike shorter than half the window disappears completely.

The median sensor stays `unknown` until the window is full after a fresh install.

### EMA Desired Time to Reach 95 %

Target time in seconds for the EMA to follow a step change. The EMA uses the real time between its
updates. See [Filter math](filter-math.md#ema) for how close the current formula gets to the
target.

## Presets

| Use case                         | Lowpass | Median | EMA (s) |
| -------------------------------- | ------- | ------ | ------- |
| Grid power, 1 s updates          | 15      | 15     | 120     |
| Grid power, 10 s updates         | 5       | 7      | 300     |
| House load for battery decisions | 15      | 31     | 300     |
| Temperature, 60 s updates        | 3       | 5      | 600     |

Odd median windows give a true middle value.
