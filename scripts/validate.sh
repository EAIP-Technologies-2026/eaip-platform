#!/usr/bin/env bash
# =============================================================================
# EAIP — Local pre-flight validation (format / lint / typecheck / test)
# -----------------------------------------------------------------------------
# Run this before pushing to make sure CI will pass. Equivalent to `make check`
# with friendlier output. Activates .venv if present.
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [ -t 1 ]; then
  C_CYAN='\033[36m'; C_GREEN='\033[32m'; C_RED='\033[31m'; C_BOLD='\033[1m'; C_RESET='\033[0m'
else
  C_CYAN=''; C_GREEN=''; C_RED=''; C_BOLD=''; C_RESET=''
fi
step()    { printf "\n${C_CYAN}${C_BOLD}▶ %s${C_RESET}\n" "$*"; }
ok()      { printf "${C_GREEN}${C_BOLD}✓ %s${C_RESET}\n" "$*"; }
fail()    { printf "${C_RED}${C_BOLD}✗ %s${C_RESET}\n" "$*"; }

if [ -d .venv ]; then
  # shellcheck disable=SC1091
  . .venv/bin/activate
fi

PY=${PY:-python}
EXIT=0

step "ruff (lint)"
"$PY" -m ruff check src tests || EXIT=1

step "ruff (format)"
"$PY" -m ruff format --check src tests || EXIT=1

step "black"
"$PY" -m black --check src tests || EXIT=1

step "mypy"
"$PY" -m mypy --config-file pyproject.toml || EXIT=1

step "pytest"
PYTHONPATH=src "$PY" -m pytest tests -q || EXIT=1

echo
if [ "$EXIT" -eq 0 ]; then
  ok "Local validation passed. Safe to push."
else
  fail "Validation failed. Fix issues above before pushing."
fi
exit "$EXIT"
