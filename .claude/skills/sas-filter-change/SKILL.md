---
name: sas-filter-change
description: Activate when changing the lowpass, median or EMA filter math, the sensor stacking order, restore behavior, or the meaning of a filter parameter.
---

# SAS Filter Change

Filter output is what users see on dashboards and feed into automations and long-term
statistics. A small formula change shifts every graph. Treat it like an API change.

## Step 1: Read the Spec

Read `docs/filter-math.md`. It is the source of truth for every formula.

## Step 2: Keep Math Pure

- Filter functions take numbers and return numbers. No `hass`, no entity state.
- Put them in one module and import them from the sensors.

## Step 3: Invariants — Check Every One

- [ ] Coefficient `k` satisfies `0 < k <= 1` for all `dt >= 0`.
- [ ] `dt = 0` (two updates in the same instant) does not divide by zero.
- [ ] A long gap (restart, hours of `unavailable`) never produces `k > 1` or a value
      outside the range of input and previous output.
- [ ] Time-based parameters (seconds) use the real elapsed `dt`. Sample-based parameters
      (median window) are documented as samples.
- [ ] Time is measured with `dt_util.utcnow()` or `time.monotonic()`, not naive
      `datetime.now()`.
- [ ] First sample after start or restore is defined and tested.
- [ ] Parameter at min and max of the config flow range is tested.

## Step 4: Tests

Add parametrized tests in `tests/test_filters.py`:

- step response reaches 95 % within the documented time (EMA)
- constant input stays constant
- negative values and zero
- large `dt`

## Step 5: Docs and Release Note

- Update `docs/filter-math.md` in the same PR. If defaults change, update the README "How It Works" table.
- Regenerate the figure: `uv run --no-project --with matplotlib python scripts/plot_filters.py`.
- Label the PR `breaking-change` if existing users will see different values for the
  same settings, and explain the change in the PR body.
