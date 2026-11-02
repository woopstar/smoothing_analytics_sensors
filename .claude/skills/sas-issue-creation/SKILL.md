---
name: sas-issue-creation
description: Activate when creating a new GitHub issue for SAS. Ensures a Conventional Commits title, a detailed description with file:line references, a proposed solution, acceptance criteria, a tailored fix prompt, and labels.
---

# SAS Issue Creation

## Step 1: Investigate Before Drafting

Read the code before writing the issue. Cite concrete `file:line` references.

## Step 2: Title — Conventional Commits

`<type>(<scope>): <description>`

Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `perf`, `test`, `ci`
Scopes: `sensor`, `ema`, `lowpass`, `median`, `flow`, `setup`, `manifest`, `docs`, `ci`

```
fix(sensor): unsubscribe state listeners on entity removal
feat(flow): add reconfigure step to change the input sensor
```

## Step 3: Body — Required Sections, in Order

```markdown
## Description

<What happens, why it is wrong or missing, where it lives (file:line), root cause.>

## Possible Solution

<Concrete approach. Name functions/files. Note trade-offs and recommend one.>

## Acceptance Criteria

- [ ] <Testable condition>
- [ ] <Edge case>
- [ ] Tests added/updated
- [ ] `./scripts/quality.sh all` passes

## Suggested Prompt

\`\`\`
<Ready-to-run prompt for a fresh session: files, expected behavior, pointer to the
sas-pre-flight skill and the quality gates.>
\`\`\`
```

## Step 4: Labels

Check current labels: `rtk gh label list`. Apply:

1. One type label: `bug`, `enhancement` or `chore` (`documentation` for docs-only).
2. One `area:*` label: `area:filters`, `area:lifecycle`, `area:config`,
   `area:home-assistant`, `area:tests`, `area:docs`, `area:ci`, `area:refactor`.
3. Optional: `priority:p0` (wrong values, leaks, broken setup), `priority:p1`,
   `breaking-change`.

Do not invent labels. Add new ones to `.github/sync-labels.yml` first.

## Step 5: Create

```bash
gh issue create --title "<title>" --body-file /tmp/issue.md --label bug --label area:lifecycle
```

## Step 6: Verify

`rtk gh issue view <n>`: title parses, four sections present, labels applied.
