---
name: sas-pr-workflow
description: Activate when creating, updating or merging a pull request for SAS. Covers Conventional Commits, PR description, quality gates, docs and translation sync, and merge rules.
---

# SAS Pull Request Workflow

## Pre-PR Checklist

```bash
./scripts/quality.sh all
git --no-optional-locks status
```

### Branch Sanity Check

```bash
git fetch origin
git merge-base --is-ancestor origin/main HEAD && echo "based on origin/main"
git reflog -3
```

If `main` moved on, `git rebase origin/main` in your worktree and re-run the gates.

## Translation and Docs Sync

- Run `sas-translation-sync` if any user-facing string changed.
- Run `sas-doc-sync`. A PR is not done until docs match the code.

## Commit Messages

`<type>(<scope>): <description>`

```
fix(sensor): unsubscribe state listeners on removal — Fixes #53
```

## PR Title and Body

Title: Conventional Commits (checked by `semantic-title.yml`, labeled by `auto-label.yml`).

Body must include:

- Summary
- What changed and why
- Files changed
- Tests added or updated
- Gate results
- User-visible impact (changed values, entity IDs, attributes)
- `Fixes #<n>`

Pass the body with `--body-file`.

```bash
gh pr create --base main --title "<title>" --body-file /tmp/pr.md
```

## Scope Rules

- [ ] One issue per PR
- [ ] No feature creep
- [ ] No mixed cleanups

## Keeping a PR Up to Date

After every follow-up commit, update title and body: `gh pr edit <n> --body-file /tmp/pr.md`.

## Labels That Matter

- `pr-on-hold` blocks merge (`check-on-hold.yml`).
- `breaking-change`, `major`, `minor`, `patch` drive Release Drafter versioning.
- `skip-changelog` hides the PR from release notes.

## Merge Rules

- [ ] All CI checks green
- [ ] Docs and translations consistent
- [ ] **Explicit permission from the maintainer**

After merge:

```bash
git worktree remove ../sas-worktrees/sas-<issue>
git branch -D <type>/<issue>-<slug>
git worktree prune
```
