# EAIP Production Adapters

> **Status:** Alpha → Beta
> **Last updated:** 2026-07-11

---

## Overview

EAIP uses a **Ports & Adapters** architecture. All platform services depend only on port interfaces (Protocols/ABCs). Production adapters implement these ports and can be swapped via dependency injection without any service code changes.

## Adapter Matrix

| Port | Default Adapter | Production Adapter | External Dep |
|------|----------------|-------------------|--------------|
| `AbstractRepository` | `InMemoryRepository` | `PostgresRepository` | `asyncpg` |
| `CacheProvider` | `InMemoryCacheProvider` | `RedisCacheProvider` | `redis` |
| `SecretProviderPort` | `EnvSecretProvider` | `FileSecretProvider` | None |
| `MetricsProvider` | `InMemoryMetricsProvider` | `PrometheusMetricsProvider` | `prometheus_client` |
| `TracingProvider` | `NoOpTracingProvider` | `OTelTracingProvider` | `opentelemetry-*` |
| Object Storage | None | `ObjectStorageProvider` | `minio` |

## PostgreSQL Repository

**File:** `src/eaip/infrastructure/postgres_repository.py`
**Implements:** `AbstractRepository`

```python
from eaip.infrastructure.postgres_repository import PostgresRepository

repo = PostgresRepository[CorrelationId, AuthToken](
    table_name="auth_tokens",
    dsn="postgresql://user:pass@host:5432/db",
    pool_min_size=2,
    pool_max_size=10,
)
```

### Features
- Connection pooling via `asyncpg.create_pool`
- JSONB serialization for flexible schema
- `ON CONFLICT DO UPDATE` for upsert semantics
- Auto-created `id`, `data`, `created_at`, `updated_at` columns
- Optional `tenant_column` for multi-tenant isolation

## Redis Cache

**File:** `src/eaip/infrastructure/redis_cache.py`
**Implements:** `CacheProvider`

```python
from eaip.infrastructure.redis_cache import RedisCacheProvider

cache = RedisCacheProvider(redis_url="redis://localhost:6379/0")
await cache.set("key", value, ttl=300)
value = await cache.get("key")
```

### Features
- Async Redis via `redis.asyncio`
- Connection pooling
- JSON serialization
- TTL-based expiration
- Key pattern invalidation
- Health check via `ping()`

## MinIO Object Storage

**File:** `src/eaip/infrastructure/object_storage.py`

```python
from eaip.infrastructure.object_storage import ObjectStorageProvider

storage = ObjectStorageProvider(
    endpoint="localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    bucket="eaip",
)
url = await storage.upload("doc.pdf", data)
data = await storage.download("doc.pdf")
presigned = await storage.presigned_url("doc.pdf", expires_seconds=3600)
```

### Features
- S3-compatible API via `minio` library
- Automatic bucket creation
- Upload, download, delete, exists
- Presigned URLs for temporary access

## File Secret Provider

**File:** `src/eaip/infrastructure/file_secret_provider.py`
**Implements:** `SecretProviderPort`

```python
from eaip.infrastructure.file_secret_provider import FileSecretProvider

provider = FileSecretProvider(path="/etc/eaip/secrets.json)
secret = provider.get("EAIP_AUTH_SECRET")
```

Supports both JSON and `.env` format files.

## OpenTelemetry Tracing

**File:** `src/eaip/infrastructure/otel_tracing.py`
**Implements:** `TracingProvider`

```python
from eaip.infrastructure.otel_tracing import OTelTracingProvider

tracer = OTelTracingProvider(
    service_name="eaip",
    otlp_endpoint="http://localhost:4318",
)
with tracer.span("process") as span:
    span.set_attribute("key", "value")
```

### Features
- OTLP HTTP exporter
- Batch span processing
- Resource attributes
- Context propagation
- Current span/trace ID access

## Prometheus Metrics

**File:** `src/eaip/infrastructure/prometheus_metrics.py`
**Implements:** `MetricsProvider`

```python
from eaip.infrastructure.prometheus_metrics import PrometheusMetricsProvider

metrics = PrometheusMetricsProvider(namespace="eaip")
counter = metrics.counter("requests_total", {"method": "GET"})
counter.inc()

# Expose for scraping
prometheus_latest = metrics.generate_latest()
```

### Features
- Standard Prometheus metric types (Counter, Gauge, Histogram)
- Label support
- Namespace prefixing
- Registry isolation
- Exposition format output

## Switching Adapters

Production adapters are injected via constructor parameters — no service
code changes required:

```python
# Development (default)
service = MyService()

# Production
service = MyService(
    cache=RedisCacheProvider(),
    metrics=PrometheusMetricsProvider(),
    tracer=OTelTracingProvider(),
)
```
