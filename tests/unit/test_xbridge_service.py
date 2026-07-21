"""Tests for :mod:`eaip.xbridge.bridge`."""

from __future__ import annotations

import pytest

from eaip.xbridge.bridge import ConnectorBridge
from eaip.xbridge.exceptions import (
    BridgeError,
    ConnectorNotFoundError,
    MessageRoutingError,
)
from eaip.xbridge.models import (
    BridgeConfig,
    BridgeRoute,
    ConnectorConfig,
    MessageEnvelope,
    ProtocolType,
)


class TestConnectorBridge:
    @pytest.fixture
    def bridge(self) -> ConnectorBridge:
        return ConnectorBridge()

    @pytest.fixture
    def rest_connector(self) -> ConnectorConfig:
        return ConnectorConfig(
            id="conn1",
            name="REST API",
            protocol=ProtocolType.REST,
            endpoint="https://api.example.com",
        )

    @pytest.fixture
    def grpc_connector(self) -> ConnectorConfig:
        return ConnectorConfig(
            id="conn2",
            name="gRPC Service",
            protocol=ProtocolType.GRPC,
            endpoint="grpc://svc.example.com:50051",
        )

    class TestRegisterConnector:
        async def test_register(
            self, bridge: ConnectorBridge, rest_connector: ConnectorConfig
        ) -> None:
            result = await bridge.register_connector(rest_connector)
            assert result.id == "conn1"

        async def test_list(self, bridge: ConnectorBridge, rest_connector: ConnectorConfig) -> None:
            await bridge.register_connector(rest_connector)
            connectors = await bridge.list_connectors()
            assert len(connectors) == 1

    class TestGetConnector:
        async def test_get(self, bridge: ConnectorBridge, rest_connector: ConnectorConfig) -> None:
            await bridge.register_connector(rest_connector)
            c = await bridge.get_connector("conn1")
            assert c.name == "REST API"

        async def test_not_found(self, bridge: ConnectorBridge) -> None:
            with pytest.raises(ConnectorNotFoundError):
                await bridge.get_connector("nonexistent")

    class TestUpdateConnector:
        async def test_update(
            self, bridge: ConnectorBridge, rest_connector: ConnectorConfig
        ) -> None:
            await bridge.register_connector(rest_connector)
            updated = await bridge.update_connector("conn1", {"name": "Updated API"})
            assert updated.name == "Updated API"

    class TestDeleteConnector:
        async def test_delete(
            self, bridge: ConnectorBridge, rest_connector: ConnectorConfig
        ) -> None:
            await bridge.register_connector(rest_connector)
            await bridge.delete_connector("conn1")
            connectors = await bridge.list_connectors()
            assert len(connectors) == 0

    class TestSendMessage:
        async def test_send(
            self,
            bridge: ConnectorBridge,
            rest_connector: ConnectorConfig,
            grpc_connector: ConnectorConfig,
        ) -> None:
            await bridge.register_connector(rest_connector)
            await bridge.register_connector(grpc_connector)
            envelope = MessageEnvelope(
                id="msg1", source="conn1", target="conn2", payload={"key": "value"}
            )
            result = await bridge.send_message(envelope)
            assert result.id == "msg1"

        async def test_send_missing_source(self, bridge: ConnectorBridge) -> None:
            envelope = MessageEnvelope(id="msg1", source="missing", target="conn2", payload={})
            with pytest.raises(ConnectorNotFoundError):
                await bridge.send_message(envelope)

    class TestRouteMessage:
        async def test_route(
            self,
            bridge: ConnectorBridge,
            rest_connector: ConnectorConfig,
            grpc_connector: ConnectorConfig,
        ) -> None:
            await bridge.register_connector(rest_connector)
            await bridge.register_connector(grpc_connector)
            route = BridgeRoute(id="r1", source="conn1", target="conn2")
            await bridge.register_route(route)
            envelope = MessageEnvelope(
                id="msg1", source="conn1", target="conn2", payload={"data": 1}
            )
            result = await bridge.route_message(envelope)
            assert result.id == "msg1"

        async def test_route_no_route(self, bridge: ConnectorBridge) -> None:
            envelope = MessageEnvelope(id="msg1", source="conn1", target="conn2", payload={})
            with pytest.raises(MessageRoutingError):
                await bridge.route_message(envelope)

    class TestMessageLog:
        async def test_get_message_log(
            self,
            bridge: ConnectorBridge,
            rest_connector: ConnectorConfig,
            grpc_connector: ConnectorConfig,
        ) -> None:
            await bridge.register_connector(rest_connector)
            await bridge.register_connector(grpc_connector)
            envelope = MessageEnvelope(id="msg1", source="conn1", target="conn2", payload={})
            await bridge.send_message(envelope)
            log = await bridge.get_message_log()
            assert len(log) == 1

    class TestConfig:
        def test_default_config(self) -> None:
            b = ConnectorBridge()
            assert b.config.max_message_size_bytes == 10 * 1024 * 1024
            assert b.config.default_timeout_seconds == 30

        def test_custom_config(self) -> None:
            config = BridgeConfig(enable_message_logging=False, default_timeout_seconds=60)
            b = ConnectorBridge(config=config)
            assert b.config.enable_message_logging is False
            assert b.config.default_timeout_seconds == 60
