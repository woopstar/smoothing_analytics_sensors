# Development

## Setup

```bash
git clone git@github.com:woopstar/smoothing_analytics_sensors.git
cd smoothing_analytics_sensors
git config core.fileMode false
./scripts/setup.sh
```

`setup.sh` creates `.venv` with the Python version from `.python-version` and installs
`requirements_lint.txt` and `requirements_test.txt`. It uses `uv` when installed.

In a OneDrive or iCloud folder, keep the venv outside the synced tree. Otherwise the sync of about
700 MB of packages blocks git:

```bash
export SAS_VENV=~/.cache/sas/venv
./scripts/setup.sh
```

`quality.sh` picks up `SAS_VENV` too.

## Quality Gates

| Command                             | Runs                                            |
| ----------------------------------- | ----------------------------------------------- |
| `./scripts/quality.sh lint`         | ruff format, ruff check --fix, prettier --write |
| `./scripts/quality.sh format-check` | Same checks, no writes (CI)                     |
| `./scripts/quality.sh typing`       | mypy                                            |
| `./scripts/quality.sh translations` | en.json vs da.json                              |
| `./scripts/quality.sh validate`     | YAML and JSON syntax                            |
| `./scripts/quality.sh test`         | pytest with coverage                            |
| `./scripts/quality.sh all`          | Everything above                                |

Optional: `pre-commit install` runs `lint` and `translations` on every commit.

## Workflow

1. Pick or create an issue. Follow `.claude/skills/sas-issue-creation/SKILL.md`.
2. Create a worktree and branch `<type>/<issue>-<slug>` from `origin/main`.
3. Make one focused change with tests.
4. Run `./scripts/quality.sh all`.
5. Open a PR with a Conventional Commits title. Follow `.claude/skills/sas-pr-workflow/SKILL.md`.

## GitHub Workflows

| Workflow              | Trigger                     | Purpose                                     |
| --------------------- | --------------------------- | ------------------------------------------- |
| `lint-and-test.yml`   | push to main, PR            | Lint, validate, typing, translations, tests |
| `hacs-validate.yml`   | push, nightly               | Hassfest and HACS validation                |
| `semantic-title.yml`  | PR opened/edited            | PR title must follow Conventional Commits   |
| `auto-label.yml`      | PR                          | Labels from the Conventional Commits type   |
| `check-on-hold.yml`   | PR                          | Blocks merge while `pr-on-hold` is set      |
| `dependabot-auto.yml` | Dependabot PR               | Approve, auto-merge patch and minor         |
| `release-drafter.yml` | push to main, nightly       | Draft release notes from labels             |
| `release.yml`         | release published           | Bump manifest version, upload zip           |
| `sync-labels.yaml`    | change to `sync-labels.yml` | Sync repo labels from the manifest          |
| `sync-wiki.yml`       | change to `docs/`           | Publish `docs/` to the GitHub wiki          |

### Wiki Sync

`docs/*.md` is copied to the wiki on every push to `main` that touches `docs/`. `home.md`
becomes `Home.md`. `_Sidebar.md` is generated from the table in `docs/index.md` by
`.github/scripts/generate_wiki_sidebar.py`.

The wiki must exist before the first sync: create one page in the GitHub UI once.

### Labels

`.github/sync-labels.yml` is the label manifest. `auto-label.yml` and `release-drafter.yml` may only
use labels defined there.

## Agent Skills

`.claude/skills/` holds skills for Claude Code and other agents. Start with `AGENTS.md` and
`CLAUDE.md`.

| Skill                  | Purpose                                        |
| ---------------------- | ---------------------------------------------- |
| `sas-pre-flight`       | Worktree, branch, read memory and docs         |
| `sas-ha-compliance`    | HA lifecycle, entity, flow and manifest checks |
| `sas-filter-change`    | Invariants and tests for filter math changes   |
| `sas-code-quality`     | Quality gates                                  |
| `sas-translation-sync` | en/da sync and glossary                        |
| `sas-doc-sync`         | Keep docs and wiki in sync                     |
| `sas-issue-creation`   | Issue format and labels                        |
| `sas-pr-workflow`      | PR format, scope and merge rules               |
| `code-review`          | Review checklist                               |

## Release

1. Merge PRs with correct labels (`bug`, `enhancement`, `breaking-change`, `major`/`minor`/`patch`).
2. Review the draft release made by Release Drafter.
3. Publish it. `release.yml` writes the version into `manifest.json` and uploads the zip for HACS.
