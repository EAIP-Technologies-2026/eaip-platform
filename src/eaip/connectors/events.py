"""Domain events for the connector management subsystem."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class ConnectorRegistered(DomainEvent):
    """Emitted when a new connector is registered."""

    event_type: ClassVar[str] = "eaip.connectors.connector.registered"

    connector_id: str
    name: str
    connector_type: str


class ConnectorUpdated(DomainEvent):
    """Emitted when a connector is updated."""

    event_type: ClassVar[str] = "eaip.connectors.connector.updated"

    connector_id: str
    name: str


class ConnectorUnregistered(DomainEvent):
    """Emitted when a connector is unregistered."""

    event_type: ClassVar[str] = "eaip.connectors.connector.unregistered"

    connector_id: str
    name: str


class ConnectorActivated(DomainEvent):
    """Emitted when a connector is activated."""

    event_type: ClassVar[str] = "eaip.connectors.connector.activated"

    connector_id: str
    name: str


class ConnectorDeactivated(DomainEvent):
    """Emitted when a connector is deactivated."""

    event_type: ClassVar[str] = "eaip.connectors.connector.deactivated"

    connector_id: str
    name: str


class ConnectorTested(DomainEvent):
    """Emitted when a connector connectivity test is initiated."""

    event_type: ClassVar[str] = "eaip.connectors.connector.tested"

    connector_id: str
    name: str


class ConnectorTestPassed(DomainEvent):
    """Emitted when a connector connectivity test succeeds."""

    event_type: ClassVar[str] = "eaip.connectors.connector.test_passed"

    connector_id: str
    latency_ms: float


class ConnectorTestFailed(DomainEvent):
    """Emitted when a connector connectivity test fails."""

    event_type: ClassVar[str] = "eaip.connectors.connector.test_failed"

    connector_id: str
    error: str


class ConnectorHealthCheckCompleted(DomainEvent):
    """Emitted when a health check completes for a connector."""

    event_type: ClassVar[str] = "eaip.connectors.connector.health_check_completed"

    connector_id: str
    healthy: bool
    latency_ms: float | None


class ConnectorHealthStatusChanged(DomainEvent):
    """Emitted when a connector's health status changes."""

    event_type: ClassVar[str] = "eaip.connectors.connector.health_status_changed"

    connector_id: str
    previous_status: str
    new_status: str


class ConnectorMetricsCollected(DomainEvent):
    """Emitted when metrics are collected from a connector."""

    event_type: ClassVar[str] = "eaip.connectors.connector.metrics_collected"

    connector_id: str
    requests_total: int
    requests_failed: int
    total_latency_ms: float


class ConnectorSyncStarted(DomainEvent):
    """Emitted when a connector synchronization starts."""

    event_type: ClassVar[str] = "eaip.connectors.connector.sync_started"

    connector_id: str


class ConnectorSyncCompleted(DomainEvent):
    """Emitted when a connector synchronization completes successfully."""

    event_type: ClassVar[str] = "eaip.connectors.connector.sync_completed"

    connector_id: str
    records_synced: int


class ConnectorSyncFailed(DomainEvent):
    """Emitted when a connector synchronization fails."""

    event_type: ClassVar[str] = "eaip.connectors.connector.sync_failed"

    connector_id: str
    error: str


class ConnectorConfigUpdated(DomainEvent):
    """Emitted when a connector's configuration is updated."""

    event_type: ClassVar[str] = "eaip.connectors.connector.config_updated"

    connector_id: str
    changes: dict[str, Any]


class ConnectorAuthRotated(DomainEvent):
    """Emitted when a connector's authentication credentials are rotated."""

    event_type: ClassVar[str] = "eaip.connectors.connector.auth_rotated"

    connector_id: str
    method: str


class ConnectorOperationExecuted(DomainEvent):
    """Emitted when a connector operation is executed successfully."""

    event_type: ClassVar[str] = "eaip.connectors.connector.operation_executed"

    connector_id: str
    operation_id: str
    operation_name: str
    duration_ms: float


class ConnectorOperationFailed(DomainEvent):
    """Emitted when a connector operation fails."""

    event_type: ClassVar[str] = "eaip.connectors.connector.operation_failed"

    connector_id: str
    operation_id: str
    operation_name: str
    error: str


__all__ = [
    "ConnectorActivated",
    "ConnectorAuthRotated",
    "ConnectorConfigUpdated",
    "ConnectorDeactivated",
    "ConnectorHealthCheckCompleted",
    "ConnectorHealthStatusChanged",
    "ConnectorMetricsCollected",
    "ConnectorOperationExecuted",
    "ConnectorOperationFailed",
    "ConnectorRegistered",
    "ConnectorSyncCompleted",
    "ConnectorSyncFailed",
    "ConnectorSyncStarted",
    "ConnectorTestFailed",
    "ConnectorTestPassed",
    "ConnectorTested",
    "ConnectorUnregistered",
    "ConnectorUpdated",
]
