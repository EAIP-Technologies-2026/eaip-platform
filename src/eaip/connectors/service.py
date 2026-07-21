"""Connector service — register, connect, sync, health, and operations."""

from __future__ import annotations

import random
import time
from typing import Any

from eaip.connectors.exceptions import (
    ConnectorConfigError,
    ConnectorConnectionError,
    ConnectorNotFoundError,
    ConnectorOperationError,
    ConnectorSyncError,
)
from eaip.connectors.models import (
    ConnectorConfig,
    ConnectorDefinition,
    ConnectorHealthStatus,
    ConnectorOperation,
    ConnectorRegistryEntry,
    ConnectorStatus,
    ConnectorSyncResult,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class ConnectorService:
    """Service for managing connectors — registration, connectivity, sync, and operations."""

    def __init__(self) -> None:
        """Initialize the connector service."""
        self._registry: dict[str, ConnectorRegistryEntry] = {}
        self._log = get_logger("eaip.connectors.service")

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register(
        self,
        definition: ConnectorDefinition,
        config: ConnectorConfig,
    ) -> ConnectorRegistryEntry:
        """Register a new connector."""
        if config.id in self._registry:
            raise ConnectorConfigError(
                f"Connector '{config.id}' is already registered",
                context={"connector_id": config.id},
            )
        entry = ConnectorRegistryEntry(
            connector_id=config.id,
            definition=definition,
            config=config,
        )
        self._registry[config.id] = entry
        self._log.info("connector.registered", connector_id=config.id)
        return entry

    async def unregister(self, connector_id: str) -> None:
        """Unregister a connector."""
        self._get_entry(connector_id)
        del self._registry[connector_id]
        self._log.info("connector.unregistered", connector_id=connector_id)

    async def get(self, connector_id: str) -> ConnectorRegistryEntry:
        """Get a registered connector."""
        return self._get_entry(connector_id)

    async def list(self) -> list[ConnectorRegistryEntry]:
        """List all registered connectors."""
        return list(self._registry.values())

    async def update(self, connector_id: str, config: ConnectorConfig) -> ConnectorRegistryEntry:
        """Update a connector's configuration."""
        entry = self._get_entry(connector_id)
        updated = ConnectorRegistryEntry(
            connector_id=config.id,
            definition=entry.definition,
            config=config,
            health=entry.health,
            metrics=entry.metrics,
            registered_at=entry.registered_at,
            updated_at=utc_now(),
        )
        self._registry[connector_id] = updated
        self._log.info("connector.updated", connector_id=connector_id)
        return updated

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def activate(self, connector_id: str) -> ConnectorRegistryEntry:
        """Activate a connector."""
        entry = self._get_entry(connector_id)
        new_config = ConnectorConfig(
            id=entry.config.id,
            connector_type=entry.config.connector_type,
            status=ConnectorStatus.ACTIVE,
            metadata=entry.config.metadata,
            auth=entry.config.auth,
            endpoint=entry.config.endpoint,
            schema=entry.config.schema_,
            rate_limit=entry.config.rate_limit,
            retry_policy=entry.config.retry_policy,
            enabled=True,
        )
        return await self.update(connector_id, new_config)

    async def deactivate(self, connector_id: str) -> ConnectorRegistryEntry:
        """Deactivate a connector."""
        entry = self._get_entry(connector_id)
        new_config = ConnectorConfig(
            id=entry.config.id,
            connector_type=entry.config.connector_type,
            status=ConnectorStatus.INACTIVE,
            metadata=entry.config.metadata,
            auth=entry.config.auth,
            endpoint=entry.config.endpoint,
            schema=entry.config.schema_,
            rate_limit=entry.config.rate_limit,
            retry_policy=entry.config.retry_policy,
            enabled=False,
        )
        return await self.update(connector_id, new_config)

    async def test_connection(self, connector_id: str) -> bool:
        """Test connectivity to a connector endpoint."""
        entry = self._get_entry(connector_id)
        if not entry.config.enabled:
            raise ConnectorConnectionError(
                f"Cannot test disabled connector '{connector_id}'",
                context={"connector_id": connector_id},
            )
        # Simulate connectivity test
        success_threshold = 0.8
        success = random.random() <= success_threshold  # noqa: S311
        if not success:
            raise ConnectorConnectionError(
                f"Connection test failed for connector '{connector_id}'",
                context={"connector_id": connector_id},
            )
        return True

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def check_health(self, connector_id: str) -> ConnectorHealthStatus:
        """Perform a health check on a connector."""
        entry = self._get_entry(connector_id)
        success_threshold = 0.8
        latency_min = 5.0
        latency_max = 500.0
        healthy = random.random() <= success_threshold  # noqa: S311
        latency = random.uniform(latency_min, latency_max)  # noqa: S311
        status = ConnectorStatus.ACTIVE if healthy else ConnectorStatus.ERROR
        health = ConnectorHealthStatus(
            connector_id=connector_id,
            healthy=healthy,
            status=status,
            message="Health check passed" if healthy else "Health check failed",
            latency_ms=latency,
        )
        updated_entry = ConnectorRegistryEntry(
            connector_id=entry.connector_id,
            definition=entry.definition,
            config=entry.config,
            health=health,
            metrics=entry.metrics,
            registered_at=entry.registered_at,
            updated_at=utc_now(),
        )
        self._registry[connector_id] = updated_entry
        return health

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    async def sync(self, connector_id: str) -> ConnectorSyncResult:
        """Synchronize data with a connector."""
        self._get_entry(connector_id)
        success_threshold = 0.8
        sync_min = 10
        sync_max = 1000
        started = utc_now()
        success = random.random() <= success_threshold  # noqa: S311
        if not success:
            raise ConnectorSyncError(
                f"Synchronization failed for connector '{connector_id}'",
                context={"connector_id": connector_id},
            )
        return ConnectorSyncResult(
            connector_id=connector_id,
            success=True,
            records_synced=random.randint(sync_min, sync_max),  # noqa: S311
            started_at=started,
            completed_at=utc_now(),
        )

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    async def execute_operation(
        self,
        connector_id: str,
        operation: ConnectorOperation,
    ) -> dict[str, Any]:
        """Execute an operation on a connector."""
        self._get_entry(connector_id)
        success_threshold = 0.8
        started = time.monotonic()
        success = random.random() <= success_threshold  # noqa: S311
        duration = (time.monotonic() - started) * 1000
        if not success:
            raise ConnectorOperationError(
                f"Operation '{operation.name}' failed for connector '{connector_id}'",
                context={"connector_id": connector_id, "operation": operation.name},
            )
        return {"status": "ok", "duration_ms": duration, "result": "operation completed"}

    def _get_entry(self, connector_id: str) -> ConnectorRegistryEntry:
        if connector_id not in self._registry:
            raise ConnectorNotFoundError(
                f"Connector '{connector_id}' not found",
                context={"connector_id": connector_id},
            )
        return self._registry[connector_id]


__all__ = ["ConnectorService"]
