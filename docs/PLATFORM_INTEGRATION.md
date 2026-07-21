# EAIP Platform Integration

> **Status:** Alpha Converged
> **Last updated:** 2026-07-11

---

## Enterprise Flow

```
Login
  │
  ▼
Knowledge Upload ──► Parsing ──► Chunking ──► Embedding ──► Vector Store
  │
  ▼
Agent Registry ──► Agent Execution
  │
  ▼
Workflow Registry ──► Workflow Engine
  │
  ▼
Mission Control ──► Mission Registry ──► Runtime Registry
  │
  ▼
Event Bus ──► Observability ──► Infrastructure Health
```

## Verified Integration Points

| Step | Component | Verified In |
|------|-----------|-------------|
| 1 | Login | `auth/auth_providers.py`, `test_auth_integration.py` |
| 2 | Knowledge Upload | `knowledge/ingestion.py`, `test_knowledge_pipeline.py` |
| 3 | Document Parsing | `knowledge/ingestion.py` (5 parsers) |
| 4 | Chunking | `knowledge/chunker.py`, `test_knowledge_ingestion.py` |
| 5 | Embedding | `knowledge/ingestion.py` (Provider abstraction) |
| 6 | Vector Store | `knowledge/base.py` (VectorStore protocol) |
| 7 | Knowledge Search | `knowledge/retrieval.py`, `test_knowledge_retrieval.py` |
| 8 | Agent Registry | `agents/registry.py`, `test_agent_lifecycle.py` |
| 9 | Agent Execution | `agents/runtime.py`, `test_agent_runtime_integration.py` |
| 10 | Workflow Registry | `workflow/registry.py`, `test_workflow_lifecycle.py` |
| 11 | Workflow Engine | `workflow/executor.py`, `test_workflow_integration.py` |
| 12 | Mission Control | `runtime/mission.py`, `test_mission_control.py` |
| 13 | Runtime Registry | `runtime/runtime_registry.py`, `test_mission_control.py` |
| 14 | Event Bus | `events/bus.py`, `test_event_flow.py` |
| 15 | Infrastructure Health | `infrastructure/health.py`, `test_platform_convergence.py` |
| 16 | End-to-End Flow | `test_platform_convergence.py` |

## Crossing Concerns

| Concern | Implementation |
|----------|---------------|
| Authentication | `auth/` — TokenService, AuthenticationService, JWT |
| Authorization | `policy/` — PolicyEngine, RBAC/ABAC |
| Event Bus | `events/` — EventBus, EventDispatcher, retry |
| Repository | `shared/repository.py` — InMemoryRepository |
| Cache | `ports/cache.py` — CacheProvider → InMemoryCacheProvider |
| Metrics | `ports/metrics.py` — MetricsProvider → InMemoryMetricsProvider |
| Tracing | `ports/tracing.py` — TracingProvider → NoOpTracingProvider |
| Logging | `ports/logger.py` — LoggerPort → InMemoryLogger |
| Health | `health/` — HealthReporter, HealthCheck protocol |
| Diagnostics | `runtime/diagnostics.py` — RuntimeDiagnosticsService |
| Background Tasks | `shared/background_task_registry.py` — TaskRegistry |
| Secrets | `ports/secret_provider.py` — SecretProviderPort → EnvSecretProvider |

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| All services communicate via EventBus | Loose coupling, audit trail, replayability |
| Ports/Adapters for all infrastructure | Swap backends without service changes |
| Optional constructor injection | Backward compatibility, testability |
| In-memory defaults for all adapters | Zero infrastructure required for development/testing |
| Collection-based isolation | Natural workspace/tenant separation |
