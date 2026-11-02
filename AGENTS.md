# AGENTS.md — Smoothing Analytics Sensors

This document is for AI coding agents (Claude Code, Copilot, Zed agents) working in this
repository. It defines setup, constraints, workflow and quality expectations for
Smoothing Analytics Sensors (SAS).

Agents must follow this document strictly.

## Agent Objectives

- Maintain a small, correct Home Assistant integration that smooths any numeric sensor.
- Keep changes minimal, isolated and testable.
- Prefer deterministic, explicit implementations over implicit or heuristic behavior.
- Never fabricate missing technical details.
- Work toward the Home Assistant integration quality scale (Bronze → Silver → Gold).

## No-Assumption Rule (Facts Only)

If required technical details are missing, the agent MUST locate them in this repository,
the Home Assistant developer docs, or explicitly ask for clarification.

The agent must NOT invent HA APIs, guess deprecation timelines or introduce undocumented
configuration keys.

## Repository Structure

| Path                                                            | Purpose                                             |
| --------------------------------------------------------------- | --------------------------------------------------- |
| `custom_components/smoothing_analytics_sensors/`                | The integration                                     |
| `custom_components/smoothing_analytics_sensors/custom_sensors/` | One module per filter sensor (lowpass, median, EMA) |
| `custom_components/smoothing_analytics_sensors/filters.py`      | Pure filter math                                    |
| `custom_components/smoothing_analytics_sensors/entity.py`       | Shared base sensor                                  |
| `custom_components/smoothing_analytics_sensors/translations/`   | `en.json` (source of truth) and `da.json`           |
| `tests/`                                                        | pytest suite                                        |
| `docs/`                                                         | User and developer docs, synced to the GitHub wiki  |
| `scripts/`                                                      | Quality gates and validators                        |
| `.claude/skills/`                                               | Agent skills (pre-flight, PR workflow, issues…)     |
| `.github/`                                                      | Workflows, label manifest, repository memory        |

## Environment & Setup

- Python version: see `.python-version`.
- Install dev tooling: `./scripts/setup.sh` (creates `.venv` with lint, typing and test deps).
- Run all gates: `./scripts/quality.sh all`.

## Mandatory Reading

| Before you…                     | Read                                      |
| ------------------------------- | ----------------------------------------- |
| Start any change                | `.github/memories.md`                     |
| Touch filter math               | `docs/filter-math.md`                     |
| Touch config/options flow       | `docs/configuration.md`                   |
| Touch entities, setup or unload | `.rules/ha-development-rules.md`          |
| Open a PR                       | `.claude/skills/sas-pr-workflow/SKILL.md` |

## Development Rules

1. **One issue per branch and PR.** Branch name: `<type>/<issue>-<slug>`.
2. **Preserve behavior** unless the issue asks to change it. Filter output changes are
   user-visible (dashboards, automations, long-term statistics) and need a release note.
3. **Unique IDs are a contract.** Changing the unique_id scheme orphans entities and
   history. Any change needs a config entry migration (`async_migrate_entry`).
4. **Filter math lives in pure functions** with unit tests. Document formulas in
   `docs/filter-math.md` in the same PR.
5. **No duplication.** Shared helpers go in `utils/`. The three sensors share one base class
   for input resolution, restore and listener handling.

## Logging & Error Handling

- `_LOGGER = logging.getLogger(__name__)` per module.
- `%`-formatting in log calls, never f-strings.
- `unavailable`/`unknown` input is a normal state. Log it at debug level, not warning.
- Catch specific exceptions (`ValueError`, `TypeError`), never bare `except`.

## Code Standards

See `CODE_QUALITY_STANDARDS.md`. Short version: type hints on public functions,
Google-style docstrings, `@override` on overrides, ruff-clean, mypy-clean.

## Git Workflow

```bash
git fetch origin
git worktree add ../sas-worktrees/sas-<issue> -b <type>/<issue>-<slug> origin/main
```

- Conventional Commits: `<type>(<scope>): <description>`.
- Scopes: `sensor`, `ema`, `lowpass`, `median`, `flow`, `setup`, `manifest`, `docs`, `ci`.
- Never push to `main`. Never force-push a shared branch.
- Never merge without explicit permission from the maintainer.

## Pull Request Guidelines

- Follow `.claude/skills/sas-pr-workflow/SKILL.md`.
- Body: summary, what changed and why, tests, gate results, `Fixes #<n>`.
- Update the PR description after every follow-up commit.

### GitHub Operations

Use the `gh` CLI (`gh issue create --body-file`, `gh pr create --body-file`). Prefer
`rtk gh ...` for compact output. Pass multiline bodies via `--body-file`, never inline.

## Security Constraints

- Never commit secrets, tokens or personal Home Assistant data.
- Never weaken CI permissions (`permissions: {}` / least privilege per job).

## Testing Requirements

- New behavior has tests. Bug fixes have a regression test.
- `pytest-homeassistant-custom-component` for anything that needs `hass`.
- Float comparisons with `pytest.approx()`.

## Definition of Done

- [ ] `./scripts/quality.sh all` passes
- [ ] Tests cover the change
- [ ] Docs in `docs/` and `README.md` match the behavior
- [ ] `en.json` and `da.json` in sync
- [ ] PR description complete and current
