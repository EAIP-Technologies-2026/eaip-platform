#!/usr/bin/env bash
# =============================================================================
# EAIP — Repository diagnostics
# -----------------------------------------------------------------------------
# Prints a concise environment snapshot suitable for pasting into bug reports.
# Read-only.
# =============================================================================

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit

print_kv() { printf "  %-22s %s\n" "$1" "$2"; }

echo "============================================================"
echo " EAIP Repository Diagnostics"
echo "============================================================"
print_kv "Date (UTC):"    "$(date -u '+%Y-%m-%d %H:%M:%S')"
print_kv "Working dir:"   "$(pwd)"
print_kv "Operating system:"  "$(uname -s) $(uname -r) ($(uname -m))"

if command -v git >/dev/null 2>&1 && [ -d .git ]; then
    print_kv "Git branch:"    "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
    print_kv "Git commit:"    "$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
    print_kv "Git status:"    "$(git status --porcelain | wc -l | tr -d ' ') uncommitted change(s)"
else
    print_kv "Git:"           "not a git checkout"
fi

PY=${PYTHON:-python3}
if command -v "$PY" >/dev/null 2>&1; then
    print_kv "Python:"        "$($PY --version 2>&1) → $(command -v "$PY")"
else
    print_kv "Python:"        "NOT FOUND"
fi

print_kv "Make:"              "$(command -v make 2>/dev/null || echo absent)"
print_kv "Docker:"            "$(command -v docker 2>/dev/null || echo absent)"
print_kv "Pre-commit:"        "$(command -v pre-commit 2>/dev/null || echo absent)"

echo ""
echo "------------------------------------------------------------"
echo " Project metrics"
echo "------------------------------------------------------------"
print_kv "Source files:"    "$(find src/eaip -name '*.py' 2>/dev/null | wc -l | tr -d ' ')"
print_kv "Test files:"      "$(find tests -name 'test_*.py' 2>/dev/null | wc -l | tr -d ' ')"
print_kv "Doc files (root):" "$(find . -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
print_kv "Per-package READMEs:" "$(find src/eaip -name 'README.md' 2>/dev/null | wc -l | tr -d ' ')"

if [ -d .venv ]; then
    print_kv "Virtualenv:"    ".venv (present)"
else
    print_kv "Virtualenv:"    "absent — run scripts/bootstrap.sh"
fi

echo ""
echo "------------------------------------------------------------"
echo " Installed key packages (if venv activated)"
echo "------------------------------------------------------------"
if [ -d .venv ]; then
    # shellcheck disable=SC1091
    . .venv/bin/activate 2>/dev/null || true
fi
for pkg in pydantic pydantic-settings structlog anyio ruff black mypy pytest; do
    if "$PY" -m pip show "$pkg" >/dev/null 2>&1; then
        ver=$("$PY" -m pip show "$pkg" 2>/dev/null | awk '/^Version:/ {print $2}')
        print_kv "$pkg:" "$ver"
    else
        print_kv "$pkg:" "not installed"
    fi
done

echo "============================================================"
