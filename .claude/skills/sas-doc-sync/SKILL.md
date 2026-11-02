---
name: sas-doc-sync
description: Activate after every code change to verify that README, docs/ (synced to the wiki) and translations describe the new behavior.
---

# SAS Documentation Sync

`docs/` is published to the GitHub wiki by `.github/workflows/sync-wiki.yml` on every
merge to `main`. Stale docs reach users within minutes.

## Files to Check

| File                        | Check when                                                     |
| --------------------------- | -------------------------------------------------------------- |
| `docs/filter-math.md`       | Any formula, coefficient, restore or stacking change           |
| `assets/visualization.png`  | Filter math or defaults changed: run `scripts/plot_filters.py` |
| `docs/configuration.md`     | Config/options flow fields, defaults, ranges                   |
| `docs/sensors-reference.md` | Entity names, unique IDs, attributes, units, state class       |
| `docs/troubleshooting.md`   | New log messages, failure modes, known issues                  |
| `docs/installation.md`      | HACS/manifest/minimum HA version                               |
| `docs/development.md`       | Tooling, gates, workflows, skills                              |
| `docs/index.md`             | A doc page was added or removed (drives the wiki sidebar)      |
| `.github/memories.md`       | Module map or canonical patterns changed                       |
| `README.md`                 | User-facing features or defaults changed                       |
| `translations/{en,da}.json` | Any user-facing string — see `sas-translation-sync`            |

## Rules

- `docs/filter-math.md` and the code must never diverge.
- A new doc page needs a row in the table in `docs/index.md`, or it will not appear in
  the wiki sidebar.
- Links between docs use relative `page.md` links. The sync strips nothing else.
- Defaults in docs must match `const.py`.

## Checklist

- [ ] Every file above read and updated where it describes the change
- [ ] Defaults in docs match `const.py`
- [ ] New pages listed in `docs/index.md`
- [ ] `./scripts/quality.sh lint` run (prettier formats markdown)
