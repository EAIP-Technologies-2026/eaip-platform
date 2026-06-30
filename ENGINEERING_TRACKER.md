# Engineering Tracker

> **Purpose:** A single, append-only ledger of **Engineering Packages (EPs)** — the units in which EAIP plans, executes, and audits work.
> **Owner:** Subham Panigrahi ([@subham1902](https://github.com/subham1902))
> **Last updated:** 2026-01-15

---

## What is an Engineering Package?

An **EP** is a contained body of engineering work with:

- A unique ID: `EP-NNNN[X]` where `NNNN` is a zero-padded sequence and `X` is an optional iteration letter (`A`, `B`, …) for re-scoped continuations.
- An **owner** (one person), **reviewers**, and an **exit definition**.
- A **scope** (in / out), **deliverables**, **acceptance criteria**, and **risks**.
- Tracked **status**: ⚪ Planned → 🟡 Active → 🔵 In Review → ✅ Done · ⏸ Paused · ❌ Dropped.

Every EP corresponds to a labelled GitHub Project view (`EP/EP-NNNNX`) and a milestone.

## EP Index

| EP ID       | Title                                        | Status     | Owner        | Target     | Notes |
| ----------- | -------------------------------------------- | ---------- | ------------ | ---------- | ----- |
| **EP-0001A** | Repository Foundation                       | ✅ Done    | @subham1902  | 2026-01-15 | Governance & scaffolding. |
| EP-0001B    | CI/CD Baseline                               | 🟡 Active  | @subham1902  | 2026-02-15 | Test matrix, caching, release automation. |
| **EP-0002** | **Platform Foundation**                      | ✅ Done    | @subham1902  | 2026-01-15 | DI, lifecycle, registries, plugins, logging, events, health. |
| EP-0003     | LLM Adapter Contract + 2 Reference Adapters  | ⚪ Planned | TBD          | 2026-04-30 | OpenAI + Anthropic adapters. |
| EP-0004     | Telemetry Baseline                           | ⚪ Planned | TBD          | 2026-05-31 | OTel traces + Prometheus metrics. |
| EP-0005     | Tool Adapter Contract + Reference Tools      | ⚪ Planned | TBD          | 2026-06-30 | HTTP, SQL, file. |
| EP-0006     | Memory Subsystem                             | ⚪ Planned | TBD          | 2026-07-31 | STM (Redis) + LTM (pgvector). |
| EP-0007     | Policy Engine v1                             | ⚪ Planned | TBD          | 2026-08-31 | Allow/deny lists + content filters. |
| EP-0008     | CLI (`eaip`)                                 | ⚪ Planned | TBD          | 2026-09-15 | agents, tools, runs, traces. |
| EP-0009     | Cost & Token Budgets                         | ⚪ Planned | TBD          | 2026-09-30 | Per-tenant & per-run budgets. |

> Add new EPs by appending below — never reorder.

---

## EP-0001A — Repository Foundation

- **Status:** ✅ Done
- **Owner:** @subham1902
- **Reviewers:** community
- **Started / Completed:** 2026-01-15 / 2026-01-15

### Scope (In)

- Governance documents (CoC, contributing, security, support).
- Process documents (versioning, changelog, roadmap, architecture).
- Project ledgers (decision register, tech debt, risk register, this tracker).
- Repository hygiene (`.editorconfig`, `.gitattributes`, `.gitignore`).
- Python tooling (`pyproject.toml`, `Makefile`, `.pre-commit-config.yaml`).
- Editor configuration (`.vscode/`).
- GitHub automation (issue/PR templates, CODEOWNERS, starter CI workflows).

### Scope (Out)

- Any runtime source code (lands in EP-0002).
- Detailed CI/CD pipelines beyond a starter (EP-0001B).
- Public documentation site (later EP).

### Deliverables

- All files listed in [`CHANGELOG.md` → 0.0.1](CHANGELOG.md#001--2026-01-15).

### Acceptance Criteria

- `make check` passes locally on a fresh clone after `make bootstrap`.
- `pre-commit run --all-files` passes.
- All required GitHub status checks defined in `.github/workflows/ci.yml` pass on PRs.
- README rendering is correct on GitHub.
- A new contributor can go from `git clone` to a green local run in **≤ 5 minutes**.

### Decisions

- [DR-0001](DECISION_REGISTER.md#dr-0001) — License: Apache-2.0.
- [DR-0002](DECISION_REGISTER.md#dr-0002) — Tooling stack: ruff + black + mypy + pytest.
- [DR-0004](DECISION_REGISTER.md#dr-0004) — Conventional Commits + DCO.

### Risks Addressed

- [R-0001](RISK_REGISTER.md#r-0001) — Onboarding friction.
- [R-0002](RISK_REGISTER.md#r-0002) — Supply-chain hygiene.

### Exit Notes

Foundation is complete and unblocking. Subsequent EPs may freely add directories under `src/`, `tests/`, `docs/`, and `infra/` without re-scoping this EP.

---

## EP-0001B — CI/CD Baseline

- **Status:** 🟡 Active
- **Owner:** @subham1902
- **Target:** 2026-02-15

### Scope (In)

- Matrix tests: Python 3.11/3.12/3.13 × Ubuntu/macOS.
- Pip & pre-commit caching.
- Release-please (or equivalent) for changelog & version bumps.
- Signed releases (sigstore/cosign) for PyPI artifacts.
- Dependabot + grouped weekly updates.

### Acceptance Criteria

- A green PR runs **< 5 minutes** end to end.
- A merged release tag automatically publishes PyPI + GitHub release with notes.
- All workflow tokens scoped to `permissions: read-all` by default; writes are job-local.

---

## EP-0002 — Platform Foundation

- **Status:** ✅ Done
- **Owner:** @subham1902
- **Reviewers:** community
- **Started / Completed:** 2026-01-15 / 2026-01-15

### Scope (In)

Production-quality reusable infrastructure under `src/eaip/`, **no business
logic**. Every future capability pack depends on this package.

- `shared/` — zero-dependency primitives: identifiers, `Result`, sentinels, time, JSON types.
- `exceptions/` — single hierarchy under `EAIPError` with stable `ErrorCode`s.
- `types/` — constrained Pydantic value types (`NonEmptyStr`, `Port`, `HostName`, `Url`, `LogLevel`, `EnvName`, `Environment`).
- `protocols/` — structural protocols (`Startable`, `Healthcheckable`, `Identifiable`, ...).
- `interfaces/` — abstract bases (`AbstractService` FSM, `AbstractRepository`).
- `metadata/` — `ComponentMetadata` and `ComponentKind`.
- `version/` — `Version` value object + `PLATFORM_VERSION`.
- `utilities/` — `gather_with_concurrency`, `chunked`, `unique`, string helpers.
- `serialization/` — strict JSON encoder/decoder.
- `validation/` — typed `ValidationError` wrappers around Pydantic v2.
- `config/` — `DictSource`, `EnvSource`, `FileSource` (JSON/TOML), `LayeredSource`.
- `settings/` — `PlatformSettings`, `CoreSettings`, `LoggingSettings`, `FeatureFlagSettings`.
- `logging/` — `structlog`-backed structured logging with context propagation & redaction.
- `events/` — in-process pub/sub bus with sync/async handlers & subclass routing.
- `factories/` — generic typed factory.
- `dependency_injection/` — `Container`, `Scope`, cycle detection.
- `registry/` — generic typed observable registry.
- `lifecycle/` — `LifecycleManager` with rollback on failure.
- `capabilities/` — `Capability`, `CapabilityRegistry`.
- `plugins/` — `PluginManifest`, `Plugin` (Protocol), `PluginRegistry`, `PluginLoader`.
- `ports/` — `ClockPort`, `IdGeneratorPort`, `SecretProviderPort`.
- `adapters/interfaces/` — `AbstractAdapter`, `AdapterCapability`.
- `infrastructure/` — `SystemClock`, `UuidIdGenerator`, `EnvSecretProvider`.
- `core/` — `FeatureFlag(Registry)`, `ShutdownSignal`, signal handlers.
- `platform/` — `Platform` composition root, `PlatformBuilder`.
- `application/` — `build_platform()`, `run_platform()`.

### Scope (Out)

- Runtime orchestration, planner, reasoner, knowledge engine (later EPs).
- LLM, vector store, tool adapters (capability packs).
- Dashboards, marketplace, deployment packs, industry packs (future EPs).

### Deliverables

- 60+ source modules under `src/eaip/`.
- 14 unit-test modules with **152 passing tests** in 0.31s.
- Per-package `README.md` documentation files.

### Acceptance Criteria

- ✅ Every Foundation package imports cleanly under Python ≥ 3.11.
- ✅ `build_platform()` returns a usable `Platform`; `async with platform:`
      transitions through `created → running → stopped`.
- ✅ Health rollup, plugin contract validation, DI cycle detection, lifecycle
      rollback all exercised by tests.
- ✅ Total test coverage **84%+** with the public Protocol modules being the
      only systematically under-covered surface (they are pure stubs).

### Decisions

- [DR-0008](DECISION_REGISTER.md#dr-0008) — async-first runtime.
- [DR-0010](DECISION_REGISTER.md#dr-0010) — OpenTelemetry as the only telemetry contract (consumed in EP-0004).

### Exit Notes

The Platform Foundation is now the load-bearing layer for every future
engineering pack. Capability packs depend on `eaip.platform.Platform`, the
DI container, registries, and ports — they MUST NOT reach across into each
other directly. Foundation modules are stable; breaking changes require a
follow-on `EP-0002B` re-scope rather than in-place edits.

---

## Lifecycle & Conventions

- **Creation:** open a discussion proposing the EP; once accepted, append to the [EP Index](#ep-index) and create a section.
- **Updates:** edit the EP's section in place; do **not** rewrite history.
- **Closure:** flip status to ✅, ⏸, or ❌; write a short *Exit Notes* paragraph; link to the merged PRs.
- **Re-scoping:** open `EP-NNNNB` (next letter) rather than mutating the original.

All status transitions must reference at least one PR or commit.
