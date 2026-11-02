# SAS Repository Memory

Architecture, conventions and lessons for Smoothing Analytics Sensors. Read before any change.

---

## RTK CLI Rule

- Prefix shell commands with `rtk` when installed (`rtk git status`, `rtk pytest`, `rtk grep`).
- `rtk proxy <cmd>` runs a command without filtering.

---

## Module Map (`custom_components/smoothing_analytics_sensors/`)

| File                               | Responsibility                                                    |
| ---------------------------------- | ----------------------------------------------------------------- |
| `__init__.py`                      | Config entry setup/unload, forwards the `sensor` platform         |
| `config_flow.py`                   | Config flow (`user` step) and options flow (`init` step)          |
| `const.py`                         | Domain, name, icon, default filter parameters                     |
| `entity.py`                        | `SmoothingAnalyticsEntity` base: device info                      |
| `diagnostics.py`                   | Config entry diagnostics: settings and internal state per stage   |
| `sensor.py`                        | Platform setup: builds the lowpass → median → EMA stack per entry |
| `custom_sensors/lowpass_sensor.py` | First-order lowpass on the raw input sensor                       |
| `custom_sensors/median_sensor.py`  | Moving median over the last N lowpass values                      |
| `custom_sensors/ema_sensor.py`     | EMA over the median values, alpha from desired time to 95 %       |
| `utils/misc.py`                    | MD5 hash of the input entity_id, options→data config lookup       |
| `translations/{en,da}.json`        | Config/options flow strings. `en.json` is the source of truth     |

## Sensor Stack

```
input sensor ──► Lowpass (sas_lowpass_<hash>) ──► Median (sas_median_<hash>) ──► EMA (sas_ema_<hash>)
```

- `<hash>` = MD5 of the input `entity_id`.
- Median and EMA find their input by resolving the upstream **unique_id** in the entity
  registry, then subscribe to state changes of the resolved `entity_id`.
- Every stage is event-driven on its upstream state change and also has `async_update`.

## Configuration Keys

| Key                     | Default                       | Meaning                                     |
| ----------------------- | ----------------------------- | ------------------------------------------- |
| `input_sensor`          | —                             | Raw sensor to smooth (config only)          |
| `device_name`           | `Smoothing Analytics Sensors` | Device and entry title                      |
| `lowpass_time_constant` | 15                            | Lowpass divisor (see `docs/filter-math.md`) |
| `median_sampling_size`  | 15                            | Median window in samples                    |
| `desired_time_to_95`    | 120                           | EMA response time in seconds                |

Values are read with `get_config_value()`: options first, then data, then default.

## Canonical Patterns

- New stage logic goes in `SmoothingAnalyticsSensor` subclasses: set `_type` (also the translation key for the name),
  implement `_apply(value)`, and `_restore_extra` / `_reset_extra` for extra restored values.
- Filter math lives only in `filters.py` and is tested in `tests/test_filters.py`.
- Config lookup: `utils.misc.get_config_value(entry, key, default)`. Never read
  `entry.options` or `entry.data` directly for filter parameters.
- Unique IDs: `sas_<type>_<hash>`. Changing this breaks history and needs a migration.
- Config entries are version 2, minor 2. `async_migrate_entry` adds `input_entity_uuid` (1 → 2) and
  converts the pre-2.0.0 `ema_smoothing_window` to `desired_time_to_95` (2.1 → 2.2).
- `<hash>` comes from `data["hash_source"]`, or `data["input_sensor"]` when there is none. Reconfigure
  sets `hash_source` to the first input. The current input entity_id comes from
  `utils.misc.current_input_sensor()` (registry id `input_entity_uuid`, then `input_sensor`).

## Known Pitfalls

- OneDrive/iCloud checkouts flip the executable bit. Run `git config core.fileMode false`.
  New shell scripts then need `git update-index --chmod=+x <file>`, or CI fails with exit 126.
- Keep the venv outside synced folders: `SAS_VENV=~/.cache/sas/venv`.
- The GitHub wiki must have one page created in the UI before `sync-wiki.yml` can push.
- Entity names come from `entity.sensor.<type>.name` in the translations (`_attr_translation_key`).
  Add a key to `en.json` and `da.json` for every new stage.

## Open Review Findings

The full code review from 2026-11 is tracked as GitHub issues labeled `review-2026-11`.
Check them before starting work in the same area.
