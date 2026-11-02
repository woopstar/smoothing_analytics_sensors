# Filter Math

This page documents what the code does today. It is the source of truth for every formula. A PR
that changes a formula must update this page.

Notation: `x` is the new input value, `y` the previous output, `y'` the new output, `Δt` the
seconds since the sensor's own previous update.

## When a Stage Updates

Each stage updates when:

1. its upstream entity changes state (`async_track_state_change_event`), and
2. Home Assistant polls it. The sensors do not set `should_poll = False`, so Home Assistant also
   calls `async_update` every 30 seconds. A poll feeds the current upstream value into the filter
   again, even when the upstream value has not changed.

Output is rounded to 2 decimals after every update.

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
- A spike lasting fewer than `N / 2` updates is removed completely.

## EMA

```
N  = desired_time_to_95 / Δt
α  = min(1, 2 / (N + 1))
y' = α · x + (1 − α) · y
```

- `Δt` is the real time since the EMA's previous update, so the filter adapts to irregular input.
- The first value after a fresh install is passed through: `y' = x`.

### How Close Is "Time to 95 %"?

`α = 2 / (N + 1)` is the classic "span" EMA. It does not reach 95 % at `desired_time_to_95`.
Measured on a unit step with `desired_time_to_95 = 120`:

| Δt (s) | α      | Reached at 120 s | Time to reach 95 % |
| ------ | ------ | ---------------- | ------------------ |
| 1      | 0.0165 | 86.5 %           | 180 s              |
| 10     | 0.1538 | 86.5 %           | 180 s              |
| 30     | 0.4000 | 87.0 %           | 180 s              |

The EMA reaches 95 % after about 1.5 × `desired_time_to_95`.

For an exact 95 % at `T95` the coefficient would be `α = 1 − 0.05^(Δt / T95)`.

### Large Gaps

Without a limit, `Δt > desired_time_to_95` would give `α > 1` and the output would overshoot the
input. This happens after a restart (the restored `last_updated` is old) or after the input was
`unavailable` for a while. α is therefore clamped:

| Δt                     | α           | Output                            |
| ---------------------- | ----------- | --------------------------------- |
| `≤ 0` (same instant)   | 0           | Unchanged                         |
| `0 < Δt < T95`         | `2 / (N+1)` | Between previous output and input |
| `≥ desired_time_to_95` | 1           | Jumps to the input                |

## Stacking Delay

The stages are in series, so delays add up. With 1-second input updates and default settings:

| Stage   | Approx. time to follow a step |
| ------- | ----------------------------- |
| Lowpass | 44 s to 95 %                  |
| Median  | + 8 s (half of 15 updates)    |
| EMA     | + 180 s to 95 %               |

## Restore After Restart

All three stages restore their last state with `RestoreEntity`. The median also restores its
window. The restored `last_updated` makes the first `Δt` after restart as long as the downtime.
