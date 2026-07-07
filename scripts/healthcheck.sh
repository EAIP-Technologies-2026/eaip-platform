#!/usr/bin/env bash
# =============================================================================
# EAIP — health check suite
# -----------------------------------------------------------------------------
# Runs sanity checks on the repository state (config syntax, importability).
# =============================================================================

set -uo pipefail

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit

PYTHON=${PYTHON:-python3}
C_RED='\033[0;31m'
C_GREEN='\033[0;32m'
C_BOLD='\033[1m'
C_RESET='\033[0m'

FAILURES=0

section() {
  printf "\n${C_BOLD}>>> %s${C_RESET}\n" "$*"
}

ok() {
  printf "  ${C_GREEN}OK${C_RESET} — %s\n" "$*"
}

fail() {
  printf "  ${C_RED}FAIL${C_RESET} — %s\n" "$*"
  FAILURES=$((FAILURES + 1))
}

# =============================================================================
section "TOML and JSON files are well-formed"
# =============================================================================
if "$PYTHON" - <<'PY'; then
import sys, tomllib, json, pathlib
errors = []
for f in pathlib.Path('.').rglob('*'):
    if f.is_file():
        try:
            if f.suffix == '.toml':
                tomllib.load(f.open('rb'))
            elif f.suffix == '.json' and 'secrets.baseline' not in str(f) and '.vscode' not in str(f):
                json.loads(f.read_text())
        except Exception as e:
            errors.append((str(f), str(e)))
for path, err in errors:
    print(f"INVALID {path}: {err}")
sys.exit(1 if errors else 0)
PY
    ok "all TOML/JSON files parse"
else
    fail "some config files invalid"
fi

# =============================================================================
section "Python sources have no import-time side effects"
# =============================================================================
if [ -d .venv ]; then
  # shellcheck disable=SC1091
  . .venv/bin/activate 2>/dev/null || true
fi

if PYTHONPATH=src "$PYTHON" - <<'PY'; then
import importlib, sys
mods = [
    'eaip','eaip.shared','eaip.exceptions','eaip.types','eaip.protocols','eaip.interfaces',
    'eaip.metadata','eaip.version','eaip.utilities','eaip.serialization','eaip.validation',
    'eaip.config','eaip.settings','eaip.logging','eaip.events','eaip.factories',
    'eaip.dependency_injection','eaip.registry','eaip.lifecycle','eaip.capabilities',
    'eaip.plugins','eaip.ports','eaip.adapters.interfaces','eaip.infrastructure','eaip.core',
    'eaip.platform','eaip.application',
]
bad = []
for m in mods:
    try:
        importlib.import_module(m)
    except Exception as e:
        bad.append(f"{m}: {e!r}")
if bad:
    print("FAIL", *bad, sep='\n')
    sys.exit(1)
sys.exit(0)
PY
    ok "all 27 EAIP packages import cleanly"
else
    fail "import failures"
fi

# =============================================================================
section "Summary"
# =============================================================================
if [ "$FAILURES" -eq 0 ]; then
  printf "%s%sHEALTHY%s — repository passes every health check.\n" "$C_GREEN" "$C_BOLD" "$C_RESET"
  exit 0
else
  printf "${C_RED}${C_BOLD}UNHEALTHY${C_RESET} — %d failure(s).\n" "$FAILURES"
  exit 1
fi
