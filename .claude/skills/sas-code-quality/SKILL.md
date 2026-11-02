---
name: sas-code-quality
description: Activate before every commit and PR to run the SAS quality gates — lint, typing, translations and tests.
---

# SAS Code Quality — Pre-Commit & Pre-PR Gates

## Gates — All Must Pass

```bash
./scripts/quality.sh lint          # ruff format + ruff check --fix + prettier --write
./scripts/quality.sh typing        # mypy
./scripts/quality.sh translations  # en.json vs da.json
./scripts/quality.sh test          # pytest with coverage
```

Or all at once:

```bash
./scripts/quality.sh all
```

CI runs `./scripts/quality.sh format-check` (no writes) plus `typing`, `translations` and
`test`. A diff from `lint` that you did not commit fails CI.

First time on a machine: `./scripts/setup.sh` creates `.venv` with the pinned tooling.

## Faster Iteration

```bash
./scripts/quality.sh test tests/test_filters.py
./scripts/quality.sh test tests/test_filters.py::test_lowpass_first_sample
```

## Standards Quick Reference

- Type hints on public functions, `X | None`
- Google-style docstrings
- `@override` on overridden HA methods
- `%`-formatting in logging
- `pytest.approx()` for floats in tests, `math.isclose()` in code
- Import order: stdlib → third-party → `homeassistant` → first-party (ruff enforces it)

## Verify Before Commit

```bash
git --no-optional-locks status
```

Only intended changes. No `.venv`, `coverage.xml` or `test-results.xml`.
