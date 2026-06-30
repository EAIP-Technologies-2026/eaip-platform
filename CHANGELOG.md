# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

Section legend: **Added** · **Changed** · **Deprecated** · **Removed** · **Fixed** · **Security**.

> Until `1.0.0`, breaking changes may occur in any minor release. See [`VERSIONING.md`](VERSIONING.md) for the full policy.

---

## [Unreleased]

### Added
- _Nothing yet._

### Changed
- _Nothing yet._

### Deprecated
- _Nothing yet._

### Removed
- _Nothing yet._

### Fixed
- _Nothing yet._

### Security
- _Nothing yet._

---

## [0.0.2] — 2026-01-15

**Engineering Package:** [EP-0002 — Platform Foundation](ENGINEERING_TRACKER.md#ep-0002--platform-foundation)

### Added

- **Source tree** under `src/eaip/` — 27 production-quality packages providing the reusable Platform Foundation. No business capabilities; pure infrastructure.
- **Composition root** — `eaip.platform.Platform` and `PlatformBuilder` wire every subsystem together; `eaip.application.build_platform()` is the one-liner entry point.
- **Lifecycle** — `LifecycleManager` orchestrates ordered startup and reverse-ordered shutdown with rollback on failure.
- **Dependency Injection** — `Container` with `Singleton`, `Transient`, and `Scoped` providers, cycle detection, type-safe bindings, and child scopes.
- **Registries** — generic observable `Registry[T]` plus domain wrappers (`CapabilityRegistry`, `PluginRegistry`, feature flags).
- **Plugin contract** — `PluginManifest`, `Plugin` Protocol, `PluginLoader` with contract-version validation.
- **Structured logging** — `structlog`-backed JSON & console formats, contextvar propagation, redaction of sensitive keys.
- **Events** — in-process `EventBus` with sync/async handlers, subclass routing, and isolated failure semantics.
- **Health** — tri-state `HealthStatus`, async `HealthCheck` protocol, aggregating `HealthReporter`.
- **Config & settings** — layered config sources (`DictSource`, `EnvSource`, `FileSource`, `LayeredSource`) and a typed `PlatformSettings` hierarchy.
- **Ports & default adapters** — `ClockPort`, `IdGeneratorPort`, `SecretProviderPort` with `SystemClock`, `UuidIdGenerator`, `EnvSecretProvider` defaults.
- **Shared primitives** — typed `str` identifiers (`CorrelationId`, `RunId`, `ComponentId`, `Slug`), `Result`/`Ok`/`Err`, `Duration`, `UNSET` sentinel, JSON type aliases.
- **Exceptions** — single hierarchy under `EAIPError` with stable `ErrorCode`s and structured `context`.
- **Tests** — 14 unit-test modules with **152 tests passing in <1s**; 84% coverage; pytest + pytest-asyncio fixtures.

### Changed

- `pyproject.toml` now declares runtime dependencies (`pydantic>=2.9`, `pydantic-settings>=2.6`, `structlog>=24.4`, `anyio>=4.6`) and registers `src/eaip` as the wheel package.

### Notes

- This release is **infrastructure-only** — no runtime orchestration, no LLM integrations, no business APIs.

---

## [0.0.1] — 2026-01-15

**Engineering Package:** [EP-0001A — Repository Foundation](ENGINEERING_TRACKER.md#ep-0001a)

### Added

- **Governance & Community**
  - `README.md` with project overview, quickstart, and documentation map.
  - `CONTRIBUTING.md` with workflow, commit conventions, DCO, and review process.
  - `CODE_OF_CONDUCT.md` — Contributor Covenant v2.1.
  - `SECURITY.md` — coordinated vulnerability disclosure policy.
  - `SUPPORT.md` — community support channels and expectations.
  - `LICENSE` — Apache License 2.0.
- **Engineering Documentation**
  - `ARCHITECTURE.md` — high-level system architecture and component contracts.
  - `ROADMAP.md` — rolling 4-quarter public roadmap.
  - `ENGINEERING_TRACKER.md` — Engineering Package (EP) ledger.
  - `DECISION_REGISTER.md` — lightweight ADR index seeded with foundational decisions.
  - `TECH_DEBT.md` — debt registry with owners and remediation plans.
  - `RISK_REGISTER.md` — active risks scored by likelihood × impact.
  - `VERSIONING.md` — SemVer policy & release cadence.
  - `CHANGELOG.md` — this file.
- **Repository Hygiene**
  - `.editorconfig`, `.gitattributes`, `.gitignore` covering Python, Node, IDEs, OS artifacts.
  - `pyproject.toml` with `ruff`, `black`, `mypy`, `pytest`, and `pip-audit` configuration.
  - `Makefile` with `bootstrap`, `fmt`, `lint`, `typecheck`, `test`, `check`, `clean` targets.
  - `.pre-commit-config.yaml` enforcing format, lint, type-check, secrets scan, and conventional commits.
- **Editor & Contributor Experience**
  - `.vscode/settings.json`, `extensions.json`, `launch.json`.
- **GitHub Automation**
  - Issue templates: bug report, feature request, documentation, with shared `config.yml`.
  - `pull_request_template.md` with checklist and DCO reminder.
  - `CODEOWNERS` mapping ownership of every top-level path.
  - `.github/workflows/ci.yml` — lint + typecheck + test matrix across Python 3.11/3.12/3.13.
  - `.github/workflows/security.yml` — `bandit`, `pip-audit`, `gitleaks` on every PR.

### Security

- Repository defaults to `permissions: read-all` in all GitHub Actions workflows.
- Secret scanning is enabled in pre-commit via `detect-secrets`.

---

[Unreleased]: https://github.com/subham1902/eaip-platform/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/subham1902/eaip-platform/releases/tag/v0.0.2
[0.0.1]: https://github.com/subham1902/eaip-platform/releases/tag/v0.0.1
