---
name: sas-ha-compliance
description: Activate when a change touches Home Assistant integration surfaces in SAS — setup/unload, entities, config or options flow, translations, device info, listeners or manifest.
---

# SAS Home Assistant Compliance

The full checklist is `.rules/ha-development-rules.md`. This skill lists what goes wrong
most often in this integration.

## Lifecycle

- [ ] `__init__.py` uses `async_forward_entry_setups` and `async_unload_platforms` with
      `[Platform.SENSOR]`.
- [ ] An update listener reloads the entry when options change:
      `entry.async_on_unload(entry.add_update_listener(_async_update_listener))`.
- [ ] Platform modules (`sensor.py`) do **not** define `async_unload_entry`. HA never calls it there.
- [ ] Per-entry objects go in `entry.runtime_data`, not `hass.data[DOMAIN]`.

## Entities

- [ ] Sensors subclass `RestoreSensor` (or `RestoreEntity, SensorEntity`), never bare `Entity`.
- [ ] Values via `_attr_native_value`, `_attr_native_unit_of_measurement`,
      `_attr_device_class`, `_attr_state_class`. No `state` override.
- [ ] `_attr_should_poll = False` for event-driven sensors.
- [ ] Every `async_track_state_change_event(...)` is wrapped:
      `self.async_on_remove(async_track_state_change_event(...))`.
- [ ] `available` reflects the input sensor. `unavailable` input is not a warning.
- [ ] `_attr_translation_key` + `_attr_has_entity_name = True` instead of a `name` property.
- [ ] `_unrecorded_attributes` excludes `data_points`, `last_updated`, `previous_value`.
- [ ] `unique_id` stable and unique per config entry.

## Config & Options Flow

- [ ] Duplicate guard: `await self.async_set_unique_id(...)` + `self._abort_if_unique_id_configured()`.
- [ ] `OptionsFlow` without a custom `__init__(config_entry)`. Use `self.config_entry`.
- [ ] Options defaults: `options` → `data` → const default.
- [ ] Same min/max in config and options schema.
- [ ] Every error key used in code exists in `translations/en.json` and `da.json`.

## Manifest

- [ ] `iot_class: "calculated"`, `integration_type: "helper"`.
- [ ] No unused `dependencies` / `after_dependencies`.
- [ ] `hacs.json` `homeassistant` minimum matches the APIs used.

## Tests

- [ ] Config flow: create, duplicate abort, options save.
- [ ] Setup → unload → setup: one listener per entity.
- [ ] Entity: `unique_id`, `device_info`, `native_value`, `state_class`, restore.
