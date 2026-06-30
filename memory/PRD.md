# EAIP Platform — PRD

**Repository:** `subham1902/eaip-platform`
**Owner:** Subham Panigrahi (@subham1902)
**License:** Apache-2.0
**Status:** EP-0001A complete (repository foundation)
**Last updated:** 2026-01-15

## Original Problem Statement

> Generate EP-0001A for the EAIP platform repository. Implement every repository foundation file in production-ready quality. Generate complete file-by-file contents for README.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, SUPPORT.md, CHANGELOG.md, ROADMAP.md, ARCHITECTURE.md, ENGINEERING_TRACKER.md, DECISION_REGISTER.md, TECH_DEBT.md, RISK_REGISTER.md, VERSIONING.md, LICENSE, .editorconfig, .gitattributes, .gitignore, pyproject.toml, Makefile, pre-commit configuration, VS Code configuration (.vscode), GitHub ISSUE_TEMPLATE files, pull_request_template.md, CODEOWNERS, and a starter GitHub Actions workflow.

## User Choices

- **Acronym:** EAIP = Enterprise Autonomous Intelligence Platform
- **Repo:** `subham1902/eaip-platform`
- **Maintainer:** Subham Panigrahi (@subham1902)
- **Copyright:** © 2026 Subham Panigrahi
- **License:** Apache 2.0
- **Python:** 3.11, 3.12, 3.13
- **Tooling:** ruff + black + mypy + pytest
- **CI scope:** lint + test + security scan + build + release automation (EP-0001B)

## Architecture / Task Summary

EP-0001A delivers **repository scaffolding & governance only** — no runtime source code (lands in EP-0002).

## What's Been Implemented (2026-01-15)

### Governance docs (root)
- `README.md` (rewritten), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1)
- `SECURITY.md` (coordinated disclosure), `SUPPORT.md`
- `CHANGELOG.md` (Keep-a-Changelog 1.1.0), `ROADMAP.md` (rolling 4-quarter)
- `ARCHITECTURE.md`, `ENGINEERING_TRACKER.md`, `DECISION_REGISTER.md` (10 ADRs seeded)
- `TECH_DEBT.md` (10 entries), `RISK_REGISTER.md` (10 risks), `VERSIONING.md` (SemVer 2.0.0)
- `LICENSE` (Apache-2.0 full text)

### Tooling / hygiene
- `.editorconfig`, `.gitattributes`, `.gitignore` (Python/Node/IDE/OS-aware)
- `pyproject.toml` (hatchling build; ruff, black, mypy --strict, pytest, coverage, bandit configured)
- `Makefile` (bootstrap, fmt, lint, typecheck, test, check, audit, clean, distclean, help)
- `.pre-commit-config.yaml` (hygiene, ruff, black, mypy, detect-secrets, markdownlint, yamlfmt, shellcheck, actionlint, conventional-pre-commit)
- `.secrets.baseline` (detect-secrets stub)

### Editor / IDE
- `.vscode/settings.json`, `.vscode/extensions.json`, `.vscode/launch.json`

### GitHub
- `.github/ISSUE_TEMPLATE/{bug_report,feature_request,documentation,config}.yml`
- `.github/pull_request_template.md`
- `.github/CODEOWNERS`
- `.github/workflows/ci.yml` (pre-commit + lint + 3.11/3.12/3.13 × ubuntu/mac/win matrix + build + aggregator)
- `.github/workflows/security.yml` (bandit + pip-audit + gitleaks; weekly schedule)
- `.github/gitleaks.toml`, `.github/dependabot.yml`

### Validation
- All TOML, YAML, JSON files parsed and validated.

## Backlog

- **P0 (EP-0001B):** CI caching tuning, release-please integration, signed releases.
- **P0 (EP-0002):** Runtime skeleton in `src/eaip/runtime/`.
- **P1 (EP-0003):** LLM adapter contract + 2 reference adapters.
- **P1 (EP-0004):** OpenTelemetry baseline + structlog config.
- **P2:** Docs site (MkDocs Material), SBOM/cosign signing, threat model.

## Next Tasks

1. Begin EP-0001B — automate releases (release-please, sigstore), add caching.
2. Begin EP-0002 — orchestrator/Run/Step skeleton + first unit tests.
3. Recruit additional maintainers (TD-0007 / R-0003).
