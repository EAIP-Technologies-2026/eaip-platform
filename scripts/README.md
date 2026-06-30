# `scripts/`

Cross-platform developer scripts. All Bash scripts are POSIX-friendly with
strict mode (`set -euo pipefail`); the PowerShell script targets PowerShell
5.1+ and PowerShell 7+.

| Script | Purpose | Platforms |
| ------ | ------- | --------- |
| `bootstrap.sh` | One-command setup: creates `.venv`, installs `[dev,test]` extras, installs pre-commit hooks. Idempotent. | Linux · macOS · WSL |
| `bootstrap.ps1` | Same, for Windows hosts. | Windows |
| `healthcheck.sh` | Read-only verification that the repo tree, toolchain, and Foundation packages are intact. | Linux · macOS · WSL |
| `validate.sh` | Local pre-flight: ruff (lint + format), black, mypy, pytest. Activates `.venv` if present. | Linux · macOS · WSL |
| `validate-docs.sh` | Walks every Markdown file checking internal links, governance-doc presence, and per-package READMEs. | Linux · macOS · WSL |
| `diagnostics.sh` | Concise environment snapshot suitable for bug reports — never mutates files. | Linux · macOS · WSL |

## Invocation

```bash
# One-command developer setup (Linux/macOS/WSL)
bash scripts/bootstrap.sh

# Windows
pwsh -File scripts/bootstrap.ps1

# Health, validation, diagnostics
make health        # → scripts/healthcheck.sh
make validate      # → scripts/validate.sh
make validate-docs # → scripts/validate-docs.sh
make diagnostics   # → scripts/diagnostics.sh
```

All scripts honour these environment variables:

* `PYTHON` — explicit interpreter to use (default: first of `python3.13 / python3.12 / python3.11 / python3`).
* `VENV` — virtualenv directory (default: `.venv`).

## Conventions

* Idempotent. Safe to re-run.
* Read-only by default; only `bootstrap.*` mutates the working tree (creates `.venv`, installs packages).
* Exit code `0` on success, non-zero on failure. Designed for CI consumption.
