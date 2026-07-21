"""Tests for the connector management subsystem."""

from __future__ import annotations

import pytest

from eaip.connectors.events import (
    ConnectorActivated,
    ConnectorAuthRotated,
    ConnectorConfigUpdated,
    ConnectorDeactivated,
    ConnectorHealthCheckCompleted,
    ConnectorHealthStatusChanged,
    ConnectorMetricsCollected,
    ConnectorOperationExecuted,
    ConnectorOperationFailed,
    ConnectorRegistered,
    ConnectorSyncCompleted,
    ConnectorSyncFailed,
    ConnectorSyncStarted,
    ConnectorTested,
    ConnectorTestFailed,
    ConnectorTestPassed,
    ConnectorUnregistered,
    ConnectorUpdated,
)
from eaip.connectors.exceptions import (
    ConnectorAuthError,
    ConnectorConfigError,
    ConnectorConnectionError,
    ConnectorError,
    ConnectorHealthError,
    ConnectorNotFoundError,
    ConnectorOperationError,
    ConnectorRateLimitError,
    ConnectorSyncError,
)
from eaip.connectors.health import ConnectorHealthCheck
from eaip.connectors.integration import ConnectorRuntimeModule
from eaip.connectors.models import (
    AuthMethod,
    ConnectorAuthConfig,
    ConnectorConfig,
    ConnectorDefinition,
    ConnectorEndpoint,
    ConnectorMetadata,
    ConnectorOperation,
    ConnectorOperationType,
    ConnectorSchema,
    ConnectorStatus,
    ConnectorType,
)
from eaip.connectors.service import ConnectorService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def service() -> ConnectorService:
    return ConnectorService()


@pytest.fixture
def definition() -> ConnectorDefinition:
    return ConnectorDefinition(
        type=ConnectorType.REST,
        metadata=ConnectorMetadata(name="test-connector", description="A test connector"),
        auth_methods=[AuthMethod.API_KEY],
        operations=["send", "receive"],
    )


@pytest.fixture
def connector_config() -> ConnectorConfig:
    return ConnectorConfig(
        id="conn-1",
        connector_type=ConnectorType.REST,
        metadata=ConnectorMetadata(name="test-connector", description="A test connector"),
        auth=ConnectorAuthConfig(method=AuthMethod.API_KEY, credentials={"key": "test-key"}),
        endpoint=ConnectorEndpoint(url="http://example.com/api", method="POST"),
    )


@pytest.fixture
async def populated_service(
    service: ConnectorService,
    definition: ConnectorDefinition,
    connector_config: ConnectorConfig,
) -> ConnectorService:
    await service.register(definition, connector_config)
    return service


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestConnectorType:
    def test_members(self) -> None:
        assert ConnectorType.REST.value == "rest"
        assert ConnectorType.GRAPHQL.value == "graphql"
        assert ConnectorType.GRPC.value == "grpc"
        assert ConnectorType.SOAP.value == "soap"
        assert ConnectorType.EVENT.value == "event"
        assert ConnectorType.STREAM.value == "stream"
        assert ConnectorType.DATABASE.value == "database"
        assert ConnectorType.CUSTOM.value == "custom"


class TestConnectorStatus:
    def test_members(self) -> None:
        assert ConnectorStatus.ACTIVE.value == "active"
        assert ConnectorStatus.INACTIVE.value == "inactive"
        assert ConnectorStatus.ERROR.value == "error"
        assert ConnectorStatus.DEGRADED.value == "degraded"
        assert ConnectorStatus.CONNECTING.value == "connecting"
        assert ConnectorStatus.DISCONNECTED.value == "disconnected"


class TestAuthMethod:
    def test_members(self) -> None:
        assert AuthMethod.NONE.value == "none"
        assert AuthMethod.API_KEY.value == "api_key"
        assert AuthMethod.BASIC.value == "basic"
        assert AuthMethod.BEARER.value == "bearer"
        assert AuthMethod.OAUTH2.value == "oauth2"
        assert AuthMethod.CERTIFICATE.value == "certificate"
        assert AuthMethod.CUSTOM.value == "custom"


class TestConnectorOperationType:
    def test_members(self) -> None:
        assert ConnectorOperationType.READ.value == "read"
        assert ConnectorOperationType.WRITE.value == "write"
        assert ConnectorOperationType.DELETE.value == "delete"
        assert ConnectorOperationType.SUBSCRIBE.value == "subscribe"
        assert ConnectorOperationType.EXECUTE.value == "execute"


class TestConnectorConfig:
    def test_defaults(self) -> None:
        cfg = ConnectorConfig(
            id="c-1",
            connector_type=ConnectorType.REST,
            metadata=ConnectorMetadata(name="test"),
            auth=ConnectorAuthConfig(method=AuthMethod.NONE),
            endpoint=ConnectorEndpoint(url="http://example.com"),
        )
        assert cfg.enabled is True
        assert cfg.status == ConnectorStatus.INACTIVE
        assert cfg.rate_limit.max_requests_per_second == 10
        assert cfg.retry_policy.max_retries == 3

    def test_frozen(self) -> None:
        cfg = ConnectorConfig(
            id="c-1",
            connector_type=ConnectorType.REST,
            metadata=ConnectorMetadata(name="test"),
            auth=ConnectorAuthConfig(method=AuthMethod.NONE),
            endpoint=ConnectorEndpoint(url="http://example.com"),
        )
        with pytest.raises(AttributeError):
            cfg.id = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class TestConnectorRegisteredEvent:
    def test_event_type(self) -> None:
        event = ConnectorRegistered(connector_id="c-1", name="test", connector_type="rest")
        assert event.event_type == "eaip.connectors.connector.registered"

    def test_fields(self) -> None:
        event = ConnectorRegistered(connector_id="c-1", name="test", connector_type="rest")
        assert event.connector_id == "c-1"
        assert event.name == "test"
        assert event.connector_type == "rest"


class TestConnectorUpdatedEvent:
    def test_event_type(self) -> None:
        event = ConnectorUpdated(connector_id="c-1", name="test")
        assert event.event_type == "eaip.connectors.connector.updated"


class TestConnectorUnregisteredEvent:
    def test_event_type(self) -> None:
        event = ConnectorUnregistered(connector_id="c-1", name="test")
        assert event.event_type == "eaip.connectors.connector.unregistered"


class TestConnectorActivatedEvent:
    def test_event_type(self) -> None:
        event = ConnectorActivated(connector_id="c-1", name="test")
        assert event.event_type == "eaip.connectors.connector.activated"


class TestConnectorDeactivatedEvent:
    def test_event_type(self) -> None:
        event = ConnectorDeactivated(connector_id="c-1", name="test")
        assert event.event_type == "eaip.connectors.connector.deactivated"


class TestConnectorTestedEvent:
    def test_event_type(self) -> None:
        event = ConnectorTested(connector_id="c-1", name="test")
        assert event.event_type == "eaip.connectors.connector.tested"


class TestConnectorTestPassedEvent:
    def test_event_type(self) -> None:
        event = ConnectorTestPassed(connector_id="c-1", latency_ms=42.0)
        assert event.event_type == "eaip.connectors.connector.test_passed"


class TestConnectorTestFailedEvent:
    def test_event_type(self) -> None:
        event = ConnectorTestFailed(connector_id="c-1", error="timeout")
        assert event.event_type == "eaip.connectors.connector.test_failed"


class TestConnectorHealthCheckCompletedEvent:
    def test_event_type(self) -> None:
        event = ConnectorHealthCheckCompleted(connector_id="c-1", healthy=True, latency_ms=10.0)
        assert event.event_type == "eaip.connectors.connector.health_check_completed"


class TestConnectorConfigUpdatedEvent:
    def test_event_type(self) -> None:
        event = ConnectorConfigUpdated(connector_id="c-1", changes={"timeout": 60})
        assert event.event_type == "eaip.connectors.connector.config_updated"


class TestConnectorAuthRotatedEvent:
    def test_event_type(self) -> None:
        event = ConnectorAuthRotated(connector_id="c-1", method="api_key")
        assert event.event_type == "eaip.connectors.connector.auth_rotated"


class TestConnectorSyncStartedEvent:
    def test_event_type(self) -> None:
        event = ConnectorSyncStarted(connector_id="c-1")
        assert event.event_type == "eaip.connectors.connector.sync_started"


class TestConnectorSyncCompletedEvent:
    def test_event_type(self) -> None:
        event = ConnectorSyncCompleted(connector_id="c-1", records_synced=100)
        assert event.event_type == "eaip.connectors.connector.sync_completed"


class TestConnectorSyncFailedEvent:
    def test_event_type(self) -> None:
        event = ConnectorSyncFailed(connector_id="c-1", error="timeout")
        assert event.event_type == "eaip.connectors.connector.sync_failed"


class TestConnectorOperationExecutedEvent:
    def test_event_type(self) -> None:
        event = ConnectorOperationExecuted(
            connector_id="c-1", operation_id="op-1", operation_name="send", duration_ms=50.0
        )
        assert event.event_type == "eaip.connectors.connector.operation_executed"


class TestConnectorOperationFailedEvent:
    def test_event_type(self) -> None:
        event = ConnectorOperationFailed(
            connector_id="c-1", operation_id="op-1", operation_name="send", error="timeout"
        )
        assert event.event_type == "eaip.connectors.connector.operation_failed"


class TestConnectorHealthStatusChangedEvent:
    def test_event_type(self) -> None:
        event = ConnectorHealthStatusChanged(
            connector_id="c-1", previous_status="active", new_status="error"
        )
        assert event.event_type == "eaip.connectors.connector.health_status_changed"


class TestConnectorMetricsCollectedEvent:
    def test_event_type(self) -> None:
        event = ConnectorMetricsCollected(
            connector_id="c-1", requests_total=100, requests_failed=5, total_latency_ms=500.0
        )
        assert event.event_type == "eaip.connectors.connector.metrics_collected"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TestConnectorError:
    def test_base_exception(self) -> None:
        err = ConnectorError("something went wrong")
        assert isinstance(err, Exception)
        assert str(err) == "something went wrong"

    def test_code_default(self) -> None:
        err = ConnectorError("test")
        assert str(err.code) == "EAIP-0017"


class TestConnectorNotFoundError:
    def test_code(self) -> None:
        err = ConnectorNotFoundError("not found", context={"connector_id": "c-1"})
        assert str(err.code) == "EAIP-0003"


class TestConnectorConfigError:
    def test_code(self) -> None:
        err = ConnectorConfigError("invalid config")
        assert str(err.code) == "EAIP-0001"


class TestConnectorAuthError:
    def test_code(self) -> None:
        err = ConnectorAuthError("auth failed")
        assert str(err.code) == "EAIP-0020"


class TestConnectorConnectionError:
    def test_code(self) -> None:
        err = ConnectorConnectionError("connection failed")
        assert str(err.code) == "EAIP-0013"


class TestConnectorOperationError:
    def test_code(self) -> None:
        err = ConnectorOperationError("operation failed")
        assert str(err.code) == "EAIP-0018"


class TestConnectorSyncError:
    def test_code(self) -> None:
        err = ConnectorSyncError("sync failed")
        assert str(err.code) == "EAIP-0018"


class TestConnectorHealthError:
    def test_code(self) -> None:
        err = ConnectorHealthError("health check failed")
        assert str(err.code) == "EAIP-0013"


class TestConnectorRateLimitError:
    def test_code(self) -> None:
        err = ConnectorRateLimitError("rate limited")
        assert str(err.code) == "EAIP-0021"


# ---------------------------------------------------------------------------
# Service — Registration
# ---------------------------------------------------------------------------


class TestConnectorServiceRegister:
    async def test_register_connector(
        self,
        service: ConnectorService,
        definition: ConnectorDefinition,
        connector_config: ConnectorConfig,
    ) -> None:
        entry = await service.register(definition, connector_config)
        assert entry.connector_id == "conn-1"
        assert entry.definition.type == ConnectorType.REST
        assert entry.config.id == "conn-1"

    async def test_register_duplicate_raises(
        self,
        service: ConnectorService,
        definition: ConnectorDefinition,
        connector_config: ConnectorConfig,
    ) -> None:
        await service.register(definition, connector_config)
        with pytest.raises(ConnectorConfigError):
            await service.register(definition, connector_config)


class TestConnectorServiceGet:
    async def test_get_registered_connector(
        self,
        populated_service: ConnectorService,
    ) -> None:
        entry = await populated_service.get("conn-1")
        assert entry.connector_id == "conn-1"

    async def test_get_not_found_raises(
        self,
        service: ConnectorService,
    ) -> None:
        with pytest.raises(ConnectorNotFoundError):
            await service.get("nonexistent")


class TestConnectorServiceList:
    async def test_list_empty(self, service: ConnectorService) -> None:
        entries = await service.list()
        assert entries == []

    async def test_list_populated(
        self,
        populated_service: ConnectorService,
    ) -> None:
        entries = await populated_service.list()
        assert len(entries) == 1


class TestConnectorServiceUnregister:
    async def test_unregister_removes_connector(
        self,
        populated_service: ConnectorService,
    ) -> None:
        await populated_service.unregister("conn-1")
        entries = await populated_service.list()
        assert entries == []

    async def test_unregister_not_found_raises(
        self,
        service: ConnectorService,
    ) -> None:
        with pytest.raises(ConnectorNotFoundError):
            await service.unregister("nonexistent")


# ---------------------------------------------------------------------------
# Service — Connection lifecycle
# ---------------------------------------------------------------------------


class TestConnectorServiceActivate:
    async def test_activate(
        self,
        populated_service: ConnectorService,
    ) -> None:
        entry = await populated_service.activate("conn-1")
        assert entry.config.status == ConnectorStatus.ACTIVE
        assert entry.config.enabled is True


class TestConnectorServiceDeactivate:
    async def test_deactivate(
        self,
        populated_service: ConnectorService,
    ) -> None:
        entry = await populated_service.deactivate("conn-1")
        assert entry.config.status == ConnectorStatus.INACTIVE
        assert entry.config.enabled is False


class TestConnectorServiceTestConnection:
    async def test_test_connection_pass(
        self,
        populated_service: ConnectorService,
    ) -> None:
        result = await populated_service.test_connection("conn-1")
        assert result is True

    async def test_test_connection_not_found(
        self,
        service: ConnectorService,
    ) -> None:
        with pytest.raises(ConnectorNotFoundError):
            await service.test_connection("nonexistent")


# ---------------------------------------------------------------------------
# Service — Health
# ---------------------------------------------------------------------------


class TestConnectorServiceCheckHealth:
    async def test_check_health(
        self,
        populated_service: ConnectorService,
    ) -> None:
        health = await populated_service.check_health("conn-1")
        assert health.connector_id == "conn-1"
        assert health.healthy is True
        assert health.latency_ms is not None

    async def test_check_health_not_found(
        self,
        service: ConnectorService,
    ) -> None:
        with pytest.raises(ConnectorNotFoundError):
            await service.check_health("nonexistent")


# ---------------------------------------------------------------------------
# Service — Sync
# ---------------------------------------------------------------------------


class TestConnectorServiceSync:
    async def test_sync(
        self,
        populated_service: ConnectorService,
    ) -> None:
        result = await populated_service.sync("conn-1")
        assert result.connector_id == "conn-1"
        assert result.success is True
        assert result.records_synced > 0

    async def test_sync_not_found(
        self,
        service: ConnectorService,
    ) -> None:
        with pytest.raises(ConnectorNotFoundError):
            await service.sync("nonexistent")


# ---------------------------------------------------------------------------
# Service — Operations
# ---------------------------------------------------------------------------


class TestConnectorServiceExecuteOperation:
    async def test_execute_operation(
        self,
        populated_service: ConnectorService,
    ) -> None:
        op = ConnectorOperation(
            operation_id="op-1",
            connector_id="conn-1",
            operation_type=ConnectorOperationType.EXECUTE,
            name="send",
        )
        result = await populated_service.execute_operation("conn-1", op)
        assert result["status"] == "ok"

    async def test_execute_operation_not_found(
        self,
        service: ConnectorService,
    ) -> None:
        op = ConnectorOperation(
            operation_id="op-1",
            connector_id="nonexistent",
            operation_type=ConnectorOperationType.READ,
            name="fetch",
        )
        with pytest.raises(ConnectorNotFoundError):
            await service.execute_operation("nonexistent", op)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


class TestConnectorHealthCheck:
    async def test_healthy_when_connectors_present(self) -> None:
        check = ConnectorHealthCheck(connector_count=3)
        report = await check.check()
        assert report.status.value == "healthy"
        assert report.details["connector_count"] == 3

    async def test_degraded_when_no_connectors(self) -> None:
        check = ConnectorHealthCheck(connector_count=0)
        report = await check.check()
        assert report.status.value == "degraded"


# ---------------------------------------------------------------------------
# Integration module
# ---------------------------------------------------------------------------


class TestConnectorRuntimeModule:
    async def test_name(self) -> None:
        mod = ConnectorRuntimeModule()
        assert mod.name == "connectors"

    async def test_service_property(self) -> None:
        svc = ConnectorService()
        mod = ConnectorRuntimeModule(service=svc)
        assert mod.service is svc


# ---------------------------------------------------------------------------
# ConnectorConfig model
# ---------------------------------------------------------------------------


class TestConnectorConfigModel:
    def test_schema_alias(self) -> None:
        cfg = ConnectorConfig(
            id="c-2",
            connector_type=ConnectorType.GRAPHQL,
            metadata=ConnectorMetadata(name="graphql-test"),
            auth=ConnectorAuthConfig(method=AuthMethod.BEARER, credentials={"token": "abc"}),
            endpoint=ConnectorEndpoint(url="http://graphql.example.com", method="POST"),
            schema=ConnectorSchema(
                input_schema={"type": "object"}, output_schema={"type": "object"}
            ),
        )
        assert cfg.schema_.input_schema == {"type": "object"}
        assert cfg.schema_.output_schema == {"type": "object"}
