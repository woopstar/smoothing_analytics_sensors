# Claude Code Instructions for SAS

Quick reference. The full rules live in `AGENTS.md`.

## Quick Start

1. Read `AGENTS.md` and `.github/memories.md`.
2. Run the `sas-pre-flight` skill: worktree + branch `<type>/<issue>-<slug>`.
3. Make one focused change.
4. Run `./scripts/quality.sh all`.
5. Open a PR with the `sas-pr-workflow` skill. Do not merge without permission.

## Skills

| Skill                  | Use when                                               |
| ---------------------- | ------------------------------------------------------ |
| `sas-pre-flight`       | Before any code change                                 |
| `sas-ha-compliance`    | Touching setup/unload, entities, config flow, manifest |
| `sas-filter-change`    | Changing lowpass, median or EMA math or stacking       |
| `sas-code-quality`     | Before every commit                                    |
| `sas-translation-sync` | Any user-facing string changed                         |
| `sas-doc-sync`         | After every behavior change                            |
| `sas-issue-creation`   | Filing a GitHub issue                                  |
| `sas-pr-workflow`      | Opening or updating a PR                               |
| `code-review`          | Reviewing a diff or PR                                 |

## Core Principles

- One issue per session, branch and PR.
- Preserve existing behavior unless the issue says otherwise.
- Unique IDs and entity IDs are a user contract. Migrate, never silently change.
- Never `==` on floats. Use `math.isclose` or an epsilon in code, `pytest.approx` in tests.
- `%`-formatting in logs.

## RTK

Prefix shell commands with `rtk` when available (`rtk git status`, `rtk pytest`,
`rtk gh issue list`). `scripts/quality.sh` does this automatically.
