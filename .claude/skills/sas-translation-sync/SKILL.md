---
name: sas-translation-sync
description: Activate before opening or updating a PR, and whenever a user-facing string (config/options flow label, description, error, abort, entity name) is added, changed or removed. Keeps translations/en.json and da.json in sync.
---

# SAS Translation Sync — Keep en/da in Sync

SAS ships **English** (`en.json`, source of truth) and **Danish** (`da.json`) under
`custom_components/smoothing_analytics_sensors/translations/`.

## Step 1 — Run the Validator

```bash
./scripts/quality.sh translations
```

Reports missing keys, stale keys and `{placeholder}` mismatches (hard errors) and
untranslated values (warnings).

## Step 2 — Fix

- **Missing keys**: translate. `config.step.user.data.*` and `options.step.init.data.*`
  share most labels. Reuse the existing Danish text.
- **Stale keys**: grep the leaf key in `custom_components/`. Delete if dead.
- **Error keys**: every `errors["field"] = "<key>"` in `config_flow.py` must exist under
  `config.error.<key>` in both files.
- **Untranslated warnings**: translate phrases. Leave cognates (`EMA`, `Median`, `Lowpass`).

## Step 3 — Glossary

| English                          | Danish                                  |
| -------------------------------- | --------------------------------------- |
| Input sensor                     | Inputsensor                             |
| Lowpass filter                   | Lavpasfilter                            |
| Time constant                    | Tidskonstant                            |
| Moving median                    | Glidende median                         |
| Sampling size / window           | Antal målinger                          |
| Exponential moving average (EMA) | Eksponentielt glidende gennemsnit (EMA) |
| Time to reach 95 %               | Tid til 95 %                            |
| Device                           | Enhed                                   |
| Name                             | Navn                                    |
| seconds                          | sekunder                                |
| samples                          | målinger                                |

Tone: short imperative, matching the English source.

## Step 4 — Re-run

Must report 0 missing, 0 stale, 0 placeholder mismatches before the PR is opened.

## Known Limitation

Entity names are hard-coded in each sensor's `name` property today, so `entity.*`
translations have no effect until sensors use `_attr_translation_key`. Do not assume a JSON
change alone renames an entity.
