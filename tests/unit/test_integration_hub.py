"""Tests for IntegrationHub."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from eaip.integration.exceptions import (
    ConnectorNotFoundError,
    MessageDeliveryError,
)
from eaip.integration.hub import IntegrationHub
from eaip.integration.models import (
    ConnectorDefinition,
    IntegrationMessage,
    MessageRoute,
    Transformation,
)


class TestIntegrationHubConnectors:
    def test_register_connector(self) -> None:
        hub = IntegrationHub()
        c = ConnectorDefinition(
            id="c1", name="HTTP Out", type="http", endpoint_url="https://ex.com"
        )
        hub.register_connector(c)
        assert hub.get_connector("c1").id == "c1"

    def test_unregister_connector(self) -> None:
        hub = IntegrationHub()
        c = ConnectorDefinition(id="c1", name="C1", type="http", endpoint_url="https://ex.com")
        hub.register_connector(c)
        removed = hub.unregister_connector("c1")
        assert removed is not None
        assert removed.id == "c1"
        with pytest.raises(ConnectorNotFoundError):
            hub.get_connector("c1")

    def test_unregister_missing(self) -> None:
        hub = IntegrationHub()
        assert hub.unregister_connector("nonexistent") is None

    def test_get_connector_missing(self) -> None:
        hub = IntegrationHub()
        with pytest.raises(ConnectorNotFoundError):
            hub.get_connector("nonexistent")

    def test_get_connector_not_found_context(self) -> None:
        hub = IntegrationHub()
        try:
            hub.get_connector("missing")
        except ConnectorNotFoundError as e:
            assert e.context.get("connector_id") == "missing"

    def test_list_connectors_all(self) -> None:
        hub = IntegrationHub()
        hub.register_connector(
            ConnectorDefinition(id="c1", name="C1", type="http", endpoint_url="https://ex.com")
        )
        hub.register_connector(
            ConnectorDefinition(id="c2", name="C2", type="mq", endpoint_url="amqp://ex.com")
        )
        assert len(hub.list_connectors()) == 2

    def test_list_connectors_filtered(self) -> None:
        hub = IntegrationHub()
        hub.register_connector(
            ConnectorDefinition(id="c1", name="C1", type="http", endpoint_url="https://ex.com")
        )
        hub.register_connector(
            ConnectorDefinition(id="c2", name="C2", type="mq", endpoint_url="amqp://ex.com")
        )
        http_list = hub.list_connectors(type="http")
        assert len(http_list) == 1
        assert http_list[0].id == "c1"

    def test_list_connectors_empty(self) -> None:
        hub = IntegrationHub()
        assert hub.list_connectors() == []

    def test_duplicate_register_overwrites(self) -> None:
        hub = IntegrationHub()
        c1 = ConnectorDefinition(id="c1", name="C1", type="http", endpoint_url="https://ex.com")
        c2 = ConnectorDefinition(id="c1", name="C2", type="http", endpoint_url="https://ex2.com")
        hub.register_connector(c1)
        hub.register_connector(c2)
        assert hub.get_connector("c1").name == "C2"


class TestIntegrationHubRoutes:
    def test_register_route(self) -> None:
        hub = IntegrationHub()
        r = MessageRoute(
            id="r1", name="R1", source_pattern="orders.*", destination_pattern="warehouse"
        )
        hub.register_route(r)
        assert len(hub.list_routes()) == 1

    def test_unregister_route(self) -> None:
        hub = IntegrationHub()
        r = MessageRoute(id="r1", name="R1", source_pattern="a", destination_pattern="b")
        hub.register_route(r)
        assert hub.unregister_route("r1") is not None
        assert len(hub.list_routes()) == 0

    def test_unregister_missing_route(self) -> None:
        hub = IntegrationHub()
        assert hub.unregister_route("nonexistent") is None

    def test_list_routes_empty(self) -> None:
        hub = IntegrationHub()
        assert hub.list_routes() == []


class TestIntegrationHubTransformations:
    def test_register_transformation(self) -> None:
        hub = IntegrationHub()
        t = Transformation(id="t1", name="T1", type="mapping")
        hub.register_transformation(t)
        assert len(hub._transformations) == 1


class TestIntegrationHubMessageFlow:
    @pytest.fixture
    def hub_with_routes(self) -> IntegrationHub:
        hub = IntegrationHub()
        hub.register_connector(
            ConnectorDefinition(
                id="dest-sys", name="Dest", type="http", endpoint_url="https://dest.com"
            )
        )
        hub.register_route(
            MessageRoute(
                id="r1", name="R1", source_pattern="orders.*", destination_pattern="dest-sys"
            )
        )
        return hub

    @pytest.mark.asyncio
    async def test_send_message(self) -> None:
        hub = IntegrationHub()
        m = IntegrationMessage(id="m1", source="sys-a", destination="sys-b")
        await hub.send_message(m)

    @pytest.mark.asyncio
    async def test_receive_message_no_routes(self) -> None:
        hub = IntegrationHub()
        m = IntegrationMessage(id="m1", source="sys-a", destination="sys-b")
        await hub.receive_message(m)

    @pytest.mark.asyncio
    async def test_receive_message_routes(self, hub_with_routes: IntegrationHub) -> None:
        hub = hub_with_routes
        m = IntegrationMessage(id="m1", source="orders.new", destination="dest-sys")
        await hub.receive_message(m)

    @pytest.mark.asyncio
    async def test_route_message_match(self, hub_with_routes: IntegrationHub) -> None:
        hub = hub_with_routes
        m = IntegrationMessage(id="m1", source="orders.new", destination="dest-sys")
        await hub.route_message(m)

    @pytest.mark.asyncio
    async def test_route_message_no_match(self) -> None:
        hub = IntegrationHub()
        m = IntegrationMessage(id="m1", source="unknown", destination="nowhere")
        await hub.route_message(m)

    @pytest.mark.asyncio
    async def test_route_message_retry_error_handling(self) -> None:
        hub = IntegrationHub()
        hub.register_route(
            MessageRoute(
                id="r1",
                name="R1",
                source_pattern="*",
                destination_pattern="nonexistent",
                error_handling="retry",
            )
        )
        m = IntegrationMessage(id="m1", source="test", destination="nowhere")
        await hub.route_message(m)

    @pytest.mark.asyncio
    async def test_route_message_dead_letter(self) -> None:
        hub = IntegrationHub()
        hub.register_route(
            MessageRoute(
                id="r1",
                name="R1",
                source_pattern="*",
                destination_pattern="nonexistent",
                error_handling="dead_letter",
            )
        )
        m = IntegrationMessage(id="m1", source="test", destination="nowhere")
        await hub.route_message(m)

    @pytest.mark.asyncio
    async def test_event_bus_integration(self) -> None:
        mock_bus = AsyncMock()
        hub = IntegrationHub(event_bus=mock_bus)
        hub.register_connector(
            ConnectorDefinition(id="c1", name="C1", type="http", endpoint_url="https://ex.com")
        )
        hub.register_route(
            MessageRoute(id="r1", name="R1", source_pattern="*", destination_pattern="c1")
        )
        m = IntegrationMessage(id="m1", source="test", destination="c1")
        await hub.receive_message(m)
        mock_bus.publish.assert_called()


class TestMatchPattern:
    def test_exact_match(self) -> None:
        assert IntegrationHub._match_pattern("orders.new", "orders.new") is True

    def test_wildcard_match(self) -> None:
        assert IntegrationHub._match_pattern("orders.new", "*") is True

    def test_prefix_match(self) -> None:
        assert IntegrationHub._match_pattern("orders.new", "orders.*") is True

    def test_suffix_match(self) -> None:
        assert IntegrationHub._match_pattern("event.orders", "*.orders") is True

    def test_no_match(self) -> None:
        assert IntegrationHub._match_pattern("inventory", "orders.*") is False

    def test_empty_source(self) -> None:
        assert IntegrationHub._match_pattern("", "orders.*") is False


class TestDeliverToConnector:
    @pytest.mark.asyncio
    async def test_deliver_disabled_connector(self) -> None:
        hub = IntegrationHub()
        hub.register_connector(
            ConnectorDefinition(
                id="c1", name="C1", type="http", endpoint_url="https://ex.com", enabled=False
            )
        )
        m = IntegrationMessage(id="m1", source="a", destination="b")
        with pytest.raises(MessageDeliveryError):
            await hub._deliver_to_connector(m, "c1")

    @pytest.mark.asyncio
    async def test_deliver_missing_connector(self) -> None:
        hub = IntegrationHub()
        m = IntegrationMessage(id="m1", source="a", destination="b")
        with pytest.raises(ConnectorNotFoundError):
            await hub._deliver_to_connector(m, "nonexistent")

    @pytest.mark.asyncio
    async def test_deliver_success(self) -> None:
        hub = IntegrationHub()
        hub.register_connector(
            ConnectorDefinition(id="c1", name="C1", type="http", endpoint_url="https://ex.com")
        )
        m = IntegrationMessage(id="m1", source="a", destination="b")
        await hub._deliver_to_connector(m, "c1")
