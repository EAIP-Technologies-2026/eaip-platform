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

### Added (EP-0023 — Enterprise Workflow & Multi-Agent Orchestration — Bundle-023)

- **Workflow State Machine** (`src/eaip/workflow/state_machine.py`): `WorkflowStateMachine`, `StepStateMachine` — finite state machines for workflow and step lifecycle enforcement with valid transitions, terminal state detection, and `InvalidStateTransitionError`.
- **Enhanced Workflow Models** (`src/eaip/workflow/models.py`): Added `TimeoutConfig`, `ParallelGroup`, `DurableExecutionConfig`, `ParentChildConfig`, `WorkflowStatus.TIMED_OUT`, `WorkflowStepStatus.TIMED_OUT`, `WorkflowStep.approval_token`, `WorkflowRun.child_run_ids`/`state_machine_state`, `WorkflowResult.timed_out_count`/`child_results`, `WorkflowContext.add_agent_output`/`add_tool_output`/`add_memory_key`.
- **Parallel Execution** (`src/eaip/workflow/executor.py`): DAG execution supports `ParallelGroup` with async concurrent step execution, configurable completion conditions, and group-level timeouts.
- **Enhanced Timeout Handling**: Workflow-level timeout via `TimeoutConfig.workflow_timeout_seconds`, step-level timeout enforcement, `WorkflowTimedOut`/`WorkflowStepTimedOut` events.
- **Human Approval Checkpoints**: `requires_approval` field on `WorkflowStep`, checkpoint save/restore in `StepApprovalHandler`, `approval_prompt` support.
- **Parent/Child Workflows**: `execute_child()` method on `WorkflowEngine`, `ParentChildConfig` for context inheritance and failure propagation.
- **Enhanced Agent Orchestration** (`src/eaip/workflow/agents.py`): Memory context loading/saving, `broadcast_message`, `count_unread`.
- **Event Extensions**: 8 new workflow domain event types.
- **Exception Extensions**: `WorkflowTimeoutError`, `ParallelExecutionError`, `ChildWorkflowError`, `DurableExecutionError`.
- **Health Check Enhancement**: `WorkflowHealthCheck` now reports running/paused/failed/timed_out/pending_approval counts.
- **Tests**: 155 passing tests (82 new for Bundle-023).

### Added (EP-0024 — Enterprise Governance & Policy Runtime — Bundle-024)

- **Resource, Tool, Department, Workflow, Approval Policies** (`src/eaip/policy/resource_policies.py`): 6 new frozen Pydantic policy models with `ResourcePolicy`, `ToolPolicy` (`ToolAccessLevel`), `DepartmentPolicy`, `WorkflowPolicy`, `ApprovalPolicy`, `PolicyEvaluationReport`.
- **Policy Exports**: Updated `eaip.policy.__init__` with all new policy types.
- **Tests**: 19 passing tests covering all new policy types.

### Added (EP-0025 — Context & Prompt Intelligence — Bundle-025)

- **New Package** `src/eaip/context/`: Context and prompt intelligence subsystem.
- **Prompt Registry** (`registry.py`): `PromptRegistry` with version tracking, CRUD, observer pattern for change notifications.
- **Prompt Manager** (`templates.py`): `PromptManager` for template creation, variable rendering, validation, version management, and policy checking.
- **Context Builder** (`builder.py`): `ContextBuilder` for assembling context from documents, relevance filtering, token truncation, and integration with Memory Engine and Knowledge Engine.
- **Context Compression** (`compression.py`): `ContextCompressor` with three strategies: extractive (score-based), summarize (top-k), truncate (token-limit).
- **Domain Models** (`models.py`): `PromptTemplate`, `PromptVersion`, `PromptRegistryEntry`, `ContextBuilderConfig`, `ContextDocument`, `AssembledContext`, `ContextCacheConfig`, `CompressionConfig`, `CompressionStrategy`.
- **Domain Events** (`events.py`): `PromptCreated`, `PromptVersioned`, `ContextAssembled`, `ContextCompressed`.
- **Exception Hierarchy** (`exceptions.py`): `ContextError`, `PromptNotFoundError`, `TemplateRenderError`, `ContextAssemblyError`, `CompressionError`.
- **Health Check & Integration** (`health.py`, `integration.py`): `ContextHealthCheck` and `ContextRuntimeModule` for kernel lifecycle.
- **Tests**: 89 passing tests across 7 test modules.

### Added (EP-0026 — Knowledge & RAG Orchestrator — Bundle-026)

- **Retrieval Engine** (`src/eaip/knowledge/retrieval_engine.py`): `RetrievalEngine` with hybrid search (semantic+keyword), configurable alpha weighting, reranking support, and multi-collection search.
- **Search Strategies** (`src/eaip/knowledge/search_strategies.py`): `SearchStrategy` protocol with `SemanticSearchStrategy`, `KeywordSearchStrategy` (BM25-like), `HybridSearchStrategy` (weighted score merge); `RerankingStrategy` protocol with `SimpleReranker` and `CrossEncoderReranker`.
- **Knowledge Federation** (`src/eaip/knowledge/federation.py`): `KnowledgeFederation` for search across multiple collections, knowledge+memory, department brain (scoped), enterprise brain (cross-department) with deduplication and score normalization.
- **Retrieval Policies** (`src/eaip/knowledge/policies.py`): `RetrievalPolicy`, `CollectionAccessPolicy`, `RetrievalPolicyEnforcer` for RBAC on knowledge collection access.
- **Event Extensions**: `HybridSearchExecuted`, `FederatedSearchExecuted`.
- **Tests**: 53 passing tests across 4 test modules (10 retrieval engine, 11 strategies, 11 federation, 12 policies).

### Added (EP-0031 — Enterprise Brain — Bundle-031)

- **Enterprise Brain** (`src/eaip/brain/`): Unified intelligence layer orchestrating knowledge, memory, context, and agent insights.
- `enterprise_brain.py` — `EnterpriseBrain` with `query()`, `query_knowledge()`, `query_memory()`, `query_context()`, `query_agents()` — merges results from all sources with deduplication, threshold filtering, reranking, and confidence scoring.
- `models.py` — `BrainQuery`, `BrainResult`, `BrainSource`, `EnterpriseBrainConfig` frozen Pydantic models.
- `events.py` — `BrainQueryExecuted`, `BrainKnowledgeRetrieved`, `BrainMemoryRetrieved`, `BrainContextBuilt`.
- `exceptions.py` — `BrainError`, `BrainQueryError`, `BrainSourceUnavailableError`.
- `health.py`, `integration.py` — `BrainHealthCheck` and `BrainRuntimeModule` for kernel lifecycle.
- **Tests**: 36 passing tests across 3 test modules.

### Added (EP-0032 — Department Brains — Bundle-032)

- **Department Brains** (`src/eaip/brain/`): Scoped brain instances for business departments with access control.
- `department_brain.py` — `DepartmentBrain` with scoped queries, config overrides, `sync_from_enterprise()`, `DepartmentBrainConfig`.
- `brain_registry.py` — `BrainRegistry` for register/get/list departments, `query_all()` (parallel), `query_departments()`.
- `access.py` — `BrainAccessManager` with `check_access()` and `authorize_query()` integrating with `PolicyEvaluationContext`.
- `events.py` — Added `DepartmentBrainQueryExecuted`, `BrainAccessDenied`, `BrainSyncCompleted`.
- `exceptions.py` — Added `BrainAccessDeniedError`.
- **Tests**: 36 new passing tests (90 total across brain package).

### Added (EP-0033 — Digital Workforce Runtime — Bundle-033)

- **Workforce Runtime** (`src/eaip/workforce/`): Orchestrates agents, workflows, and jobs.
- `models.py` — `WorkerDefinition`, `WorkerAssignment`, `WorkforceConfig`, `WorkforceMetrics`.
- `worker.py` — `WorkerRegistry` with register/unregister/get/list/count.
- `orchestrator.py` — `WorkforceOrchestrator` with `assign()`, `assign_best_worker()`, `execute_assignment()`, `get_status()`, `cancel_assignment()`.
- `scheduler.py` — `WorkforceScheduler` for cron/interval worker scheduling using `JobScheduler`.
- `events.py` — 6 domain events for worker lifecycle.
- `exceptions.py` — `WorkforceError`, `WorkerNotFoundError`, `WorkerBusyError`, `AssignmentError`.
- `health.py`, `integration.py` — health check and kernel lifecycle.
- **Tests**: 71 passing tests across 5 test modules.

### Added (EP-0034 — Business Goal Engine — Bundle-034)

- **Goal Engine** (`src/eaip/goals/`): Define, track, and execute business goals.
- `models.py` — `BusinessGoal`, `Objective`, `KpiDefinition`, `GoalProgress`, `GoalConfig` with enums (`GoalStatus`, `Priority`, `MeasurementType`, `KpiDirection`, `ObjectiveStatus`).
- `engine.py` — `GoalEngine` with 11 async methods for CRUD, evaluation, assignment, deployment.
- `tracker.py` — `GoalTracker` for KPI recording, history, trend analysis, threshold checking.
- `events.py` — 8 domain events for goal lifecycle and KPI monitoring.
- `exceptions.py` — 5 exception classes.
- `health.py`, `integration.py` — health check and kernel lifecycle.
- **Tests**: 78 passing tests across 5 test modules.

### Added (EP-0035 — Enterprise Search & Federation — Bundle-035)

- **Enterprise Search** (`src/eaip/search/`): Enterprise-wide federated search across knowledge, memory, and custom providers.
- `models.py` — `SearchQuery`, `SearchResult`, `SearchResultItem`, `SearchFilter`, `SearchProviderConfig`, `Pagination`.
- `providers.py` — `SearchProvider` protocol, `KnowledgeSearchProvider`, `MemorySearchProvider`, `CompositeSearchProvider`.
- `engine.py` — `EnterpriseSearchEngine` with provider registration, cross-provider search, pagination, result merging.
- `ranking.py` — `RankingService` for score normalization, query-aware reranking, configurable weights.
- `federation.py` — `SearchFederation` for enterprise-wide and department-scoped search.
- `events.py`, `exceptions.py`, `health.py`, `integration.py` — domain events, exceptions, health check, runtime module.
- **Tests**: 90 passing tests across 7 test modules.

### Added (EP-0036 — Context & Session Intelligence — Bundle-036)

- **Session Management** (`src/eaip/session/`): Enterprise session and context management with lifecycle and propagation.
- `models.py` — `Session`, `SessionContext`, `ContextScope`, `ContextPropagationConfig`, `SessionConfig`, `ExecutionContext`.
- `manager.py` — `SessionManager` with create/get/update/close/suspend/resume/expire, TTL-based expiry, filtered listing.
- `context_manager.py` — `EnterpriseContextManager` with scope-based attribute management, propagation, session context building.
- `serialization.py` — `SessionSerializer` for serialize/deserialize/export/import.
- `lifecycle.py` — `SessionLifecycleManager` for expiry cycles, tenant cleanup, transfer, merge.
- `events.py` — 9 domain events, `exceptions.py` — 5 exceptions, `health.py`, `integration.py`.
- **Tests**: 95 passing tests across 7 test modules.

### Added (EP-0037 — Collaboration & Workflow Runtime — Bundle-037)

- **Collaboration Runtime** (`src/eaip/collaboration/`): Multi-agent collaboration with coordination, delegation, approval.
- `models.py` — `CollaborationSession`, `AgentTask`, `DelegationRequest`, `CoordinationConfig`, `CollaborationResult`, `SharedState`.
- `coordinator.py` — `CoordinationEngine` with 4 strategy implementations (sequential, parallel, broadcast, auction).
- `delegation.py` — `TaskDelegationService` for agent task delegation lifecycle.
- `approval.py` — `CollaborationApprovalService` for multi-party approval workflows.
- `state.py` — `SharedStateManager` with versioned shared state and conflict detection.
- `tracking.py` — `ExecutionTracker` for session/agent timelines, reports, metrics.
- `events.py` — 15 domain events, `exceptions.py` — 6 exceptions, `health.py`, `integration.py`.
- **Tests**: 123 passing tests across 8 test modules.

### Added (EP-0038 — Enterprise Analytics & Insights — Bundle-038)

- **Analytics & Insights** (`src/eaip/analytics/`): KPI engine, analytics service, trends, aggregation, dashboards.
- `models.py` — `MetricDefinition`, `MetricPoint`, `TimeSeriesPoint`, `TimeSeriesResult`, `AnalyticsReport`, `TrendAnalysis`, `DashboardDefinition`, `DashboardWidget`, `AnalyticsConfig`.
- `service.py` — `AnalyticsService` for metric recording, time-series queries, report generation.
- `kpi_engine.py` — `KpiEngine` integrating with GoalTracker for KPI evaluation and trend analysis.
- `trends.py` — `TrendAnalyzer` with trend detection, anomaly detection (std-dev), forecasting (linear regression), period comparison, seasonality detection (autocorrelation).
- `aggregation.py` — `AggregationEngine` with sum/avg/min/max/count/latest, rollups, derived metrics, percentiles (p50/p95/p99).
- `dashboard.py` — `DashboardService` with full CRUD, widget rendering, dashboard rendering.
- `telemetry.py` — `TelemetryCollector` for operational and platform metric collection.
- `events.py` — 7 domain events, `exceptions.py` — 5 exceptions, `health.py`, `integration.py`.
- **Tests**: 145 passing tests across 9 test modules.

### Added (EP-0039 — Knowledge Graph Runtime — Bundle-039)

- **Knowledge Graph** (`src/eaip/kgraph/`): Enterprise knowledge graph with entity/relationship model, traversal, and semantic APIs.
- `models.py` — `Entity`, `Relationship`, `GraphQuery` (BFS/DFS/shortest_path/subgraph modes), `GraphResult`, `Path`, `GraphConfig`, `EntityIndex`, `GraphStats`.
- `graph.py` — `KnowledgeGraph` with entity/relationship CRUD, cascade delete, 5 query modes, neighbor/property search, graph statistics.
- `traversal.py` — `GraphTraversalService` with BFS/DFS depth-limited traversal, shortest path, subgraph extraction, conditional paths, cycle detection, degree centrality.
- `index.py` — `GraphIndex` with inverted index for entities/relationships, rebuild/clear.
- `semantic.py` — `SemanticRelationshipService` with relationship inference via shared properties, Jaccard similarity, entity clustering, missing relationship suggestions.
- 10 domain events, 6 exceptions, health check, runtime module.
- **Tests**: 139 passing tests across 7 test modules.

### Added (EP-0040 — Enterprise Automation Runtime — Bundle-040)

- **Automation Runtime** (`src/eaip/automation/`): Enterprise rule-based automation engine with event triggers and scheduling.
- `models.py` — `AutomationRule`, `RuleCondition`, `RuleAction`, `AutomationExecution`, `TriggerEvent`, `AutomationConfig`, `ExecutionHistoryEntry`.
- `engine.py` — `AutomationEngine` with rule CRUD, condition evaluation, action execution, concurrency control, execution lifecycle.
- `triggers.py` — `TriggerService` with event processing, listener management, wildcard support, EventBus integration.
- `executor.py` — `ActionExecutor` with webhook (httpx), workflow, agent, command (subprocess), event, notification actions. Exponential backoff retry.
- `scheduler.py` — `AutomationScheduler` with cron-based scheduling via croniter.
- `history.py` — `ExecutionHistory` with record/query/cleanup, per-rule statistics.
- 11 domain events, 6 exceptions, health check, runtime module.
- **Tests**: 128 passing tests across 8 test modules.

[Unreleased]: <https://github.com/subham1902/eaip-platform/compare/v0.0.2...HEAD>
[0.0.2]: <https://github.com/subham1902/eaip-platform/releases/tag/v0.0.2>
[0.0.1]: <https://github.com/subham1902/eaip-platform/releases/tag/v0.0.1>
