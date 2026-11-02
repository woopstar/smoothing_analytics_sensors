# Custom GitHub Copilot Instructions

## Read First

1. `.github/memories.md` — module map, canonical patterns, known pitfalls.
2. `AGENTS.md` — workflow, scope and quality rules.
3. `.rules/ha-development-rules.md` — Home Assistant compliance checklist. Read before every PR.

## Quality Gates

```bash
./scripts/quality.sh lint
./scripts/quality.sh typing
./scripts/quality.sh test
./scripts/quality.sh all
```

## Conventions

- Conventional Commits for commits, PR titles and issue titles.
- Branch: `<type>/<issue>-<slug>` from `origin/main`.
- `en.json` is the translation source of truth. `da.json` must stay in sync.
- Docs in `docs/` sync to the wiki on merge to `main`. Update them in the same PR.
