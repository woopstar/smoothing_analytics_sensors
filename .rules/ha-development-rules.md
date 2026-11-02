# SAS Compliance Checklist — Read Before Any Code Change

This checklist enforces Home Assistant development guidelines from:

- https://developers.home-assistant.io/docs/creating_component_code_review
- https://developers.home-assistant.io/docs/development_guidelines
- https://developers.home-assistant.io/docs/core/integration-quality-scale/

Apply these rules to **every** PR, regardless of scope.

---

## Pre-Flight

Work in a dedicated worktree, never directly on `main` (details:
`.claude/skills/sas-pre-flight/SKILL.md`):

```bash
git fetch origin
git worktree add ../sas-worktrees/sas-<issue> -b <type>/<issue>-<slug> origin/main
cd ../sas-worktrees/sas-<issue>
cat .github/memories.md
```

Branch naming: `<type>/<issue-number>-<slug>`

---

## Section 1 — Development Checklist (HA Silver/Gold)

- [ ] **Dependencies**: SAS has no third-party runtime dependencies. Keep it that way unless justified. Dev-only deps go in `pyproject.toml` / `requirements_*.txt`.
- [ ] **Async patterns**: No blocking calls (`time.sleep`, `requests`, `open()`) on the event loop. All `hass.async_create_task()` calls have error handling.
- [ ] **Setup/unload**: `async_setup_entry` forwards platforms with `async_forward_entry_setups`; `async_unload_entry` uses `async_unload_platforms`. Options changes trigger a reload through an update listener registered with `entry.async_on_unload(...)`.
- [ ] **Listeners**: Every `async_track_*` subscription is wrapped in `self.async_on_remove(...)` (entities) or `entry.async_on_unload(...)` (setup). Nothing outlives its entity or entry.
- [ ] **Config flow**: Every `async_step_*` returns a proper dict. No state leaks between steps. Duplicate entries are prevented with `async_set_unique_id` + `_abort_if_unique_id_configured`. `async_migrate_entry` handles version bumps.
- [ ] **Options flow**: Use `self.config_entry` (HA ≥ 2024.11). Never pass `config_entry` into the `OptionsFlow` constructor. Defaults fall back from `options` to `data`.
- [ ] **Voluptuous schemas**: Present for all configuration validation. Defaults live in the schema. Use generic keys from `homeassistant.const` where possible (`CONF_NAME`).
- [ ] **Translations**: Every user-facing string (field labels, errors, aborts, entity names) has a key in `translations/en.json` and `translations/da.json`.
- [ ] **Entity base classes**: Correct MRO — mixins before base: `RestoreSensor, SensorEntity` (or `RestoreEntity, SensorEntity`). No bare `Entity` for sensors.
- [ ] **Entity values**: Use `native_value`, `native_unit_of_measurement`, `device_class`, `state_class` via `_attr_*`. Do not override `state`.
- [ ] **Device info**: Every entity has a stable `unique_id` that includes the config entry ID, and `device_info` with `identifiers={(DOMAIN, entry.entry_id)}`.
- [ ] **Runtime data**: Store per-entry runtime objects in `entry.runtime_data`, not in `hass.data[DOMAIN]`.
- [ ] **Recorder**: Large or fast-changing attributes are excluded via `_unrecorded_attributes`.
- [ ] **Event names**: Prefix all custom event names with the domain name.

---

## Section 2 — Style Guidelines

- [ ] **File headers**: Every `.py` file starts with a docstring describing what the file does.
- [ ] **Import order**: Standard library → third-party → `homeassistant.*` → `custom_components.smoothing_analytics_sensors.*` (ruff isort enforces it).
- [ ] **Alphabetical ordering**: Constants and the content of lists/dictionaries should be in alphabetical order.
- [ ] **HA constants**: Check [`homeassistant/const.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/const.py) before defining your own (`CONF_NAME`, `Platform`, `STATE_UNAVAILABLE`, `STATE_UNKNOWN`).
- [ ] **No hardcoded strings**: No `"unknown"`, `"unavailable"`, `"sensor"` — use HA constants.
- [ ] **String formatting**: f-strings for runtime strings. Logging uses `%`-formatting, never f-strings.
- [ ] **Logging rules**: No component name in log messages. No period at the end. Restrict `_LOGGER.info`; use `_LOGGER.debug` for details. Do not log a warning on every unavailable input update.
- [ ] **Time**: Use `homeassistant.util.dt` (`dt_util.utcnow()`) or `time.monotonic()`. Never naive `datetime.now()`.
- [ ] **Type hints**: Every public function has parameter and return type annotations. Use `| None`, not `Optional[...]`.
- [ ] **Docstrings**: Google-style. Summary line (imperative, period).
- [ ] **`@override`**: Every method that overrides a base class method has the `@override` decorator.

---

## Section 3 — Filter Math

- [ ] Filter functions are pure, live in one module, and have unit tests.
- [ ] Every filter is time-aware: its coefficient depends on the real elapsed time `dt`, not on the sample count, unless the parameter is explicitly defined in samples (median).
- [ ] Coefficients are clamped to `0 < k ≤ 1`. A long gap (restart, unavailable input) must never produce `k > 1`.
- [ ] `docs/filter-math.md` is updated in the same PR as any formula change.

---

## Section 4 — PR Scope Rules

- [ ] **No feature creep**: Do not add features not directly needed by the issue.
- [ ] **No mixed cleanups**: Do not mix refactors/cleanups with feature work in one PR.
- [ ] **One issue per PR**: Do not solve multiple issues in a single PR.
- [ ] **No unmerged dependencies**: Do not submit PRs that depend on other unmerged work.

---

## Section 5 — Testing

- [ ] **Framework**: `pytest-homeassistant-custom-component` for anything that needs `hass`; plain pytest for pure filter math.
- [ ] **Config flow tests**: Fresh install, options flow, abort-on-duplicate, validation errors.
- [ ] **Entity tests**: Assert `unique_id`, `device_info`, `native_value`, `native_unit_of_measurement`, `state_class`, `extra_state_attributes`.
- [ ] **Lifecycle tests**: Setup → unload → setup leaves exactly one listener per entity.
- [ ] **Float comparisons**: `pytest.approx()` in tests, epsilon guard in production.

---

## Quality Gates

```bash
./scripts/quality.sh lint     # ruff format + ruff check + prettier
./scripts/quality.sh typing   # mypy
./scripts/quality.sh test     # pytest with coverage
./scripts/quality.sh all      # everything above + translations
```

---

## Commit & PR

- Conventional Commits: `<type>(<scope>): <description>`
- PR description: summary, files changed, what changed and why, tests, quality gate results
- Include `Fixes #<ISSUE_NUMBER>` if applicable
- Never merge without explicit permission
