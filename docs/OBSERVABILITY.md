# EAIP Observability Architecture

> **Status:** Alpha
> **Last updated:** 2026-07-11

---

## Overview

EAIP provides a comprehensive observability framework based on the **Ports & Adapters** pattern. Every observability concern (logging, metrics, tracing, health) is defined as a `Protocol` port with an in-memory default adapter, ensuring that production deployments can swap in external backends (OpenTelemetry, Prometheus, Datadog, etc.) without changing any service code.

```
┌─────────────────────────────────────────────────────────┐
│                   Service / Capability                    │
│  (depends only on port Protocols — never on adapters)     │
└────────────────────┬────────────────────────────────────┘
                     │ depends on
                     ▼
┌─────────────────────────────────────────────────────────┐
│                      Ports Layer                          │
│  LoggerPort · MetricsProvider · TracingProvider          │
│  HealthCheck · HealthReporter                            │
└────────────────────┬────────────────────────────────────┘
                     │ implemented by
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                    │
│  InMemoryLogger · InMemoryMetricsProvider                │
│  NoOpTracingProvider · InMemoryCacheProvider             │
│  SystemClock · EnvSecretProvider                         │
└─────────────────────────────────────────────────────────┘
```

---

## 1. Logging — `LoggerPort`

**Port:** `eaip.ports.logger.LoggerPort`

**Default adapter:** `eaip.infrastructure.logger.InMemoryLogger`

### Interface

```python
class LoggerPort(Protocol):
    def debug(self, event: str, **context: Any) -> None: ...
    def info(self, event: str, **context: Any) -> None: ...
    def warning(self, event: str, **context: Any) -> None: ...
    def error(self, event: str, **context: Any) -> None: ...
    def critical(self, event: str, **context: Any) -> None: ...
    def bind(self, **context: Any) -> LoggerPort: ...
    def is_enabled_for(self, level: str) -> bool: ...
```

### Structured Event Convention

Events follow a `domain.action` naming convention:

| Domain | Examples |
|--------|----------|
| `auth.*` | `auth.token.created`, `auth.token.expired` |
| `event.*` | `event.published`, `event.handler_failed` |
| `cache.*` | `cache.hit`, `cache.miss`, `cache.evicted` |
| `repo.*` | `repo.get`, `repo.add`, `repo.cleanup` |
| `workflow.*` | `workflow.started`, `workflow.completed` |
| `agent.*` | `agent.run.started`, `agent.run.completed` |

### Default Level: `INFO`

### Example

```python
logger = InMemoryLogger(level="INFO")
logger.info("auth.token.created", user_id="abc", token_type="access")
```

---

## 2. Metrics — `MetricsProvider`

**Port:** `eaip.ports.metrics.MetricsProvider`

**Default adapter:** `eaip.infrastructure.metrics.InMemoryMetricsProvider`

### Metric Types

| Type | Behavior | Use Case |
|------|----------|----------|
| `Counter` | Monotonically increasing | Request count, event count |
| `Gauge` | Set, inc, dec | Active connections, queue depth |
| `Histogram` | Value distribution | Request latency, payload size |
| `Timer` | Duration recording | Method execution time |

### Instrumentation Points

| Component | Metrics |
|-----------|---------|
| Repository | `repo.get.hits`, `repo.get.misses`, `repo.evictions`, `repo.cleanup` |
| Cache | `cache.hits`, `cache.misses`, `cache.evictions` |
| Event Bus | `event.published`, `event.failures`, `event.handler_count` |
| Authentication | `auth.login.success`, `auth.login.failure`, `auth.token.created` |
| Automation | `automation.rules.evaluated`, `automation.actions.executed` |
| Gateway | `gateway.requests.total`, `gateway.requests.latency` |
| Pipelines | `pipeline.runs.total`, `pipeline.runs.failed`, `pipeline.steps.duration` |

### Example

```python
metrics = InMemoryMetricsProvider()
counter = metrics.counter("auth.login.success")
counter.inc()
snapshot = metrics.get_snapshot()
```

---

## 3. Tracing — `TracingProvider`

**Port:** `eaip.ports.tracing.TracingProvider`

**Default adapter:** `eaip.infrastructure.tracing.NoOpTracingProvider`

### Interface

```python
class TracingProvider(Protocol):
    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Span: ...
    @contextmanager
    def span(self, name: str, attributes: dict[str, Any] | None = None) -> Iterator[Span]: ...
    def inject(self, span: Span) -> dict[str, str]: ...
    def current_span_id(self) -> str | None: ...
    def current_trace_id(self) -> str | None: ...
```

The `NoOpTracingProvider` discards all spans. A future `OpenTelemetryTracingProvider` adapter will export to OTLP without service changes.

---

## 4. Health Services

| Service | Endpoint | Description |
|---------|----------|-------------|
| `HealthReporter` | Internal | Aggregates per-component health checks |
| `GET /live` | HTTP | Liveness probe — 200 while the process is alive |
| `GET /ready` | HTTP | Readiness probe — 200 when critical/required deps are healthy or skipped |
| `GET /health` | HTTP | Full dependency report — 200 when healthy/skipped/degraded, 503 when unhealthy |
| `RuntimeDiagnosticsService` | Internal | Collects system-wide metrics snapshot |

### Dependency Classification

Each health check declares a `criticality` (`critical`, `required`, or
`optional`) and a `configured` flag. The `HealthReporter` copies these onto
the produced `HealthReport` and uses them for readiness gating:

- **Critical** — core platform components (application process, agent runtime,
  workflow engine, knowledge engine, memory engine, infrastructure).
- **Required** — the configured database provider, event bus. These gate
  readiness; an unhealthy required dependency fails `/ready`.
- **Optional** — Sentry, Better Stack, analytics, telemetry. These may report
  `degraded` without ever failing `/ready`.

A dependency that has no external component to check — such as the `local`
database provider — reports status `skipped` instead of `unhealthy`, so local
development never fails readiness because of an intentionally absent external
service.

`HealthStatus` is ordered `healthy < skipped < degraded < unhealthy`, and the
reporter's rollup picks the worst child status. `/ready` fails (503) only when
a critical or required dependency is unhealthy.

### Runtime Diagnostics

The `RuntimeDiagnosticsService.collect()` method accepts named components and
returns a structured dict:

```python
diag = RuntimeDiagnosticsService()
snapshot = await diag.collect(
    cache=cache_provider,
    repository=token_repo,
    event_bus=event_bus,
)
# Returns:
# {
#   "timestamp": "2026-07-11T12:00:00Z",
#   "uptime_seconds": 1234.5,
#   "cache": {"size": 42, "hit_rate_pct": 87.5, ...},
#   "repository": {"size": 100, "eviction_count": 5, ...},
#   ...
# }
```

### Component Requirements

Any component passed to `collect()` should implement one of:
- `get_stats() -> dict`
- `get_snapshot() -> dict`
- `active_count -> int`

---

## 5. Background Task Registry — `BackgroundTaskRegistry`

**Location:** `eaip.shared.background_task_registry`

Replaces scattered `asyncio.ensure_future()` calls with a central registry.

| Method | Purpose |
|--------|---------|
| `register(name, coro)` | Register and track an async task |
| `register_fire_and_forget(name, coro)` | Fire a task without awaiting it |
| `await_all(timeout)` | Gracefully wait for all tasks |
| `cancel(task_id)` | Cancel a specific task |
| `cancel_all()` | Cancel all tracked tasks |
| `active_count` | Count of running tasks |
| `total_count` | Count of all registered tasks |
| `failed_count` | Count of failed tasks |
| `get_stats()` | Snapshot of all task state |

### Example

```python
registry = BackgroundTaskRegistry()
await registry.register("data-sync", sync_data())
# ... on shutdown:
registry.cancel_all()
await registry.await_all(timeout=5.0)
```

---

## 6. Integration with Existing Infrastructure

### Dependency Injection

All observability ports support optional constructor injection:

```python
class MyService:
    def __init__(
        self,
        logger: LoggerPort | None = None,
        metrics: MetricsProvider | None = None,
        tracer: TracingProvider | None = None,
    ):
        self._logger = logger or InMemoryLogger()
        self._metrics = metrics or InMemoryMetricsProvider()
        self._tracer = tracer or NoOpTracingProvider()
```

This pattern is already used across the platform for `EventBus`, `SecretProviderPort`, etc.

---

## 7. Architecture Diagram

```
                           ┌──────────────────────────┐
                           │   External Observability   │
                           │  (Prometheus / Datadog /   │
                           │   OpenTelemetry / ELK)     │
                           └──────────┬───────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                  ▼
            ┌────────────┐   ┌────────────┐   ┌──────────────┐
            │  LoggerPort │   │ Metrics    │   │ Tracing      │
            │             │   │ Provider   │   │ Provider     │
            └──────┬──────┘   └──────┬─────┘   └──────┬───────┘
                   │                 │                 │
            ┌──────▼──────┐   ┌──────▼─────┐   ┌──────▼───────┐
            │ InMemory    │   │ InMemory   │   │ NoOp         │
            │ Logger      │   │ Metrics    │   │ Tracing      │
            │             │   │ Provider   │   │ Provider     │
            └─────────────┘   └────────────┘   └──────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    Platform Services                             │
│  Repository · Cache · EventBus · Auth · Automation · Gateway    │
│  (instrumented via optional port injection)                     │
└────────────────────────────────────────────────────────────────┘
```

---

## 8. Extending with a New Backend

To add a Prometheus metrics adapter:

```python
from eaip.ports.metrics import MetricsProvider

class PrometheusMetricsProvider(MetricsProvider):
    def counter(self, name, labels=None):
        return prometheus_client.Counter(name, "", labels or {})
    # ... implement remaining methods
```

Then inject it via DI:

```python
service = MyService(metrics=PrometheusMetricsProvider())
```

No changes to `MyService` or any platform code are required.

---

## 9. Sentry Error Tracking & Performance Monitoring

EAIP integrates with **Sentry** for error tracking and performance monitoring via the `eaip.integrations.sentry` module.

### Configuration

All Sentry settings are driven by environment variables under the `EAIP_SENTRY_` prefix (read by `SentrySettings` in `eaip.settings.core_settings`):

| Variable | Description | Default |
|----------|-------------|---------|
| `EAIP_SENTRY_DSN` | Sentry DSN. When unset or empty, Sentry is disabled. | (none) |
| `EAIP_SENTRY_ENVIRONMENT` | Environment name (e.g. `staging`, `production`). | `core.environment_name` |
| `EAIP_SENTRY_RELEASE` | Release version string. | `eaip._version.__version__` |
| `EAIP_SENTRY_TRACES_SAMPLE_RATE` | Rate for performance traces (0.0–1.0). | `0.0` |
| `EAIP_SENTRY_SEND_DEFAULT_PII` | Whether to send PII in events. | `false` |
| `EAIP_SENTRY_ATTACH_STACKTRACE` | Attach stack traces to messages. | `true` |
| `EAIP_SENTRY_PROFILE_LIFE_CYCLE` | Profile lifecycle mode. | `auto` |

### Production-Safe Defaults

Sentry is fully disabled by default. It must be explicitly enabled by setting `EAIP_SENTRY_DSN`. Performance tracing and session replays default to zero sampling, and `send_default_pii` is `false`, ensuring no sensitive data is collected unless intentionally configured.

### Backend Integration

Sentry is initialised in `create_app()` when building the FastAPI application and adds a Sentry error-capture middleware:

```python
# In eaip.http.api.create_app():
init_sentry(lifecycle.platform.settings)
add_sentry_middleware(app)
```

A `SentryHealthCheck` is registered with the platform health reporter, so Sentry availability is reflected in `/health` and `/ready` endpoints.

### Frontend Integration

Both the `enterprise-console` and `administration` Next.js apps include Sentry via `@sentry/nextjs`. Initialisation is in `src/lib/sentry.ts` and `src/instrumentation.ts`, reading from `NEXT_PUBLIC_SENTRY_*` environment variables with the same production-safe defaults.

Client-side errors are reported in the existing `src/app/error.tsx` error boundary via `Sentry.Sentry.captureException(error)`.

### Release Tracking

Release versions are automatically derived from `eaip._version.__version__` when `EAIP_SENTRY_RELEASE` is not set. On the frontend, set `NEXT_PUBLIC_SENTRY_RELEASE` to pin a release version.
