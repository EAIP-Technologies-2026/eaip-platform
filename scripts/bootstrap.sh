#!/usr/bin/env bash
# =============================================================================
# EAIP — One-command developer bootstrap (Linux / macOS / WSL)
# -----------------------------------------------------------------------------
# Creates .venv, installs the project in editable mode with [dev,test] extras,
# installs pre-commit hooks. Idempotent — safe to re-run.
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ---- Colour helpers ----------------------------------------------------------
if [ -t 1 ]; then
  C_CYAN='\033[36m'; C_GREEN='\033[32m'; C_YELLOW='\033[33m'; C_RED='\033[31m'; C_RESET='\033[0m'
else
  C_CYAN=''; C_GREEN=''; C_YELLOW=''; C_RED=''; C_RESET=''
fi
say()  { printf "${C_CYAN}→ %s${C_RESET}\n"  "$*"; }
ok()   { printf "${C_GREEN}✓ %s${C_RESET}\n" "$*"; }
warn() { printf "${C_YELLOW}! %s${C_RESET}\n" "$*"; }
die()  { printf "${C_RED}✗ %s${C_RESET}\n" "$*" >&2; exit 1; }

# ---- Locate Python ----------------------------------------------------------
PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
  for cand in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then PYTHON="$cand"; break; fi
  done
fi
[ -n "$PYTHON" ] || die "No Python 3.11+ found on PATH. Set PYTHON=/path/to/python."

ver=$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
case "$ver" in
  3.11|3.12|3.13) ok "Python $ver detected ($PYTHON)";;
  *) die "Python $ver is unsupported. EAIP requires 3.11, 3.12, or 3.13.";;
esac

# ---- Create venv ------------------------------------------------------------
VENV="${VENV:-.venv}"
if [ ! -d "$VENV" ]; then
  say "Creating virtualenv at $VENV"
  "$PYTHON" -m venv "$VENV"
else
  say "Reusing existing virtualenv at $VENV"
fi
# shellcheck disable=SC1091
. "$VENV/bin/activate"

# ---- Install ----------------------------------------------------------------
say "Upgrading pip / wheel / setuptools"
python -m pip install --quiet --upgrade pip wheel setuptools

say "Installing project (dev + test extras)"
python -m pip install --quiet -e ".[dev,test]"

# ---- Pre-commit -------------------------------------------------------------
if command -v pre-commit >/dev/null 2>&1 || python -m pre_commit --version >/dev/null 2>&1; then
  say "Installing pre-commit hooks"
  pre-commit install --install-hooks >/dev/null
  pre-commit install --hook-type commit-msg >/dev/null
else
  warn "pre-commit not on PATH — skipping hook install"
fi

ok "Bootstrap complete."
echo
echo "Next steps:"
echo "  source $VENV/bin/activate"
echo "  make help"
echo "  make check       # run all quality gates"
