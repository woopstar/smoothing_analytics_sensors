---
name: sas-pre-flight
description: Run before starting any SAS code change. Fetch origin, create a dedicated git worktree and feature branch, read repository memory and the relevant docs.
---

# SAS Pre-Flight — Start Any Code Change

Activate this skill **before writing any code**: bug fix, feature, refactor or docs change.

## Step 1: Create a Worktree and Feature Branch

Never work directly in the main checkout on `main`. Several agent sessions may share it.
Give every task its own worktree:

```bash
git fetch origin
git worktree add ../sas-worktrees/sas-<issue> -b <type>/<issue>-<slug> origin/main
cd ../sas-worktrees/sas-<issue>
git config core.fileMode false   # OneDrive/iCloud checkouts flip the exec bit
```

- Branch from `origin/main` unless the user says otherwise.
- If `worktree add` fails because the branch is checked out elsewhere, another session owns
  it. Inspect it (`git worktree list`) before touching it.
- Don't use `git stash`. The stash is shared by every worktree. Commit work in progress.

## Step 2: Read Repository Memory

Read `.github/memories.md`: module map, sensor stack, config keys, canonical patterns,
known pitfalls.

## Step 3: Read the Issue

For issue-driven work, read the full issue first: `rtk gh issue view <n>`.
Issues from the November 2026 review carry the `review-2026-11` label and a
"Suggested Prompt" section.

## Step 4: Branch Naming

`<type>/<issue-number>-<slug>`

| Type       | Use for           |
| ---------- | ----------------- |
| `feat`     | New features      |
| `fix`      | Bug fixes         |
| `chore`    | Repository chores |
| `docs`     | Documentation     |
| `refactor` | Refactoring       |
| `perf`     | Performance       |
| `test`     | Tests             |
| `ci`       | CI/CD             |

Examples: `fix/53-unsubscribe-listeners`, `feat/60-reconfigure-flow`

## Step 5: Read the Relevant Docs

| Change touches                        | Must read                        |
| ------------------------------------- | -------------------------------- |
| Lowpass, median, EMA math or stacking | `docs/filter-math.md`            |
| Config or options flow                | `docs/configuration.md`          |
| Entities, attributes, unique IDs      | `docs/sensors-reference.md`      |
| Setup, unload, listeners, manifest    | `.rules/ha-development-rules.md` |

## Step 6: Understand the Affected Code

Search and read the source files. Do not guess paths.

## One Issue Per Branch

Solve one issue per branch and PR. Do not refactor unrelated code.
