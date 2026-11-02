#!/usr/bin/env bash
# Quality gates for Smoothing Analytics Sensors.
# Local runs, the pre-commit hook and CI all go through this script.
set -euo pipefail

cd "$(dirname "$0")/.." || exit

# Prefer the venv created by scripts/setup.sh. Set SAS_VENV to keep it outside
# a synced folder (OneDrive/iCloud), e.g. SAS_VENV=~/.cache/sas/venv.
VENV_DIR="${SAS_VENV:-.venv}"
if [[ -d "${VENV_DIR}/bin" ]]; then
    PATH="$(cd "${VENV_DIR}" && pwd)/bin:$PATH"
fi
if [[ -d "$HOME/.local/bin" ]]; then
    PATH="$HOME/.local/bin:$PATH"
fi

# Run a command through rtk when available, otherwise run it directly.
run() {
    if command -v rtk >/dev/null 2>&1; then
        rtk "$@"
    else
        "$@"
    fi
}

PRETTIER_VERSION="3.1.0"

# Usage: prettier_run --write | --check
prettier_run() {
    local mode="$1"
    if ! command -v npx >/dev/null 2>&1; then
        if [[ "${mode}" == "--check" ]]; then
            echo "[error] npx not found — cannot verify prettier formatting" >&2
            return 1
        fi
        echo "[warn] npx not found — skipping prettier (CI will still check it)" >&2
        return 0
    fi
    run npx --yes "prettier@${PRETTIER_VERSION}" "${mode}" .
}

usage() {
    cat <<USAGE
Usage: quality.sh <command>

Commands:
  lint          ruff format + ruff check --fix + prettier --write
  format-check  Verify ruff format, ruff lint and prettier without writing (CI)
  typing        mypy
  translations  Validate en/da translation files stay in sync
  validate      Validate YAML and JSON files
  test          pytest with coverage (extra args are passed to pytest)
  all           lint, validate, translations, typing and test
USAGE
    exit 1
}

case "${1:-}" in
    lint)
        run ruff format .
        run ruff check . --fix
        prettier_run --write
        ;;
    format-check)
        run ruff format --check .
        run ruff check .
        prettier_run --check
        ;;
    typing)
        run mypy custom_components
        ;;
    translations)
        python3 scripts/validate_translations.py
        ;;
    validate)
        python3 scripts/validate-yaml.py
        python3 scripts/validate-json.py
        ;;
    test)
        run python -m pytest tests/ \
            --timeout=60 \
            --cov=custom_components \
            --cov-report=xml \
            --cov-report=term-missing \
            --junitxml=test-results.xml \
            "${@:2}"
        ;;
    all)
        "$0" lint
        "$0" validate
        "$0" translations
        "$0" typing
        "$0" test
        ;;
    *)
        usage
        ;;
esac
