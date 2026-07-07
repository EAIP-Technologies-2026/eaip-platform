# EAIP — Enterprise Autonomous Intelligence Platform

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python Versions](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](pyproject.toml)
[![Code Style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linter: ruff](https://img.shields.io/badge/lint-ruff-46aef7.svg)](https://github.com/astral-sh/ruff)
[![Type Checker: mypy](https://img.shields.io/badge/types-mypy-blue.svg)](<http://mypy-lang.org/>)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen)](https://pre-commit.com/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://www.conventionalcommits.org)

> **Status:** 🚧 Foundation (EP-0001A) — repository scaffolding & governance complete; runtime services land in subsequent engineering packages (EP-0002 onwards).

EAIP is an open, modular platform for building, orchestrating, and operating **autonomous intelligent agents** at enterprise scale. It is designed around three principles:

1. **Composable** — agents, tools, memory, and policies are first-class building blocks.
2. **Observable** — every decision, prompt, tool call, and state transition is auditable.
3. **Governed** — security, compliance, cost, and safety are built in, not bolted on.

---

## Table of Contents

- [Why EAIP](#why-eaip)
- [Architecture at a Glance](#architecture-at-a-glance)
- [Quickstart](#quickstart)
- [Repository Layout](#repository-layout)
- [Development](#development)
- [Testing](#testing)
- [Quality Gates](#quality-gates)
- [Documentation Map](#documentation-map)
- [Versioning & Releases](#versioning--releases)
- [Security](#security)
- [Support](#support)
- [Contributing](#contributing)
- [License](#license)

---

## Why EAIP

Most agent frameworks optimise for *demos*. EAIP optimises for *production*:

| Concern               | EAIP Approach                                                                 |
| --------------------- | ----------------------------------------------------------------------------- |
| Reliability           | Deterministic orchestration core, retries, circuit breakers, idempotency keys |
| Observability         | OpenTelemetry traces, structured logs, prompt/tool replay                     |
| Cost control          | Token & tool-call budgets per request, tenant, and agent                      |
| Safety & policy       | Pluggable policy engine, content filters, allow/deny lists, audit logs        |
| Multi-tenant ops      | Per-tenant isolation for memory, secrets, quotas, and telemetry               |
| Extensibility         | Stable plugin contracts for LLMs, tools, memory backends, and policies        |

## Architecture at a Glance

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full system view. In short:

```text
┌────────────────────────────────────────────────────────────────────┐
│                          Control Plane                             │
│   Identity · Tenants · Policies · Quotas · Audit · Admin UI/API    │
└────────────────────────────────────────────────────────────────────┘
                                  │
┌────────────────────────────────────────────────────────────────────┐
│                          Agent Runtime                             │
│   Orchestrator · Planner · Tool Router · Memory · Guardrails       │
└────────────────────────────────────────────────────────────────────┘
                                  │
┌──────────────┬───────────────┬───────────────┬────────────────────┐
│  LLM Adapters│  Tool Adapters│  Memory Stores│  Telemetry / OTel  │
└──────────────┴───────────────┴───────────────┴────────────────────┘
```

## Quickstart

> Requires **Python 3.11+**, **make**, and **git**. (Runtime services arrive in EP-0002.)

```bash
# 1. Clone
git clone https://github.com/subham1902/eaip-platform.git
cd eaip-platform

# 2. One-command developer setup (Linux/macOS/WSL)
bash scripts/bootstrap.sh          # creates .venv, installs deps, installs hooks
#    Windows:
pwsh -File scripts/bootstrap.ps1

# 3. Run the standard quality gates locally
make check                          # ruff + black --check + mypy + pytest
#    or, with friendlier output:
bash scripts/validate.sh

# 4. Verify the repository is healthy end-to-end
make health                         # → scripts/healthcheck.sh
make validate-docs                  # → scripts/validate-docs.sh

# Or work inside a containerised dev environment:
make docker-dev                     # docker compose -f docker-compose.dev.yml run --rm eaip
```

If you use **VS Code**, opening the folder prompts you to reopen in the
shipped **devcontainer** (`.devcontainer/devcontainer.json`) — everything is
pre-installed and tasks are wired under `Tasks: Run Task → EAIP: *`.

If you only want to verify the scaffolding:

```bash
make lint          # ruff + black --check
make typecheck     # mypy
make test          # pytest (no tests yet → exits 0 with `--passed-with-no-tests` semantics)
```

## Repository Layout

```text
.
├── .github/                # Issue/PR templates, CODEOWNERS, CI workflows
├── .vscode/                # Recommended editor settings & extensions
├── docs/                   # (EP-0002+) Long-form documentation
├── src/                    # (EP-0002+) Source packages (eaip_*)
├── tests/                  # Test suite (mirrors src/ layout)
├── ARCHITECTURE.md         # System architecture & component contracts
├── CHANGELOG.md            # Keep-a-Changelog formatted history
├── CODE_OF_CONDUCT.md      # Contributor Covenant v2.1
├── CONTRIBUTING.md         # Contribution workflow & standards
├── DECISION_REGISTER.md    # Lightweight ADR index
├── ENGINEERING_TRACKER.md  # Engineering Package (EP) ledger
├── LICENSE                 # Apache License 2.0
├── Makefile                # Standard developer tasks
├── README.md               # You are here
├── RISK_REGISTER.md        # Active risks & mitigations
├── ROADMAP.md              # Public roadmap (rolling 4 quarters)
├── SECURITY.md             # Vulnerability disclosure policy
├── SUPPORT.md              # How to get help
├── TECH_DEBT.md            # Tracked technical debt
├── VERSIONING.md           # SemVer + release policy
├── pyproject.toml          # Build system, deps, tool config
└── .pre-commit-config.yaml # Hooks: ruff, black, mypy, secrets, formatting
```

## Development

```bash
make bootstrap     # create venv, install dev deps, install pre-commit
make fmt           # auto-format (black + ruff --fix)
make lint          # ruff + black --check
make typecheck     # mypy --strict
make test          # pytest with coverage
make check         # all gates (fmt-check + lint + typecheck + test)
make clean         # remove caches & build artifacts
```

Editor configuration is shipped under `.vscode/` and is automatically picked up by VS Code. `.editorconfig` provides cross-editor defaults.

## Testing

- **Unit tests** live under `tests/unit/` and must run in < 100ms each.
- **Integration tests** live under `tests/integration/` and may use Docker compose fixtures.
- **End-to-end tests** live under `tests/e2e/`.
- Coverage threshold (enforced in CI starting EP-0002): **85% lines, 80% branches**.

## Quality Gates

Every PR must pass:

| Gate          | Tool                                  | Enforced In |
| ------------- | ------------------------------------- | ----------- |
| Format        | `black`, `ruff format`                | pre-commit + CI |
| Lint          | `ruff` (pyflakes, pycodestyle, isort, bugbear, security, pyupgrade) | pre-commit + CI |
| Types         | `mypy --strict`                       | CI |
| Tests         | `pytest` + `pytest-cov`               | CI |
| Security      | `bandit`, `pip-audit`, `gitleaks`     | CI |
| Conventional Commits | commit message validation      | pre-commit |
| Signed-off-by | DCO                                   | CI |

## Documentation Map

| Audience             | Start Here                                 |
| -------------------- | ------------------------------------------ |
| New contributor      | [`CONTRIBUTING.md`](CONTRIBUTING.md)       |
| Operator / SRE       | [`ARCHITECTURE.md`](ARCHITECTURE.md)       |
| Security researcher  | [`SECURITY.md`](SECURITY.md)               |
| Product / planning   | [`ROADMAP.md`](ROADMAP.md), [`ENGINEERING_TRACKER.md`](ENGINEERING_TRACKER.md) |
| Architecture history | [`DECISION_REGISTER.md`](DECISION_REGISTER.md) |
| Risk & debt          | [`RISK_REGISTER.md`](RISK_REGISTER.md), [`TECH_DEBT.md`](TECH_DEBT.md) |

## Versioning & Releases

EAIP follows [Semantic Versioning 2.0.0](https://semver.org/). Detailed policy lives in [`VERSIONING.md`](VERSIONING.md). Release notes are auto-generated from Conventional Commits and curated in [`CHANGELOG.md`](CHANGELOG.md).

## Security

Please **do not** open public issues for security vulnerabilities. See [`SECURITY.md`](SECURITY.md) for the coordinated disclosure process and PGP key.

## Support

See [`SUPPORT.md`](SUPPORT.md) for community channels, SLA expectations, and the issue triage process.

## Contributing

Contributions are welcome and appreciated. Please read:

1. [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) — expected behaviour.
2. [`CONTRIBUTING.md`](CONTRIBUTING.md) — branching, commits, PRs, review.
3. [`VERSIONING.md`](VERSIONING.md) — what counts as a breaking change.

All contributions must include a `Signed-off-by` trailer (DCO).

## License

Copyright © 2026 Subham Panigrahi.

Licensed under the **Apache License, Version 2.0**. See [`LICENSE`](LICENSE) for the full text.
