# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

Section legend: **Added** · **Changed** · **Deprecated** · **Removed** · **Fixed** · **Security**.

> Until `1.0.0`, breaking changes may occur in any minor release. See [`VERSIONING.md`](VERSIONING.md) for the full policy.

---

## [Unreleased]

### Added

- **Event Bus & Messaging Core** (`EP-0002.5 — Bundle-011`):
  - `src/eaip/events/envelope.py` — `EventEnvelope` (frozen Pydantic model with event_id, correlation_id, causation_id, retry_count, payload, metadata).
  - `src/eaip/events/errors.py` — `EventError`, `EventHandlerError`, `EventPublishError`, `EventRetryExhaustedError`.
  - `src/eaip/events/retry.py` — `ImmediateRetry`, `FixedDelayRetry`, `ExponentialBackoffRetry` (async protocol with jitter support).
  - `src/eaip/events/hooks.py` — `BeforePublishHook`, `AfterPublishHook`, `BeforeHandleHook`, `AfterHandleHook`, `OnErrorCallback`, `EventHooks` container.
  - `src/eaip/events/dispatcher.py` — `EventDispatcher` wrapping `EventBus` with hooks, retry (per-handler), metrics (`Meter`), structured logging.
  - 4 unit test modules (envelope, retry, hooks, dispatcher), 1 integration module (event flow), 1 e2e module (order workflow demo).
  - Full quality-gate pass: ruff zero errors, mypy zero errors, coverage 86.72% (303 tests).

- **Runtime Integration & Bootstrap** (`EP-0002.4 — Bundle-010`):
  - `src/eaip/__main__.py` — Application entry point (`python -m eaip` with `--version` support).
  - `src/eaip/app/runner.py` — `run_application()` now accepts optional pre-built `ApplicationBuilder`.
  - `Dockerfile` — `CMD` changed to `["python", "-m", "eaip"]` for production container startup.
  - 11 runtime smoke tests in `tests/smoke/test_runtime_bootstrap.py` (full bootstrap, DI, events, health, metrics, logging, settings, kernel, runner, idempotent stop).
  - 10 integration tests in `tests/integration/test_runtime_integration.py` (kernel + services, custom health checks, multi-subscriber events, start failure recovery, concurrent health checks, singleton sharing).
  - Full quality-gate pass: ruff zero errors, mypy zero errors, coverage 86.18% (266 tests).
  - Docker build and runtime boot verified (container logs show `app.running` phase).

- **Services & Application Layer** (`EP-0002.3 — Bundle-009`):
  - `src/eaip/services/` — `ServiceCollection` (fluent registration), `ServiceDescriptor`, `ServiceProvider` (DI bridge), `add_default_services()`, `ServiceLifetime` enum.
  - `src/eaip/app/` — `ApplicationBuilder` (fluent build), `ApplicationLifecycle` (async lifecycle manager), `ApplicationRunner` (signal-driven shutdown), `run_application()` convenience function.
  - 58 new tests across 6 test modules (unit: service collection, service provider, app lifecycle, app builder, app runner; integration: full bootstrap).
  - Full quality-gate pass: ruff zero errors, mypy zero errors, coverage 86.10% (248 tests).

- **Platform Kernel** (`EP-0002.2 — Bundle-008`):
  - `src/eaip/runtime/` — `RuntimeKernel`, `RuntimeContext`, `HookRegistry`, `Host`, `Scheduler`, `RuntimeModule` protocol.
  - `src/eaip/metrics/` — thread-safe `Counter`, `Gauge`, `Histogram`, `Meter` factory, and `prometheus_text()` OpenMetrics export.
  - 36 new unit tests (kernel lifecycle, scheduler, metrics + Prometheus export).
  - `src/eaip/runtime/README.md` documenting all modules and planned extensions.
  - Full quality-gate pass: ruff zero errors, mypy --strict zero errors, coverage 85.22% (188 tests).
- **Developer experience** (`EP-0002 + DX`):
  - `.devcontainer/devcontainer.json` — VS Code dev container targeting Python 3.13.
  - `Dockerfile` + `docker-compose.dev.yml` + `.dockerignore` for a reproducible local dev environment.
  - `scripts/bootstrap.sh` (Linux/macOS/WSL) and `scripts/bootstrap.ps1` (Windows) — one-command developer setup.
  - `scripts/healthcheck.sh` — read-only repository health check (governance docs, package layout, toolchain, configuration parsing, import safety).
  - `scripts/validate.sh` — local pre-flight gate (ruff + black + mypy + pytest) with friendly output.
  - `scripts/validate-docs.sh` — Markdown link validator skipping code spans and fences; verifies governance docs & per-package READMEs.
  - `scripts/diagnostics.sh` — environment snapshot suitable for bug reports.
  - `scripts/_dev_smoke.py` — exercises `build_platform()` end-to-end for VS Code launch config.
  - `scripts/README.md` documenting every script.
- **VS Code automation:** new `.vscode/tasks.json` (Bootstrap / Healthcheck / Validate / Format / Tests / Docker shell) and refreshed `launch.json`.
- **CI:** new `.github/workflows/docs.yml` for fast doc-only PR validation (Markdown links + healthcheck).
- **Makefile targets:** `health`, `validate`, `validate-docs`, `diagnostics`, `docker-dev`, `docker-test`.

### Changed

- `README.md` quickstart now advertises the cross-platform bootstrap scripts and devcontainer.
- `SUPPORT.md` no longer references the not-yet-existing `docs/` tree; links to `DEVELOPER_GUIDE.md` instead.

### Removed

- Stripped the pre-existing e1 pod scaffold remnants (`frontend/`, `backend/`, `yarn.lock`, `test_result.md`) — they were never part of EAIP and caused external code-review tools to scan files that don't belong to the platform.

### Fixed

- Documentation reference consistency: every Markdown internal link now resolves; every Foundation package has a `README.md` (added `src/eaip/adapters/README.md`).

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
- **Events** — in-process `EventBus` with sync/async handlers, subclass routing, and isolated failure.
- **Health** — tri-state `HealthStatus`, async `HealthCheck` protocol, aggregating `HealthReporter`.
- **Config & settings** — layered sources (`DictSource`, `EnvSource`, `FileSource`, `LayeredSource`) and a typed `PlatformSettings` hierarchy.
- **Ports & default adapters** — `ClockPort`, `IdGeneratorPort`, `SecretProviderPort` with `SystemClock`, `UuidIdGenerator`, `EnvSecretProvider` defaults.
- **Shared primitives** — typed `str` identifiers (`CorrelationId`, `RunId`, `ComponentId`, `Slug`), `Result`/`Ok`/`Err`, `Duration`, `UNSET`, JSON aliases.
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

## [0.0.3] - Unreleased

### Added (EP-0002.10 — Knowledge Engine — Bundle-016)

- **Knowledge Engine** (`Bundle-016`):
  - `src/eaip/knowledge/` — Complete knowledge subsystem: ingestion, chunking, embedding, vector storage (Qdrant), retrieval, registry, health check, and runtime integration.
  - `engine.py` — `KnowledgeEngine` orchestrates the full pipeline with flexible constructor patterns (`(registry, vs, ep)`, `(vs, ep, chunker)`, `(vs, ep)`).
  - `ingestion.py` — `KnowledgeIngestionService` with chunking, embedding, and vector-store persistence; auto-parser selection via `DocumentFormat`.
  - `retrieval.py` — `KnowledgeRetriever` with single/multi-collection `search()` and `retrieve()` returning `RetrievalResult` with `AssembledContext`.
  - `registry.py` — `KnowledgeRegistry` for in-memory tracking of collections, documents, and chunks with health reporting.
  - `health.py` — `KnowledgeHealthCheck` returning `HealthReport` (Pydantic model) for runtime health integration.
  - `integration.py` — `KnowledgeIntegration` / `KnowledgeRuntimeModule` wiring for the EAIP runtime kernel (start/stop lifecycle, health checks, capability registration).
  - `chunker.py` — `FixedSizeChunker` (token/char) and `SemanticChunker`.
  - `embedding.py` — `MockEmbeddingProvider` for testing; embedding provider protocol.
  - `qdrant_store.py` — `QdrantStore` for Qdrant vector DB integration.
  - `models.py` — All Pydantic models: `KnowledgeCollection`, `KnowledgeDocument`, `DocumentChunk`, `RetrievalQuery`, `RetrievalResult`, `RetrievedChunk`, `SourceAttribution`, `AssembledContext`, `DocumentFormat`, `ChunkingConfig`, `EmbeddingConfig`, `IngestionConfig`, `RetrievalConfig`.
  - `exceptions.py` — `KnowledgeError`, `CollectionNotFoundError`, `ChunkingError`, `EmbeddingError`, `RetrievalError`, `UnsupportedFormatError`.
  - `events.py` — Domain events: `KnowledgeEngineEvent`, `DocumentIngested`, `DocumentDeleted`.
  - 14 unit test modules, 1 integration module (lifecycle), 1 e2e module (demo).
  - Full quality-gate pass: mypy strict zero errors, ruff zero errors on all new code, coverage 77.47% on knowledge module.

### Added (EP-0002.6 — Registry & Plugin Runtime)

- **Service Registry** (`eaip.registry.service_registry`): tracks running service instances by type name with status (`REGISTERED`, `RUNNING`, `STOPPED`, `FAILED`), optional metadata, and observable change notifications.
- **Plugin Manifest enhancements** (`eaip.plugins.plugin`): added `PluginDependency` model (name, version_spec, optional flag), plus `entry_point`, `requires_platform`, `tags`, and `dependencies` fields to `PluginManifest`.
- **Plugin Discovery** (`eaip.plugins.discovery`): `PluginDiscovery` scans entry-point groups (`eaip.plugins`), single modules, or full packages recursively for `Plugin` protocol instances.
- **Dependency Validation** (`eaip.plugins.dependency`): `PluginDependencyValidator` validates semver range specs (`>=`, `~`, `^`, exact, range, `*`) and produces topological activation order via Kahn's algorithm. Circular dependencies are detected and raise `PluginError`.
- **Lifecycle Manager** (`eaip.plugins.lifecycle`): `PluginLifecycleManager` orchestrates discover → install → validate → activate (dependency-ordered) → deactivate (reverse order).
- **Runtime Integration** (`eaip.runtime.plugin_integration`): `PluginRuntimeModule` hooks into the kernel boot/shutdown lifecycle; `PluginHealthCheck` reports plugin subsystem health (healthy/degraded); domain events (`PluginInstalled`, `PluginActivated`, `PluginDeactivated`) defined for event-bus routing.
- **Loader helpers** (`eaip.plugins.loader`): `PluginLoader` gains `all()`, `count()`, and `activated_count` for introspection.
- **Tests**: 69 new tests (unit, integration, e2e) covering ServiceRegistry, dependencies, discovery, lifecycle, health check, and runtime integration.
- **Quality gates**: ruff zero errors, mypy zero errors, pytest 372/372 pass.

---

### Added (EP-0004.1 — Agent Runtime — Bundle-022)

- **Agent Runtime** (`eaip.agents`):
  - `models.py` — `AgentSpec`, `Goal`, `Plan`, `Step`, `StepStatus`, `StepType`, `RunRecord`, `RunStatus` — frozen Pydantic models for agent execution.
  - `base.py` — `Planner` protocol, `Guardrail` protocol, `GuardrailResult` — extensible planning and guardrail contracts.
  - `planner.py` — `FixedPlanner` (deterministic), `SimpleLLMPlanner` (LLM-based step decomposition).
  - `executor.py` — `StepExecutor` dispatching `TOOL_CALL` and `LLM_COMPLETION` steps with timing.
  - `guardrails.py` — `NoopGuardrail`, `CompositeGuardrail` — pre/post step hooks with block/modify semantics.
  - `events.py` — `RunStarted`, `RunCompleted`, `RunFailed`, `RunCancelled`, `StepStarted`, `StepCompleted`, `StepFailed`.
  - `exceptions.py` — `AgentError`, `AgentNotFoundError`, `RunNotFoundError`, `PlanningError`, `StepExecutionError`.
  - `health.py` — `AgentHealthCheck` reporting total/active runs.
  - `runtime.py` — `AgentRunContext`, `AgentRuntime` orchestrator with create/start/cancel/list/get lifecycle.
  - `integration.py` — `AgentRuntimeModule` for kernel registration with capabilities and health.
- **OpenTelemetry tracing**: Run and step spans with status propagation.
- **Tests**: 80 new tests across 8 modules (models, base, events, executor, guardrails, health, planner, runtime, integration).
- **Quality gates**: ruff zero errors, mypy zero errors, pytest 80/80 pass.

### Added (EP-0003.2 — LLM Adapter Contract — Bundle-021)

- **LLMAdapter Contract** (`eaip.adapters.llm`):
  - `models.py` — `LLMRequest` (frozen Pydantic with `tools: tuple[str, ...]` by name), `LLMResponse` (includes `rounds` count), `RunContext` (tenant/run/correlation IDs, `max_tool_rounds`).
  - `base.py` — `LLMAdapter` protocol (`@runtime_checkable`) with `name`, `version`, `async complete()`, `async health()`.
  - `orchestration.py` — `ToolCallOrchestrator`: call LLM → parse tool calls → execute tools via ToolRegistry → feed results back → repeat; configurable max_rounds, `MaxToolRoundsError` and `ToolExecutionError` handling.
  - `openai_adapter.py` — `OpenAIAdapter` wrapping an OpenAI-compatible `Provider` with tool orchestration and health checking.
  - `anthropic_adapter.py` — `AnthropicAdapter` wrapping an Anthropic-compatible `Provider` with tool orchestration and health checking.
  - `exceptions.py` — `LLMAdapterError`, `ToolExecutionError`, `MaxToolRoundsError`.
- **ErrorCode**: Added `INTERNAL_ERROR = "EAIP-0017"` for adapter-level failures.
- **Tests**: 35 new tests across 4 modules (models, orchestration, OpenAI adapter, Anthropic adapter).
- **Quality gates**: ruff zero errors, mypy zero errors, pytest 1093/1093 pass.

### Added (EP-0003.1 — Tool Calling & Function Support — Bundle-020)

- **Tool models** (`eaip.providers.models`): `ToolDefinition`, `ToolCall`, `ToolResult` — frozen Pydantic models for LLM tool invocation.
- **ChatRequest.tools**: Optional `tuple[ToolDefinition, ...]` field for sending tool definitions to LLM providers.
- **ChatResponse.tool_calls**: Optional `tuple[ToolCall, ...]` field for receiving tool invocation requests from LLMs.
- **OpenAICompatProvider tool calling**: Sends `tools` array in OpenAI format; parses `tool_calls` from response; handles `content: null` and malformed JSON arguments.
- **Tool Framework** (`eaip.tools`): `Tool` protocol (`@runtime_checkable`), `ToolRegistry` (register/get/unregister/all/clear), `ToolNotFoundError`/`ToolExecutionError` exceptions.
- **Built-in reference tools**: `EchoTool` (echo), `CalculatorTool` (safe arithmetic via operator module, no eval), `CurrentTimeTool` (UTC time).
- **Tests**: 77 new tests across 4 modules (tool models, tool protocol/registry, builtin tools, provider tool calling).
- **Quality gates**: ruff zero errors, mypy zero errors, pytest 1058/1058 pass.

[Unreleased]: <https://github.com/subham1902/eaip-platform/compare/v0.0.2...HEAD>
[0.0.2]: <https://github.com/subham1902/eaip-platform/releases/tag/v0.0.2>
[0.0.1]: <https://github.com/subham1902/eaip-platform/releases/tag/v0.0.1>
