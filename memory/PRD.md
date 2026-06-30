# EAIP Platform — PRD

**Repository:** `subham1902/eaip-platform`
**Owner:** Subham Panigrahi (@subham1902)
**License:** Apache-2.0
**Status:** EP-0001A ✅ + EP-0002 ✅ — Platform Foundation complete
**Last updated:** 2026-01-15

## Original Problem Statement (latest CTO Order — EP-0002)

> Build the complete reusable **Platform Foundation** for EAIP. Infrastructure
> only — no runtime orchestration, planners, reasoners, knowledge engines,
> memory engines, workflow engines, dashboards, marketplaces, deployment
> packs, industry packs, LLM integrations, or business APIs.
> Must feel like an OS-style foundation (Kubernetes / Linux / VS Code).

## User Choices

- EAIP = Enterprise Autonomous Intelligence Platform
- Repo: `subham1902/eaip-platform`
- Maintainer: Subham Panigrahi (@subham1902)
- License: Apache 2.0
- Python: 3.11/3.12/3.13 (target 3.13)
- Tooling: ruff + black + mypy + pytest

## Architecture

EP-0001A and EP-0002 together establish the architectural foundation. EP-0002
delivers a **layered Platform Foundation** under `src/eaip/`:

```
application → platform → (lifecycle, registry, DI, capabilities, plugins, core)
            → (events, logging, health, config, settings, factories)
            → (serialization, validation, protocols, interfaces, metadata, version, utilities)
            → (ports ↔ infrastructure ↔ adapters/interfaces)
            → (shared, exceptions, types)   — bottom layer, zero deps
```

## What's Been Implemented

### EP-0001A — Repository Foundation (2026-01-15) ✅
35 governance/process/tooling files (README, CONTRIBUTING, CoC, SECURITY,
ROADMAP, ARCHITECTURE, etc.), `pyproject.toml`, `Makefile`, `.pre-commit`,
`.vscode/`, GitHub issue/PR templates, CODEOWNERS, CI + security workflows.

### EP-0002 — Platform Foundation (2026-01-15) ✅
**27 source packages** under `src/eaip/` totalling ~1,830 lines of strictly-
typed, production-quality Python. Highlights:

- **Composition root:** `Platform`, `PlatformBuilder`, `build_platform()`, `run_platform()`.
- **Lifecycle:** ordered start, LIFO stop, automatic rollback on failure.
- **Dependency Injection:** typed `Container` with `Singleton`/`Transient`/`Scoped` scopes, cycle detection.
- **Registries:** generic observable `Registry[T]` + `CapabilityRegistry`, `PluginRegistry`, `FeatureFlagRegistry`.
- **Plugins:** Protocol-based contract, manifest validation, idempotent activate/deactivate.
- **Logging:** `structlog` JSON+console, contextvar propagation, secret redaction.
- **Events:** in-process bus with subclass routing, sync/async handlers, isolated failure.
- **Health:** worst-status rollup with failure isolation.
- **Config/Settings:** layered sources + typed Pydantic settings hierarchy.
- **Ports & infrastructure:** clock, ID generator, secret provider with default adapters.
- **Shared:** typed `str` identifiers, `Result` monad, `Duration`, `UNSET`, JSON aliases.
- **Exceptions:** single hierarchy with stable `ErrorCode`s and structured context.

**Tests:** 14 unit-test modules, **152 tests passing in 0.31s**, 84% coverage.

## Backlog

- **P0 (EP-0001B):** release-please + sigstore, signed PyPI releases.
- **P0 (EP-0003):** LLM adapter contract + OpenAI/Anthropic reference adapters.
- **P0 (EP-0004):** OpenTelemetry baseline (traces + metrics).
- **P1 (EP-0005):** Tool adapter contract + HTTP/SQL/file reference tools.
- **P1 (EP-0006):** Memory subsystem (STM Redis + LTM pgvector).
- **P1 (EP-0007):** Policy Engine v1 (OPA/Rego facade, per [DR-0003](DECISION_REGISTER.md#dr-0003)).
- **P2 (EP-0008–EP-0009):** CLI, cost/token budgets.

## Next Tasks

1. Begin EP-0001B (release automation + signing).
2. Begin EP-0003 (LLM adapter contract atop `AbstractAdapter`).
3. Recruit additional maintainers (TD-0007 / R-0003).
