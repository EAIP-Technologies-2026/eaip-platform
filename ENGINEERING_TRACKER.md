# Engineering Tracker

> **Purpose:** A single, append-only ledger of **Engineering Packages (EPs)** — the units in which EAIP plans, executes, and audits work.
> **Owner:** Subham Panigrahi ([@subham1902](https://github.com/subham1902))
> **Last updated:** 2026-07-09

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
| **EP-0002.2** | **Platform Kernel Engineering Pack (Bundle-008)** | ✅ Done | @subham1902  | 2026-07-07 | Runtime kernel, scheduler, hooks, context, metrics, Prometheus export. |
| **EP-0002.3** | **Services & Application Layer (Bundle-009)** | ✅ Done    | @subham1902  | 2026-07-07 | ServiceCollection, DI integration, app lifecycle, fluent builder. |
| **EP-0002.4** | **Runtime Integration & Bootstrap (Bundle-010)** | ✅ Done | @subham1902  | 2026-07-07 | Bootstrap pipeline, smoke tests, Docker validation. |
| **EP-0002.5** | **Event Bus & Messaging Core (Bundle-011)** | ✅ Done | @subham1902  | 2026-07-07 | Envelope, retry, hooks, dispatcher. |
| **EP-0003**     | **LLM Adapter Contract + 2 Reference Adapters**  | ✅ Done    | @subham1902  | 2026-07-10 | OpenAI + Anthropic adapters, tool orchestration loop. |
| EP-0004     | Telemetry Baseline                           | ⚪ Planned | TBD          | 2026-05-31 | OTel traces + Prometheus metrics. |
| EP-0005     | Tool Adapter Contract + Reference Tools      | ⚪ Planned | TBD          | 2026-06-30 | HTTP, SQL, file. |
| EP-0006     | Memory Subsystem                             | ⚪ Planned | TBD          | 2026-07-31 | STM (Redis) + LTM (pgvector). |
| EP-0007     | Policy Engine v1                             | ⚪ Planned | TBD          | 2026-08-31 | Allow/deny lists + content filters. |
| EP-0008     | CLI (`eaip`)                                 | ⚪ Planned | TBD          | 2026-09-15 | agents, tools, runs, traces. |
| EP-0009     | Cost & Token Budgets                         | ⚪ Planned | TBD          | 2026-09-30 | Per-tenant & per-run budgets. |
| **EP-0015** | **Knowledge Engine (Bundle-016)**            | ✅ Done    | @subham1902  | 2026-07-08 | Ingestion, chunking, embedding, Qdrant store, retrieval, registry, health, runtime integration. |
| **EP-0003.1** | **Tool Calling & Function Support (Bundle-020)** | ✅ Done    | @subham1902  | 2026-07-09 | Tool models, Tool protocol, ToolRegistry, OpenAICompatProvider tool calling, 3 reference tools. |
| **EP-0003.2** | **LLM Adapter Contract (Bundle-021)**           | ✅ Done    | @subham1902  | 2026-07-10 | LLMAdapter protocol, ToolCallOrchestrator, OpenAIAdapter, AnthropicAdapter. |
| **EP-0004.1** | **Agent Runtime (Bundle-022)**                 | ✅ Done    | @subham1902  | 2026-07-10 | AgentRuntime, planners, executor, guardrails, events, health, 80 tests. |

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

## EP-0002.2 — Platform Kernel Engineering Pack (Bundle-008)

- **Status:** ✅ Done
- **Owner:** @subham1902
- **Reviewers:** AI-assisted (opencode)
- **Started / Completed:** 2026-07-07 / 2026-07-07

### Scope (In)

Production-quality runtime kernel and metrics subsystem for the EAIP platform:

- `runtime/` — `RuntimeKernel` lifecycle (boot/shutdown), `RuntimeContext` (contextvars), `HookRegistry` (ordered lifecycle hooks), `Host` (async entry point), `Scheduler` (one-shot/recurring tasks), `RuntimeModule` (protocol).
- `metrics/` — thread-safe `Counter`, `Gauge`, `Histogram`, `Meter` (singleton factory), `prometheus_text()` OpenMetrics export.
- 36 new unit tests across 3 modules (kernel, scheduler, metrics).
- `runtime/README.md` documenting all modules.

### Scope (Out)

- LLM adapters, vector stores, tool adapters (tracked by EP-0003, EP-0005).
- OpenTelemetry traces (planned for EP-0004).
- CLI (`eaip` command, planned for EP-0008).

### Deliverables

- 10 new source modules under `src/eaip/runtime/` and `src/eaip/metrics/`.
- 3 new test modules with **36 passing tests**.
- **188 total tests passing**, coverage **85.22%**.

### Acceptance Criteria

- ✅ `ruff check` — zero errors on new code.
- ✅ `ruff format` — zero formatting drift.
- ✅ `mypy --strict` — zero type errors on new code.
- ✅ `pytest --cov` — 188/188 pass, coverage ≥ 85%.
- ✅ `RuntimeKernel` transitions `created → starting → running → stopping → stopped`.
- ✅ `Scheduler` executes one-shot and recurring tasks with cancellation support.
- ✅ `Meter` creates and caches Counter/Gauge/Histogram instances; `prometheus_text()` renders valid OpenMetrics output.

### Decisions

- [DR-TBD] — `RuntimeContext` is an immutable frozen dataclass backed by `contextvars`.
- [DR-TBD] — Metrics use thread-safe in-process primitives rather than OTel SDK (deferred to EP-0004).

### Exit Notes

The Platform Kernel is complete and fully gated. It extends the `eaip.platform.Platform` composition root with a runtime lifecycle layer. Future EPs (EP-0003, EP-0004, EP-0005, etc.) register themselves as `RuntimeModule`s on the kernel.

---

## EP-0002.3 — Services & Application Layer (Bundle-009)

- **Status:** ✅ Done
- **Owner:** @subham1902
- **Reviewers:** AI-assisted (opencode)
- **Started / Completed:** 2026-07-07 / 2026-07-07

### Scope (In)

Production-quality service abstraction and application composition layer:

- `services/` — `ServiceCollection` (fluent service registration), `ServiceDescriptor` (lifetime, factory, instance), `ServiceProvider` (DI bridge), `add_default_services()` extension, `ServiceLifetime` (Singleton/Scoped/Transient).
- `app/` — `ApplicationBuilder` (fluent build with services, settings, plugins, kernel toggle), `ApplicationLifecycle` (async context manager with start/stop/phase transitions), `ApplicationRunner` (signal-driven graceful shutdown), `run_application()` convenience function.
- 58 new tests across 6 test modules (service collection, service provider, app lifecycle, app builder, app runner, integration bootstrap).

### Scope (Out)

- Runtime integration beyond the ApplicationLifecycle wrapper (Bundle-010).
- Docker startup or containerisation changes (Bundle-010).
- Full E2E smoke tests (Bundle-010).

### Deliverables

- 9 new source modules under `src/eaip/services/` and `src/eaip/app/`.
- 6 test modules with **58 passing tests**.
- **248 total tests passing**, coverage **86.10%**.

### Acceptance Criteria

- ✅ `ruff check` — zero errors.
- ✅ `ruff format` — zero formatting drift.
- ✅ `mypy` — zero type errors on new code.
- ✅ `pytest --cov` — 248/248 pass, coverage ≥ 86%.
- ✅ `ServiceCollection` fluent registration (singleton, scoped, transient, instance, factory).
- ✅ `ServiceCollection.build_container()` produces a valid `Container`.
- ✅ `ApplicationBuilder.build()` returns a wired `ApplicationLifecycle` with platform + optional kernel.
- ✅ `ApplicationLifecycle` transitions `created → running → stopped → failed` correctly.
- ✅ `ApplicationRunner` manages graceful start/stop with signal support.
- ✅ Integration test: full bootstrap, event publish/subscribe, health check resolution, meter registration all pass.

### Decisions

- [DR-TBD] — `ServiceCollection` wraps `Container` under `ServiceProvider`; application code never touches the Container directly.
- [DR-TBD] — `ApplicationBuilder` is the single entry point for production code; `PlatformBuilder` remains for tests and low-level use.
- [DR-TBD] — `HealthReporter` is registered as an instance (not a factory) at build time to share the same `HealthReporter` between Platform and DI.

### Exit Notes

The Services & Application Layer completes the Platform Foundation engineering track. The composition root (`Platform`) now has a high-level application API (`ApplicationBuilder` → `ApplicationLifecycle` → `ApplicationRunner`) that replaces the previous need to manually wire Platform + RuntimeKernel. Bundle-010 will integrate the full bootstrap pipeline and validate the stack end-to-end including Docker startup.

---

## EP-0002.4 — Runtime Integration & Bootstrap (Bundle-010)

- **Status:** ✅ Done
- **Owner:** @subham1902
- **Reviewers:** AI-assisted (opencode)
- **Started / Completed:** 2026-07-07 / 2026-07-07

### Scope (In)

Complete runtime bootstrap pipeline and end-to-end validation of the assembled platform:

- Runtime bootstrap pipeline (`ApplicationBuilder` → `ApplicationLifecycle` → `Platform` → `RuntimeKernel`).
- Application entry point (`python -m eaip` with `--version` flag).
- Graceful startup/shutdown with signal handling via `ApplicationRunner`.
- 11 runtime smoke tests verifying every subsystem boots successfully (DI, events, health, metrics, logging, settings, kernel).
- 10 integration tests covering the assembled runtime (services + kernel, custom health checks, multi-subscriber events, start failure recovery, concurrent health checks, singleton sharing).
- Dockerfile updated to `CMD ["python", "-m", "eaip"]` for production readiness.
- Docker image validated: `docker build` succeeds; `docker run` boots to `app.running` phase with all subsystems initialized.
- All repository quality gates: ruff zero errors, mypy zero errors, pytest 266/266 pass, coverage 86.18%.

### Scope (Out)

- LLM adapters, vector stores, tool adapters (EP-0003, EP-0005).
- OpenTelemetry traces (EP-0004).
- CLI (`eaip` command, EP-0008).

### Acceptance Criteria

- ✅ `docker build` succeeds (validated locally).
- ✅ `python -m eaip --version` prints version and exits.
- ✅ `python -m eaip` boots to `app.running` phase with all subsystems (logs verified).
- ✅ `pytest --cov` — 266/266 pass, coverage ≥ 86%.
- ✅ `ruff check` — zero errors.
- ✅ `mypy` — zero type errors on all source packages.
- ✅ Runtime smoke test covers the full bootstrap: Platform → ApplicationLifecycle → RuntimeKernel → start → health check → stop.

### Decisions

- [DR-TBD] — `python -m eaip` is the canonical container entry point; `eaip.application.run_application()` accepts an optional pre-built `ApplicationBuilder`.
- [DR-TBD] — Smoke tests live in `tests/smoke/` and exercise the fully assembled runtime; integration tests in `tests/integration/` cover cross-subsystem scenarios.
- [DR-TBD] — `ServiceCollection.add_singleton(key, factory)` requires `factory` be a concrete type; use `add_factory()` with `ServiceLifetime.SINGLETON` for callable factories.

### Exit Notes

Bundle-010 completes the Platform Foundation engineering track. The runtime bootstrap pipeline is fully integrated, tested, and containerised. The EAIP platform can now be started as a module (`python -m eaip`), builds cleanly in Docker, and passes all quality gates. Future engineering packages (EP-0003, EP-0004, EP-0005) extend this foundation with LLM adapters, telemetry, and tool contracts — no further bootstrap or integration work is required.

---

## EP-0002.5 — Event Bus & Messaging Core (Bundle-011)

- **Status:** ✅ Done
- **Owner:** @subham1902
- **Reviewers:** AI-assisted (opencode)
- **Started / Completed:** 2026-07-07 / 2026-07-07

### Scope (In)

Enhanced in-process event bus with messaging infrastructure:

- `envelope.py` — `EventEnvelope` (frozen Pydantic model with event_id, correlation_id, causation_id, retry_count, payload, metadata, occurred_at).
- `errors.py` — `EventError`, `EventHandlerError`, `EventPublishError`, `EventRetryExhaustedError`.
- `retry.py` — `RetryStrategy` (async protocol), `ImmediateRetry`, `FixedDelayRetry`, `ExponentialBackoffRetry` (configurable base/max delay, jitter).
- `hooks.py` — Lifecycle hook protocols (`BeforePublishHook`, `AfterPublishHook`, `BeforeHandleHook`, `AfterHandleHook`, `OnErrorCallback`) and `EventHooks` container.
- `dispatcher.py` — `EventDispatcher` wrapping `EventBus` with pre/post-publish hooks, per-handler retry with configurable strategy, `Meter` metrics integration (published/failure counters, handler count histogram), structured logging with scoped context.
- 4 unit test modules (envelope, retry, hooks, dispatcher), 1 integration test module (end-to-end flow through app), 1 e2e test module (order workflow demonstration with chained causation, retry, compensation).

### Scope (Out)

- Cross-process messaging (RabbitMQ, Kafka, Azure Service Bus — future capability pack).
- Event sourcing or outbox pattern (future EP).
- Dead-letter queue persistence (future EP).

### Deliverables

- 6 new source modules under `src/eaip/events/`.
- 6 test modules with **37 new tests** (20 unit + 10 integration + 7 e2e).
- **303 total tests passing**, coverage **86.72%**.

### Acceptance Criteria

- ✅ `ruff check` — zero errors.
- ✅ `mypy` — zero type errors on all event source packages.
- ✅ `pytest --cov` — 303/303 pass, coverage ≥ 86%.
- ✅ `EventEnvelope.from_event()` wraps a `DomainEvent` with event_id, correlation_id, causation_id, timestamp.
- ✅ All three retry strategies (Immediate, FixedDelay, ExponentialBackoff) correctly limit attempts and return appropriate delays.
- ✅ `EventDispatcher.publish()` delivers to multiple subscribers, supports sync/async handlers, invokes lifecycle hooks, retries on failure.
- ✅ Integration tests verify the full publish→dispatch→consume flow through a builder-constructed app.
- ✅ E2E tests demonstrate chained causation, retry with compensation, and metrics visibility.

### Decisions

- [DR-TBD] — `EventDispatcher` is the recommended entry point for publishing; `EventBus.publish()` remains for low-level use.
- [DR-TBD] — Hooks are async-by-default; the dispatcher awaits all hook invocations before proceeding.
- [DR-TBD] — Retry strategies receive the envelope and exception but are free to ignore them (Immediate, FixedDelay do); ExponentialBackoff uses exception metadata for diagnostics only.

### Exit Notes

Bundle-011 completes the Event Bus & Messaging Core. The in-process event infrastructure now supports typed envelopes, configurable retry with backoff, lifecycle hooks, and metrics integration. The dispatcher provides a production-grade layer over the base `EventBus` and is the recommended publish path. Future messaging capabilities (cross-process, event sourcing, DLQ) build on this contract.

---

## EP-0002.6 — Registry & Plugin Runtime (Bundle-012)

**Status:** ✅ Complete  
**Owner:** @subham1902  
**Theme:** Runtime Systems  
**Dependencies:** EP-0002.4 (Runtime Kernel), EP-0002.5 (Event Bus)  
**PR/Branch:** sprint-2

### Objective

Enable the platform to discover, validate, install, and activate third-party plugins within the runtime kernel, tracked by a service registry.

### Deliverables

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | `ServiceRegistry` — track running service instances with status, metadata, and observable changes | ✅ |
| 2 | Enhanced `PluginManifest` — `PluginDependency`, `entry_point`, `requires_platform`, `tags`, `dependencies` | ✅ |
| 3 | `PluginDiscovery` — entry-point group scanning, module scanning, recursive package scanning | ✅ |
| 4 | `PluginDependencyValidator` — semver range resolution, topological sort (Kahn's algorithm), cycle detection | ✅ |
| 5 | `PluginLifecycleManager` — orchestrates discover→install→validate→activate→deactivate | ✅ |
| 6 | `PluginRuntimeModule` — kernel lifecycle hooks for plugin boot/shutdown | ✅ |
| 7 | `PluginHealthCheck` — plugin subsystem health reporting (healthy/degraded) | ✅ |
| 8 | Plugin domain events (`PluginInstalled`, `PluginActivated`, `PluginDeactivated`) | ✅ |
| 9 | Loader helpers — `all()`, `count()`, `activated_count` | ✅ |
| 10 | Exports through `plugins/__init__.py`, `registry/__init__.py`, `runtime/__init__.py` | ✅ |

### Scope / Boundaries

- **In scope:** Plugin discovery via entry points, semver dependency validation, topological activation ordering, kernel runtime integration, health monitoring, service instance tracking.
- **Out of scope:** Cross-process plugin loading, hot-reload of plugins (planned for future EP), remote service discovery (K8s, Consul), plugin sandboxing/security.

### Verification

- ✅ `ruff check src/eaip` — zero errors
- ✅ `mypy src/eaip` — zero errors (116 files)
- ✅ `pytest` — 372 tests passing (72 new for this bundle)
- ✅ `pytest --cov=...` — 89.52% coverage on registry/plugins/runtime modules

### Decisions

- [DR-012.1] — Semver range parsing lives in `_satisfies` (private); the validator delegates to helper functions rather than pulling in a third-party semver library to avoid dependency bloat.
- [DR-012.2] — `PluginLifecycleManager` uses Kahn's algorithm for deterministic activation order; optional dependencies do not create edges in the DAG.
- [DR-012.3] — `PluginHealthCheck` class implements the `HealthCheck` protocol directly rather than using `callable_check` for richer state access.

### Exit Notes

Bundle-012 completes the Registry & Plugin Runtime. The platform can now discover plugins via entry points, validate their inter-plugin semver dependencies, and activate them in topological order through the kernel boot sequence. The ServiceRegistry provides runtime introspection of running services. Plugin health monitoring integrates with the existing HealthReporter. Future work includes hot-reload (EP-0002.7) and remote discovery.

---

## EP-0015 — Knowledge Engine (Bundle-016)

- **Status:** ✅ Done
- **Owner:** @subham1902
- **Reviewers:** community
- **Started / Completed:** 2026-07-08 / 2026-07-08

### Scope (In)

- Knowledge subsystem under `src/eaip/knowledge/`:
  - `KnowledgeEngine` — orchestrator for ingestion, query, and collection management with flexible constructor patterns.
  - `KnowledgeIngestionService` — document parsing, chunking, embedding, and vector-store persistence pipeline.
  - `KnowledgeRetriever` — single- and multi-collection search with context assembly.
  - `KnowledgeRegistry` — in-memory tracking of collections, documents, and chunks.
  - `FixedSizeChunker` and `SemanticChunker` — text splitting strategies.
  - `MockEmbeddingProvider` — test double for embedding integration.
  - `QdrantStore` — Qdrant vector database adapter.
  - `KnowledgeHealthCheck` — runtime health integration returning `HealthReport`.
  - `KnowledgeIntegration` / `KnowledgeRuntimeModule` — kernel lifecycle wiring.
  - All domain models, exception types, and event definitions.
  - 14 unit test modules, 1 integration test module, 1 e2e demo.
  - mypy strict, ruff, pytest quality gates.

### Scope (Out)

- Alternative vector store backends (pgvector, Azure AI Search) — deferred to a later bundle.
- Embedding provider implementations beyond mock (OpenAI, Azure OpenAI adapters).
- Production-grade Qdrant cluster configuration (TLS, auth, sharding).
- Caching layer for repeated queries.
- Cross-process or distributed knowledge sharing.

### Verification

- ✅ `ruff check src/eaip/knowledge/` — 0 errors on new code (1 pre-existing in `qdrant_store.py`)
- ✅ `mypy --strict src/eaip/knowledge/` — 0 errors
- ✅ `pytest tests/unit/test_knowledge_*.py` — 111/111 passed
- ✅ `pytest` — 621/632 passed (11 pre-existing provider failures unrelated to knowledge)
- ✅ `pytest --cov=src/eaip/knowledge/` — 77.47% (QdrantStore at 24.36% without live Qdrant)

### Decisions

- [DR-015.1] — `KnowledgeEngine.__init__` supports 4 call patterns to accommodate both registry-backed and standalone usage without breaking existing tests.
- [DR-015.2] — `KnowledgeRegistry` is an in-memory store for collections/documents/chunks rather than a registry-as-a-service; delegates persistence to `VectorStore`.
- [DR-015.3] — `KnowledgeHealthCheck` returns a Pydantic `HealthReport` instead of a raw dict for type safety and schema evolution.
- [DR-015.4] — `KnowledgeRuntimeModule` follows the `RuntimeModule` protocol (no-arg constructor, `start(kernel)`/`stop(kernel)`) for drop-in kernel integration.

### Exit Notes

Bundle-016 delivers the Knowledge Engine — a complete ingestion-to-retrieval pipeline. The `KnowledgeEngine` orchestrates document parsing, chunking, embedding, vector storage, and semantic search with runtime kernel integration. QdrantStore achieves only 24% coverage without a live Qdrant instance; the gap is acceptable for CI and will be addressed when a test Qdrant container is added. Coverage excluding QdrantStore is ~86%. Future bundles can layer on additional vector backends, production embedding providers, and cross-process knowledge sharing.

## EP-0002.8 — Enterprise Memory Engine (Bundle-017)

- **Status:** ✅ Done
- **Owner:** @subham1902
- **Reviewers:** AI-assisted (opencode)
- **Started / Completed:** 2026-07-09 / 2026-07-09

### Scope (In)

- Memory subsystem under `src/eaip/memory/`:
  - `MemoryEngine` — high-level API orchestrating memory creation, retrieval, search, update, deletion, lifecycle, consolidation, and summarisation.
  - `MemoryItem`, `MemoryScope`, `ScopedMemoryId`, `MemoryQuery`, `MemoryResult`, `MemorySearchResult` — domain models.
  - `MemoryConfig`, `RetentionConfig`, `ConsolidationConfig`, `IndexingConfig` — typed configuration.
  - `InMemoryStore` — dict-backed MemoryStore implementation with full CRUD, search, expiry, and scope management.
  - `MemoryStoreAdapter` — wraps separated store + indexer + retriever into a MemoryProvider.
  - `MemoryRegistry` — in-memory catalog with relationship tracking (register/unregister/get/has/list/count/relations).
  - `MemoryRetrievalService` — retrieval by ID, type, tags, relations, and free-form search.
  - `ContentIndexer`, `TagIndexer`, `MetadataIndexer`, `CompositeIndexer` — indexing strategies and implementations.
  - `TimeBasedConsolidationStrategy`, `NeverConsolidateStrategy`, `ConditionalConsolidationStrategy` — consolidation strategies.
  - `MemoryConsolidationService` — episodic-to-semantic promotion and deduplication.
  - `MaxAgeRetentionPolicy`, `MaxCountRetentionPolicy`, `PriorityRetentionPolicy`, `CompositeRetentionPolicy` — retention policies.
  - `MemoryExpirationService` — TTL-based expiry and archiving.
  - `MemoryLifecycleManager` — coordinated retention cycles.
  - `ExtractiveMemorySummarizer` — deterministic snippet extraction.
  - `MemoryHealthCheck` — runtime health integration returning HealthReport.
  - `MemoryIntegration` / `MemoryRuntimeModule` — kernel lifecycle wiring.
  - All domain event types (13 events: MemoryCreated, MemoryUpdated, MemoryDeleted, etc.).
  - All exception types (10 exceptions under MemoryError).
  - `eaip/memory/README.md` — package contracts documentation.
  - 13 unit test modules, 1 integration test module, 1 e2e demo.
  - mypy strict, ruff, pytest quality gates.
  - Missing exports in `__init__.py` corrected (`NeverIndexStrategy`, `ExtractiveMemorySummarizer`).

### Scope (Out)

- Alternative memory store backends (Redis, pgvector, Azure Cosmos DB) — deferred to later bundles.
- Embedding-based semantic search integration with the Knowledge Engine.
- Cross-process or distributed memory sharing.
- Persistent registry (beyond in-memory).
- Production-grade vector index for memory search.
- Hot-reload of memory configurations.

### Verification

- ✅ `ruff check src/eaip/memory/` — 0 errors on new code
- ✅ `mypy --strict src/eaip/memory/` — 0 errors
- ✅ `pytest tests/unit/test_memory_*.py` — all passed
- ✅ `pytest tests/integration/test_memory_lifecycle.py` — all passed
- ✅ `pytest tests/e2e/test_memory_demo.py` — all passed
- ✅ `pytest --cov=src/eaip/memory/` — ≥ 85%

### Decisions

- [DR-017.1] — `MemoryItem` is a frozen Pydantic model; updates use `model_copy(update=...)` to enforce immutability.
- [DR-017.2] — `MemoryScope` uses colon-delimited scope keys for hierarchical storage indexing; `ScopedMemoryId.fully_qualified()` provides globally unique identifiers.
- [DR-017.3] — `MemoryEngine` accepts optional `authorize_fn` and `event_publisher` callables for policy and event bus integration without tight coupling.
- [DR-017.4] — `MemoryStoreAdapter` wraps separate `MemoryStore`, `MemoryIndexer`, and `MemoryRetrievalService` into a unified `MemoryProvider` following the adapter pattern from `eaip.adapters`.
- [DR-017.5] — TTL-based expiry uses per-type configuration (`RetentionConfig`) with `archive_on_expire` toggle; `semantic_ttl_seconds` defaults to 0 (never expires).

### Exit Notes

Bundle-017 delivers the Enterprise Memory Engine — a complete multi-tier memory subsystem supporting working, session, long-term, episodic, and semantic memory types. The `MemoryEngine` orchestrates creation, retrieval, search, update, deletion, consolidation, summarisation, and lifecycle management. The in-memory store provides full functionality for single-process deployments and testing. The subsystem integrates with the runtime kernel via `MemoryRuntimeModule` and reports health through `MemoryHealthCheck`. All 13 domain event types and 10 exception types follow EAIP conventions. Future bundles can layer on persistent backends (Redis, pgvector), embedding-based semantic search, and cross-process memory sharing.

## EP-0003.1 — Tool Calling & Function Support (Bundle-020)

- **Status:** ✅ Done
- **Owner:** @subham1902
- **Reviewers:** AI-assisted (opencode)
- **Started / Completed:** 2026-07-09 / 2026-07-09

### Scope (In)

Tool calling and function execution support for the AI Provider Framework:

- **Tool models** — `ToolDefinition` (name, description, JSON Schema parameters), `ToolCall` (id, name, arguments), `ToolResult` (tool_call_id, content, is_error) in `eaip.providers.models`.
- **ChatRequest extension** — `tools: tuple[ToolDefinition, ...] | None` field for sending tool definitions to LLMs.
- **ChatResponse extension** — `tool_calls: tuple[ToolCall, ...] | None` field for receiving tool invocation requests from LLMs.
- **OpenAICompatProvider tool calling** — sends `tools` array in OpenAI format, parses `tool_calls` from response, handles malformed JSON arguments gracefully.
- **Tool protocol** — `eaip.tools.base.Tool` (`@runtime_checkable` Protocol) with `name`, `description`, `parameters` (JSON Schema), and `async execute(**kwargs) -> str`.
- **ToolRegistry** — register, get, try_get, unregister, all, clear, len, contains; `ToolNotFoundError` for missing tools.
- **Tool exceptions** — `ToolError`, `ToolNotFoundError`, `ToolExecutionError` inheriting from `EAIPError`.
- **Built-in reference tools** — `EchoTool` (echoes input), `CalculatorTool` (safe arithmetic via operator module, no eval), `CurrentTimeTool` (UTC time with optional format string).
- 4 new test modules with **77 passing tests** (22 model tests + 15 protocol/registry tests + 25 builtin tool tests + 15 provider tool-calling tests).

### Scope (Out)

- Full `LLMAdapter` protocol with `RunContext` and tool orchestration loop (planned for future bundle).
- Streaming tool call support — `chat_stream` does not yet emit tool calls from streamed chunks.
- Tool calling for `OllamaProvider` and `NVIDIAProvider` (they use different API formats).
- Function/tool choice control (`tool_choice`, `parallel_tool_calls`).
- Cross-process or distributed tool execution.
- Tool dependency injection or plugin-based tool discovery.

### Verification

- ✅ `ruff check src/eaip/tools/ src/eaip/providers/` — 0 errors
- ✅ `mypy src/eaip/tools/ src/eaip/providers/` — 0 errors
- ✅ `pytest tests/unit/test_tool_*.py tests/unit/test_provider_tool_calling.py` — 77/77 passed
- ✅ `pytest` — 1058/1058 passed (all existing tests + 77 new)

### Decisions

- [DR-020.1] — Tool parameters use `pydantic.json_schema.JsonSchemaValue` (JSON Schema dict) to remain provider-agnostic rather than Pydantic model fields.
- [DR-020.2] — `Tool` is a structural Protocol (not ABC) following the same pattern as `Provider` — enables duck-typed tool implementations without inheritance.
- [DR-020.3] — `CalculatorTool` uses the `operator` module with precedence climbing (no `eval`) for safe arithmetic evaluation.
- [DR-020.4] — Tool calling is added to `ChatRequest`/`ChatResponse` as optional tuple fields; backwards compatible — all existing tests pass without modification.

### Exit Notes

Bundle-020 delivers Tool Calling & Function Support — the critical bridge between LLM providers and tool execution. The OpenAICompatProvider now correctly sends tool definitions in chat requests and parses tool call responses from the LLM. The `Tool` protocol and `ToolRegistry` provide the registration and execution infrastructure for tools. Three built-in reference tools (Echo, Calculator, CurrentTime) serve as examples and test fixtures. The next logical step is an `LLMAdapter` layer that orchestrates the full tool-calling loop (call LLM → parse tool calls → execute tools → call LLM again with results).

## EP-0003.2 — LLM Adapter Contract (Bundle-021)

- **Status:** ✅ Done
- **Owner:** @subham1902
- **Reviewers:** AI-assisted (opencode)
- **Started / Completed:** 2026-07-10 / 2026-07-10

### Scope (In)

LLM Adapter Contract — the high-level orchestration layer wrapping providers with tool-calling loop support:

- **`LLMRequest`** — high-level request with `model`, `messages`, `temperature`, `max_tokens`, `stream`, `tools` (by name), and `metadata`.
- **`LLMResponse`** — high-level response with `content`, `finish_reason`, `tool_calls`, `usage`, `duration_ms`, `rounds` (tool-calling iterations), `adapter` name.
- **`RunContext`** — immutable runtime context with `tenant_id`, `run_id`, `correlation_id`, `labels`, `max_tool_rounds`.
- **`LLMAdapter` protocol** — `@runtime_checkable` Protocol with `name`, `version`, `async complete(request, *, context) -> LLMResponse`, `async health() -> HealthReport`.
- **`ToolCallOrchestrator`** — the call-LLM → parse tool calls → execute tools → feed results back → call-again loop, parameterised by Provider + ToolRegistry + max_rounds.
- **`OpenAIAdapter`** — reference implementation wrapping an OpenAI-compatible Provider with tool orchestration and health checking.
- **`AnthropicAdapter`** — reference implementation wrapping an Anthropic-compatible Provider with tool orchestration and health checking.
- **`LLMAdapterError`**, **`ToolExecutionError`**, **`MaxToolRoundsError`** — structured exception types.
- **`ErrorCode.INTERNAL_ERROR`** (`EAIP-0017`) added for adapter-level failures.
- 4 new test modules with **35 passing tests** (12 model tests + 9 orchestration tests + 7 OpenAI adapter tests + 7 Anthropic adapter tests).

### Scope (Out)

- Streaming support in the adapter `complete()` path (future bundle).
- Model-level retry, fallback, or circuit-breaker logic.
- Provider-specific content-filter or RAI integration.
- Tool choice control (`tool_choice`, `parallel_tool_calls`) at the adapter level.
- Tenant-aware rate limiting or cost tracking.
- Distributed or cluster-mode tool execution.

### Verification

- ✅ `ruff check src/eaip/adapters/llm/ tests/unit/test_llm_adapter_*.py` — 0 errors
- ✅ `mypy src/eaip/adapters/llm/ tests/unit/test_llm_adapter_*.py` — 0 errors
- ✅ `pytest tests/unit/test_llm_adapter_*.py` — 35/35 passed
- ✅ `pytest` — 1093/1093 passed (all existing tests + 35 new)

### Decisions

- [DR-021.1] — `LLMRequest.tools` is `tuple[str, ...]` (tool names) rather than inline `ToolDefinition` schemas; the adapter resolves names through the `ToolRegistry`, decoupling request construction from schema generation.
- [DR-021.2] — `RunContext` is a frozen Pydantic model (not a dataclass) for consistency with the codebase's model convention and to get JSON serialisation for free.
- [DR-021.3] — `ToolCallOrchestrator` is a concrete class (not a protocol) because the orchestration logic is a single fixed algorithm; the `LLMAdapter` protocol provides the plug point for alternative orchestrators.
- [DR-021.4] — `OpenAIAdapter` and `AnthropicAdapter` are concrete classes implementing the `LLMAdapter` protocol structurally (no explicit `__subclasshook__`), following the same duck-typing pattern as the `Provider` protocol.

### Exit Notes

Bundle-021 delivers the LLMAdapter Contract (EP-0003) — the high-level orchestration layer that completes the AI provider stack. The `LLMAdapter` protocol wraps any `Provider` with automatic tool-calling loop support, `RunContext` propagation, and health reporting. `OpenAIAdapter` and `AnthropicAdapter` provide ready-to-use reference implementations. The `ToolCallOrchestrator` handles the full call → parse → execute → repeat cycle with configurable max rounds and error handling. The next logical step is streaming support or the Tool Adapter Contract (EP-0005).

## EP-0004.1 — Agent Runtime (Bundle-022)

- **Status:** ✅ Done
- **Owner:** @subham1902
- **Reviewers:** AI-assisted (opencode)
- **Started / Completed:** 2026-07-10 / 2026-07-10

### Scope (In)

Agent Runtime — orchestrated agent execution with planning, tool use, guardrails, and memory:

- **`AgentSpec`, `Goal`, `Plan`, `Step`, `StepStatus`, `StepType`, `RunRecord`, `RunStatus`** — core domain models for agent execution.
- **`Planner` protocol + `FixedPlanner` + `SimpleLLMPlanner`** — plan decomposition from goals; `FixedPlanner` for deterministic tests, `SimpleLLMPlanner` for LLM-based step generation.
- **`Guardrail` protocol + `NoopGuardrail` + `CompositeGuardrail`** — pre/post step hooks with block/modify semantics.
- **`StepExecutor`** — dispatches `TOOL_CALL` and `LLM_COMPLETION` steps with timing.
- **`AgentRunContext`** — per-run context holding LLM adapter, tool registry, memory, event bus, meter.
- **`AgentRuntime`** — orchestrator managing run lifecycle: create → plan → execute steps → guardrails → publish events → metrics.
- **Domain events** — `RunStarted`, `RunCompleted`, `RunFailed`, `RunCancelled`, `StepStarted`, `StepCompleted`, `StepFailed`.
- **`AgentHealthCheck`** — health check reporting total/active runs.
- **`AgentRuntimeModule`** — runtime module for kernel registration with capability and health registration.
- **`AgentError`** hierarchy — `AgentNotFoundError`, `RunNotFoundError`, `PlanningError`, `StepExecutionError`.
- **OpenTelemetry tracing** — spans for runs and steps with status propagation.
- 8 new test modules with **80 passing tests** (7 unit + 1 integration).

### Scope (Out)

- Streaming agent execution (per-step streaming).
- Multi-agent orchestration (agent-to-agent handoff).
- Human-in-the-loop approval steps.
- Persistent run history beyond in-memory registry.
- Agent-specific prompt templates or system prompts.
- Parallel step execution (currently sequential).

### Verification

- ✅ `ruff check src/eaip/agents/ tests/unit/test_agent_*.py tests/integration/test_agent_runtime_integration.py` — 0 errors
- ✅ `mypy src/eaip/agents/` — 0 errors
- ✅ `pytest tests/unit/test_agent_*.py tests/integration/test_agent_runtime_integration.py` — 80/80 passed

### Decisions

- [DR-022.1] — `AgentRuntime` stores runs in-memory (not a database) for simplicity; a persistent backend can be swapped in later via the `_runs` dict.
- [DR-022.2] — Step failures do not cascade to run failure unless *all* steps fail; a single successful step keeps the run `COMPLETED`.
- [DR-022.3] — `StepExecutor` uses dict dispatch (`_handlers`) rather than if/elif chains to avoid MyPy unreachable-code warnings and ease extension.
- [DR-022.4] — `_fail_run` and `_finalize_run` are async methods (though they do async work only when publishing events) for consistency with the rest of the runtime.

### Exit Notes

Bundle-022 delivers the Agent Runtime (EP-0004.1) — the execution engine that ties together planning, tool calling, guardrails, events, and health into a single orchestrated loop. `AgentRuntime.create_run → start_run` provides a clean two-phase API, domain events enable observability, and the modular planner/executor/guardrail architecture supports easy extension. The next logical steps are multi-agent orchestration, persistent run storage, and human-in-the-loop support.

## Lifecycle & Conventions
- **Creation:** open a discussion proposing the EP; once accepted, append to the [EP Index](#ep-index) and create a section.
- **Updates:** edit the EP's section in place; do **not** rewrite history.
- **Closure:** flip status to ✅, ⏸, or ❌; write a short *Exit Notes* paragraph; link to the merged PRs.
- **Re-scoping:** open `EP-NNNNB` (next letter) rather than mutating the original.

All status transitions must reference at least one PR or commit.
