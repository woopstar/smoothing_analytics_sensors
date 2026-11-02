# Filter Math

This page documents what the code does today. It is the source of truth for every formula. A PR
that changes a formula must update this page.

Notation: `x` is the new input value, `y` the previous output, `y'` the new output, `Δt` the
seconds since the sensor's own previous update.

## When a Stage Updates

Each stage updates only when its upstream entity changes state (`async_track_state_change_event`).
Home Assistant does not poll the sensors (`should_poll = False`).

| Upstream state | Stage                                                  |
| -------------- | ------------------------------------------------------ |
| number         | Filters the value, is available                        |
| `unavailable`  | Becomes `unavailable`. Keeps its last value internally |
| `unknown`      | Skips the update and keeps its last value              |
| other text     | Skips the update and logs a warning                    |

Unavailability propagates down the stack: lowpass → median → EMA. When the input returns, each
stage continues from its last value.

There is no periodic tick. While the input stays constant, the outputs stay where they are, and
the median window only holds real upstream readings. `Δt` is always the time between two real
updates, measured in UTC, so DST changes and time zone changes do not affect it.

Filters keep full precision. The UI shows 2 decimals by default (`suggested_display_precision`).
Change it per entity in the entity settings (**Display precision**).

## Lowpass

```
B  = 1 / time_constant
y' = (1 − B) · y + B · x
```

- The first value after a fresh install is passed through: `y' = x`.
- `time_constant` is a number of **updates**. The real time constant in seconds depends on how
  often the stage updates. `Δt` is measured and exposed as an attribute but not used in the formula.

Step response (updates needed to reach 95 % of a step):

| time_constant | Updates to 95 % |
| ------------- | --------------- |
| 1             | 1               |
| 5             | 14              |
| 15            | 44              |
| 60            | 179             |

With 1-second input updates and the default 15, the lowpass reaches 95 % after about 44 seconds.

## Moving Median

```
window = last N lowpass values
y'     = median(window)        once len(window) ≥ N
```

- `N` = `median_sampling_size`, counted in updates.
- Until the window holds `N` values the output keeps its previous value (`unknown` after a fresh
  install).
- The window is stored in the `data_points` attribute and restored after restart.
- After lowering `median_sampling_size`, the restored window is cut to the newest `N` values.
- A spike lasting fewer than `N / 2` updates is removed completely.

## EMA

```
α  = 1 − 0.05^(Δt / desired_time_to_95)
y' = α · x + (1 − α) · y
```

- `Δt` is the real time since the EMA's previous update, so the filter adapts to irregular input.
- The first value after a fresh install is passed through: `y' = x`.

### Time to 95 %

After `desired_time_to_95` seconds the EMA has covered 95 % of a step, whatever the update rate.
With `desired_time_to_95 = 120`:

| Δt (s) | α      | Reached at 120 s |
| ------ | ------ | ---------------- |
| 1      | 0.0247 | 95 %             |
| 10     | 0.2209 | 95 %             |
| 30     | 0.5271 | 95 %             |

Releases before this change used `α = 2 / (desired_time_to_95 / Δt + 1)`, which reached only
86.5 % at `desired_time_to_95` and 95 % after about 1.5 × `desired_time_to_95`. The same setting
now reacts about a third faster.

### Large Gaps

`α` is always below 1, so a long gap (restart, `unavailable` input) moves the output toward the
input but never past it:

| Δt                        | α    | Output                       |
| ------------------------- | ---- | ---------------------------- |
| `≤ 0` (same instant)      | 0    | Unchanged                    |
| `desired_time_to_95`      | 0.95 | 95 % of the way to the input |
| `10 × desired_time_to_95` | ≈ 1  | At the input                 |

## Stacking Delay

The stages are in series, so delays add up. With 1-second input updates and default settings:

| Stage   | Approx. time to follow a step |
| ------- | ----------------------------- |
| Lowpass | 44 s to 95 %                  |
| Median  | + 8 s (half of 15 updates)    |
| EMA     | + 120 s to 95 %               |

## Restore After Restart

All three stages restore their last state with `RestoreSensor`. The median also restores its
window. `sensor_update_interval` is restored too, so the EMA starts with the alpha it had before
the restart. The restored `last_updated` makes the first `Δt` after restart as long as the
downtime.
