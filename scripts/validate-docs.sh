#!/usr/bin/env bash
# =============================================================================
# EAIP — Documentation link & reference validator
# -----------------------------------------------------------------------------
# Walks the documentation tree looking for:
#   • internal links to files that don't exist
#   • required cross-references between governance documents
#   • missing per-package READMEs under src/eaip/
# Read-only.
# =============================================================================

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit

PY=${PYTHON:-python3}
"$PY" - <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(".").resolve()
DOC_GLOB = ["*.md", "src/eaip/**/README.md"]

# Match Markdown links of the form [text](target). The validator strips fenced
# code blocks (```...```) and inline code spans (`...`) BEFORE running this
# regex so embedded code with `[...](...)`-shaped syntax does not produce
# false positives.
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+?)(?:#[^)]*)?\)")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
CODE_SPAN_RE = re.compile(r"`[^`\n]*`")


def strip_code(text: str) -> str:
    text = FENCE_RE.sub("", text)
    text = CODE_SPAN_RE.sub("", text)
    return text


failures: list[str] = []
checked = 0

doc_files: list[Path] = []
for pattern in DOC_GLOB:
    doc_files.extend(ROOT.glob(pattern))

# 1. Internal link integrity
for md in doc_files:
    text = strip_code(md.read_text(encoding="utf-8"))
    for match in LINK_RE.finditer(text):
        target = match.group(1).strip()
        # Skip empty links, external URLs, and pure-anchor in-page links.
        if not target or target.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            continue
        candidate = (md.parent / target).resolve()
        checked += 1
        if not candidate.exists():
            failures.append(f"{md.relative_to(ROOT)}: broken link → {target}")

# 2. Required governance docs exist
required = [
    "README.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md",
    "SUPPORT.md", "CHANGELOG.md", "ROADMAP.md", "ARCHITECTURE.md",
    "ENGINEERING_TRACKER.md", "DECISION_REGISTER.md", "TECH_DEBT.md",
    "RISK_REGISTER.md", "VERSIONING.md", "LICENSE", "DEVELOPER_GUIDE.md",
]
for name in required:
    if not (ROOT / name).exists():
        failures.append(f"missing required doc: {name}")

# 3. Every source package has a README
src_pkgs = sorted(
    p for p in (ROOT / "src" / "eaip").iterdir()
    if p.is_dir() and not p.name.startswith("__")
)
for pkg in src_pkgs:
    if not (pkg / "README.md").exists():
        failures.append(f"src/eaip/{pkg.name}/README.md missing")

# Summary
if failures:
    print(f"DOC VALIDATION FAILED — {len(failures)} issue(s):")
    for line in failures:
        print(f"  ✗ {line}")
    sys.exit(1)
print(
    f"DOC VALIDATION OK — {checked} internal link(s) checked, "
    f"{len(src_pkgs)} package(s) verified, all required docs present."
)
PY
