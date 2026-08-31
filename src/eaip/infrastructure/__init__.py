"""Default, dependency-free adapters for the Foundation's own ports.

These are the implementations the platform wires by default. Hosts may swap
any of them for environment-specific alternatives via the DI container.
"""

from __future__ import annotations

from eaip.infrastructure.cache import InMemoryCacheProvider
from eaip.infrastructure.clock import SystemClock
from eaip.infrastructure.file_secret_provider import FileSecretProvider
from eaip.infrastructure.health import InfrastructureHealthService
from eaip.infrastructure.id_generator import UuidIdGenerator
from eaip.infrastructure.logger import InMemoryLogger
from eaip.infrastructure.metrics import InMemoryMetricsProvider
from eaip.infrastructure.object_storage import ObjectStorageProvider
from eaip.infrastructure.otel_tracing import OTelTracingProvider
from eaip.infrastructure.postgres_repository import PostgresRepository
from eaip.infrastructure.prometheus_metrics import PrometheusMetricsProvider
from eaip.infrastructure.redis_cache import RedisCacheProvider
from eaip.infrastructure.secret_provider import EnvSecretProvider
from eaip.infrastructure.tracing import NoOpTracingProvider

__all__ = [
    "EnvSecretProvider",
    "FileSecretProvider",
    "InMemoryCacheProvider",
    "InMemoryLogger",
    "InMemoryMetricsProvider",
    "InfrastructureHealthService",
    "NoOpTracingProvider",
    "OTelTracingProvider",
    "ObjectStorageProvider",
    "PostgresRepository",
    "PrometheusMetricsProvider",
    "RedisCacheProvider",
    "SystemClock",
    "UuidIdGenerator",
]
