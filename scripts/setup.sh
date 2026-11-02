#!/usr/bin/env bash
# Create .venv with the pinned lint, typing and test tooling.
set -euo pipefail

cd "$(dirname "$0")/.." || exit

PYTHON_VERSION="$(cat .python-version)"
# Set SAS_VENV to keep the venv outside a synced folder (OneDrive/iCloud).
VENV_DIR="${SAS_VENV:-.venv}"

if command -v uv >/dev/null 2>&1; then
    uv venv --python "${PYTHON_VERSION}" "${VENV_DIR}"
    uv pip install --python "${VENV_DIR}/bin/python" -r requirements_lint.txt -r requirements_test.txt
else
    python3 -m venv "${VENV_DIR}"
    "${VENV_DIR}/bin/pip" install --upgrade pip
    "${VENV_DIR}/bin/pip" install -r requirements_lint.txt -r requirements_test.txt
fi

echo "Done. Run ./scripts/quality.sh all"
