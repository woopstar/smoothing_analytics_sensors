# Code Quality Standards for SAS

## Overview

SAS is small. Keep it that way: few files, pure filter math, thin Home Assistant glue.

## Core Principles

### 1. `./scripts/quality.sh lint` is non-negotiable

Runs `ruff format`, `ruff check --fix` and prettier. CI runs the same checks in
`format-check` mode and fails on any diff.

### 2. Type hints required

Every public function has parameter and return annotations. Use `X | None`.

```python
def ema_alpha(dt: float, time_to_95: float) -> float:
    """Return the EMA coefficient for an update after dt seconds."""
```

### 3. Docstrings for public APIs

Google-style. Imperative summary line ending with a period.

### 4. Explicit error handling

```python
# Bad: swallows everything
try:
    value = float(state.state)
except Exception:
    pass

# Good: expected states are handled, unexpected values are logged once
if state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
    return
try:
    value = float(state.state)
except (TypeError, ValueError):
    _LOGGER.debug("Non-numeric value from %s: %s", state.entity_id, state.state)
    return
```

### 5. Pure filter functions

Filter math takes numbers and returns numbers. No `hass`, no state, no logging.
Every function has unit tests including edge cases: first sample, `dt = 0`,
very large `dt`, negative values, parameter at its min and max.

### 6. Floats

Never `==` / `!=` on floats in production code. Use `math.isclose()` or an epsilon.
Tests use `pytest.approx()`.

### 7. Comments explain why, not what

### 8. Logging

`%`-formatting, no trailing period, no component name, `debug` for routine events.

## Pre-commit Checklist

```bash
./scripts/quality.sh lint
./scripts/quality.sh typing
./scripts/quality.sh test
./scripts/quality.sh translations
```

Or `./scripts/quality.sh all`.

## File Organization

- One sensor class per file in `custom_sensors/`.
- Shared behavior (input resolution, restore, listener lifecycle) in one base class.
- Shared helpers in `utils/`. A helper used twice lives in `utils/`.
