# EAIP Operations Guide

> **Status:** Alpha → Beta
> **Last updated:** 2026-07-11

---

## Runtime Commands

| Command | Description |
|---------|-------------|
| `make bootstrap` | Create venv, install deps, pre-commit hooks |
| `make test` | Run full test suite with coverage |
| `make check` | Run all quality gates (fmt, lint, typecheck, test) |
| `make security` | Run security audit (bandit + pip-audit) |
| `make lint` | Run ruff linter |
| `make typecheck` | Run mypy type checker |
| `python -m eaip` | Start the EAIP platform |

## Health Checks

The EAIP platform exposes health information via the `HealthReporter` and
`InfrastructureHealthService`:

- Register checks via `HealthReporter.register(HealthCheck)`
- Aggregate report via `HealthReporter.report()`
- Infrastructure checks via `InfrastructureHealthService.check()`

### Health Status Values

| Status | Meaning |
|--------|---------|
| `healthy` | All subsystems operational |
| `degraded` | One or more subsystems degraded (non-critical) |
| `unhealthy` | One or more subsystems failed |

## Monitoring

### Key Metrics

| Metric | Source | Description |
|--------|--------|-------------|
| `repo.get.hits` | `InMemoryRepository` | Cache hit count |
| `repo.get.misses` | `InMemoryRepository` | Cache miss count |
| `repo.evictions` | `InMemoryRepository` | LRU eviction count |
| `repo.cleanup_count` | `InMemoryRepository` | Expired entries removed |
| `event.published` | `EventDispatcher` | Events published |
| `event.publish_failures` | `EventDispatcher` | Events that failed delivery |

### Runtime Diagnostics

```python
from eaip.runtime.diagnostics import RuntimeDiagnosticsService
from eaip.runtime.runtime_registry import RuntimeRegistry

diag = RuntimeDiagnosticsService()
registry = RuntimeRegistry()

snapshot = await diag.collect(
    runtime=registry,
    cache=cache_provider,
)
```

## Background Tasks

The `BackgroundTaskRegistry` manages async background tasks:

```python
registry = BackgroundTaskRegistry()

# Register a task
task = await registry.register("data-sync", sync_data())

# Check status
stats = registry.get_stats()
# {"active_count": 1, "total_count": 5, "failed_count": 0, ...}

# Graceful shutdown
registry.cancel_all()
await registry.await_all(timeout=5.0)
```

## Backup

See `BACKUP_AND_RECOVERY.md` for detailed procedures.

## Logging

Structured JSON logging via `LoggerPort` → `InMemoryLogger`.

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

Default production level: `INFO`

## Secrets Management

Secrets are resolved via `SecretProviderPort` → `EnvSecretProvider`.

In production, use a vault-backed adapter implementing `SecretProviderPort`.

Required secrets:
- `EAIP_AUTH_SECRET` — JWT signing key
- `EAIP_DB_PASSWORD` — database password
