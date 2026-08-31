# EAIP Runtime Architecture

> **Status:** Alpha Converged
> **Last updated:** 2026-07-11

---

## Runtime Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Mission Control Layer                     │
│  MissionRegistry · Mission · MissionStatus                  │
│  RuntimeRegistry · RuntimeDiagnosticsService                │
├─────────────────────────────────────────────────────────────┤
│                    Orchestration Layer                       │
│  WorkflowEngine · WorkflowRegistry · WorkflowStateMachine   │
│  AgentRuntime · AgentRegistry · StepExecutor                │
├─────────────────────────────────────────────────────────────┤
│                    Capability Layer                          │
│  KnowledgeEngine · KnowledgeRetriever · IngestionPipeline   │
│  AuthenticationService · TokenService                       │
├─────────────────────────────────────────────────────────────┤
│                    Foundation Layer                          │
│  EventBus · EventDispatcher · Scheduler · HealthReporter    │
│  InMemoryRepository · InMemoryCacheProvider                 │
│  BackgroundTaskRegistry                                     │
├─────────────────────────────────────────────────────────────┤
│                    Ports & Adapters Layer                    │
│  CacheProvider · MetricsProvider · TracingProvider          │
│  LoggerPort · ClockPort · SecretProviderPort                │
│  VectorStore · EmbeddingProvider · DocumentParser           │
└─────────────────────────────────────────────────────────────┘
```

## Runtime Lifecycle

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Created  │────►│ Starting │────►│ Running  │────►│ Stopped  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                        │
                                   ┌────┴────┐
                                   │  Paused │
                                   └─────────┘
```

## Component Registry

| Component | Registry | Storage |
|-----------|----------|---------|
| Agent Definitions | `AgentRegistry` | In-memory dict |
| Workflow Definitions | `WorkflowRegistry` | In-memory dict |
| Missions | `MissionRegistry` | In-memory dict |
| Runtime State | `RuntimeRegistry` | In-memory counters |
| Background Tasks | `BackgroundTaskRegistry` | In-memory task set |
| Tokens | `TokenService._tokens` | `InMemoryRepository` |
| Collaboration Sessions | `CoordinationEngine._sessions` | `InMemoryRepository` |
| Cache | `ResponseCache._cache` | `CacheProvider` → `InMemoryCacheProvider` |
| Health Checks | `HealthReporter._checks` | In-memory dict |

## Event Flow

```
Service ──► EventBus.publish(event)
                │
                ├──► Subscriber 1 (sync handler)
                │
                ├──► Subscriber 2 (async handler)
                │
                └──► Dispatcher (retry, hooks, metrics)
```

All domain events inherit from `DomainEvent` and follow the
`eaip.<domain>.<action>` naming convention.

## Background Task Lifecycle

```
BackgroundTaskRegistry.register(name, coro)
    │
    ├──► Task created via asyncio.ensure_future
    │
    ├──► Tracked in _tasks dict + _infos dict
    │
    ├──► On completion: auto-removed from _tasks
    │
    └──► On cancel: CancelledError propagated, tracked as failed
```

## Health Check Architecture

```
HealthReporter
    │
    ├──► register(HealthCheck)
    │       │
    │       └──► async check() → HealthReport
    │
    └──► report()
            │
            └──► asyncio.gather(*checks) → HealthReport (aggregated)
```

## Infrastructure Health

```
InfrastructureHealthService
    │
    ├──► register_connection("cache", is_connected=True)
    ├──► register_connection("database", is_connected=False)
    │
    └──► check() → HealthReport (worst-status aggregation)
```

## Ports Summary

| Port | Protocol | Default Adapter |
|------|----------|-----------------|
| `CacheProvider` | `ports/cache.py` | `InMemoryCacheProvider` |
| `ClockPort` | `ports/clock.py` | `SystemClock` |
| `IdGeneratorPort` | `ports/id_generator.py` | `UuidIdGenerator` |
| `SecretProviderPort` | `ports/secret_provider.py` | `EnvSecretProvider` |
| `LoggerPort` | `ports/logger.py` | `InMemoryLogger` |
| `MetricsProvider` | `ports/metrics.py` | `InMemoryMetricsProvider` |
| `TracingProvider` | `ports/tracing.py` | `NoOpTracingProvider` |
| `VectorStore` | `knowledge/base.py` | `QdrantStore` / `_MemoryVectorStore` |
| `EmbeddingProvider` | `knowledge/base.py` | `MockEmbeddingProvider` |
| `DocumentParser` | `knowledge/base.py` | `TextParser` / `MarkdownParser` / etc. |
