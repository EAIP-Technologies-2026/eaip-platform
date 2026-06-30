#!/usr/bin/env bash
# =============================================================================
# EAIP — Repository health check
# -----------------------------------------------------------------------------
# Read-only validation that the working tree is consistent and the toolchain
# is in good shape. Safe to run inside CI; never mutates files.
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ---- Output helpers ---------------------------------------------------------
if [ -t 1 ]; then
  C_GREEN='\033[32m'; C_RED='\033[31m'; C_YELLOW='\033[33m'; C_BOLD='\033[1m'; C_RESET='\033[0m'
else
  C_GREEN=''; C_RED=''; C_YELLOW=''; C_BOLD=''; C_RESET=''
fi
ok()   { printf "  ${C_GREEN}✓${C_RESET} %s\n" "$*"; }
fail() { printf "  ${C_RED}✗${C_RESET} %s\n" "$*"; FAILURES=$((FAILURES + 1)); }
warn() { printf "  ${C_YELLOW}!${C_RESET} %s\n" "$*"; }
section() { printf "\n${C_BOLD}%s${C_RESET}\n" "$*"; }

FAILURES=0
PYTHON="${PYTHON:-python3}"

# =============================================================================
section "Repository structure"
# =============================================================================
REQUIRED_DOCS=(
  README.md CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md SUPPORT.md
  CHANGELOG.md ROADMAP.md ARCHITECTURE.md ENGINEERING_TRACKER.md
  DECISION_REGISTER.md TECH_DEBT.md RISK_REGISTER.md VERSIONING.md
  LICENSE pyproject.toml Makefile DEVELOPER_GUIDE.md
)
for f in "${REQUIRED_DOCS[@]}"; do
  if [ -f "$f" ]; then ok "$f"; else fail "$f missing"; fi
done

REQUIRED_DIRS=(src/eaip tests .github .vscode .devcontainer scripts)
for d in "${REQUIRED_DIRS[@]}"; do
  if [ -d "$d" ]; then ok "$d/"; else fail "$d/ missing"; fi
done

# =============================================================================
section "Foundation package layout (EP-0002)"
# =============================================================================
EXPECTED_PKGS=(
  shared exceptions types protocols interfaces metadata version utilities
  serialization validation config settings logging events factories
  dependency_injection registry lifecycle capabilities plugins ports
  infrastructure adapters core platform application
)
for p in "${EXPECTED_PKGS[@]}"; do
  if [ -d "src/eaip/$p" ] && [ -f "src/eaip/$p/__init__.py" ]; then
    ok "eaip.$p"
  else
    fail "eaip.$p missing or empty"
  fi
done

# =============================================================================
section "Toolchain"
# =============================================================================
if command -v "$PYTHON" >/dev/null 2>&1; then
  pyver=$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  case "$pyver" in
    3.11|3.12|3.13) ok "Python $pyver";;
    *) fail "Python $pyver (require 3.11–3.13)";;
  esac
else
  fail "Python interpreter not found ($PYTHON)"
fi

for tool in git make; do
  if command -v "$tool" >/dev/null 2>&1; then ok "$tool"; else warn "$tool not on PATH"; fi
done

# =============================================================================
section "Configuration files parse cleanly"
# =============================================================================
"$PYTHON" - <<'PY'
import json, sys, tomllib, pathlib
errors = []
for f in pathlib.Path('.').rglob('*'):
    if any(part.startswith('.') and part not in {'.github', '.vscode', '.devcontainer', '.pre-commit-config.yaml'.split('.')[0]} for part in f.parts):
        continue
    if any(part in {'.venv', 'node_modules', 'htmlcov', '__pycache__'} for part in f.parts):
        continue
    if f.is_file():
        try:
            if f.suffix == '.toml':
                tomllib.load(f.open('rb'))
            elif f.suffix == '.json' and 'secrets.baseline' not in str(f):
                # detect-secrets baseline + .vscode JSON-with-comments handled separately
                if '.vscode' not in str(f):
                    json.loads(f.read_text())
        except Exception as e:
            errors.append((str(f), str(e)))
for path, err in errors:
    print(f"INVALID {path}: {err}")
sys.exit(1 if errors else 0)
PY
if [ $? -eq 0 ]; then ok "all TOML/JSON files parse"; else fail "some config files invalid"; fi

# =============================================================================
section "Python sources have no import-time side effects"
# =============================================================================
if [ -d .venv ]; then
  # shellcheck disable=SC1091
  . .venv/bin/activate 2>/dev/null || true
fi
PYTHONPATH=src "$PYTHON" - <<'PY'
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
PY
if [ $? -eq 0 ]; then ok "all 27 EAIP packages import cleanly"; else fail "import failures"; fi

# =============================================================================
section "Summary"
# =============================================================================
if [ "$FAILURES" -eq 0 ]; then
  printf "${C_GREEN}${C_BOLD}HEALTHY${C_RESET} — repository passes every health check.\n"
  exit 0
else
  printf "${C_RED}${C_BOLD}UNHEALTHY${C_RESET} — %d failure(s).\n" "$FAILURES"
  exit 1
fi
