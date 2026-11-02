---
name: code-review
description: Activate when reviewing code changes, diffs, or pull requests to identify high-confidence bugs, regressions, security issues, and correctness problems.
---

# Code Review Skill

Activate this skill when the user asks for a code review, PR review, or diff review.

## Review Goals

- Focus on correctness, regressions, security, data loss, and broken tests.
- Report only high-confidence findings.
- Ignore style nits and trivial issues unless they hide a bug.
- Prefer the smallest actionable set of findings.

## Review Workflow

1. Read the diff and relevant surrounding code.
2. Trace call paths and invariants.
3. Check tests, types, and behavior changes.
4. Compare against repository conventions and docs when the change affects them.
5. Summarize findings with severity, rationale, and exact file and line references.

## SAS-Specific Checks

- If the change touches filter math, read `docs/filter-math.md` and check the coefficient
  stays in `0 < k <= 1` for every `dt`, including `dt = 0` and a gap of hours.
- Every `async_track_*` call must be wrapped in `async_on_remove` / `async_on_unload`.
- Setup → unload → setup must leave one listener per entity, not two.
- unique_id changes need `async_migrate_entry`.
- Translations: `en.json` and `da.json` must have the same keys.
- Verify affected tests exist or are updated.

## Output Format

- Start with an overall assessment.
- List findings sorted by severity.
- For each finding, include:
  - file path
  - line number or lines
  - concise explanation
  - why it matters
- If no issues are found, say so explicitly.
