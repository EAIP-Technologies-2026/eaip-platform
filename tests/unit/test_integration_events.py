"""Tests for integration domain events."""

from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.integration.events import (
    ConnectorRegistered,
    ConnectorUnregistered,
    MessageReceived,
    MessageRouted,
    MessageSent,
    MessageTransformed,
    RouteRegistered,
    TransformationApplied,
    WebhookDelivered,
    WebhookTriggered,
)
from eaip.integration.models import (
    ConnectorDefinition,
    IntegrationMessage,
    MessageRoute,
    Transformation,
)


class TestConnectorRegistered:
    def test_event_type(self) -> None:
        c = ConnectorDefinition(id="c1", name="C1", type="http", endpoint_url="https://ex.com")
        event = ConnectorRegistered(connector=c)
        assert event.event_type == "integration.connector.registered"
        assert isinstance(event, DomainEvent)

    def test_connector_content(self) -> None:
        c = ConnectorDefinition(id="c1", name="Test", type="http", endpoint_url="https://ex.com")
        event = ConnectorRegistered(connector=c)
        assert event.connector.id == "c1"
        assert event.connector.name == "Test"


class TestConnectorUnregistered:
    def test_event_type(self) -> None:
        event = ConnectorUnregistered(connector_id="c1", connector_name="C1")
        assert event.event_type == "integration.connector.unregistered"

    def test_fields(self) -> None:
        event = ConnectorUnregistered(connector_id="c1", connector_name="Test Connector")
        assert event.connector_id == "c1"
        assert event.connector_name == "Test Connector"


class TestMessageSent:
    def test_event_type(self) -> None:
        m = IntegrationMessage(id="m1", source="a", destination="b")
        event = MessageSent(message=m)
        assert event.event_type == "integration.message.sent"

    def test_message_content(self) -> None:
        m = IntegrationMessage(id="m1", source="sys-a", destination="sys-b")
        event = MessageSent(message=m)
        assert event.message.id == "m1"
        assert event.message.source == "sys-a"


class TestMessageReceived:
    def test_event_type(self) -> None:
        m = IntegrationMessage(id="m1", source="a", destination="b")
        event = MessageReceived(message=m)
        assert event.event_type == "integration.message.received"

    def test_message_content(self) -> None:
        m = IntegrationMessage(id="m1", source="sys-a", destination="sys-b")
        event = MessageReceived(message=m)
        assert event.message.id == "m1"


class TestMessageRouted:
    def test_event_type(self) -> None:
        m = IntegrationMessage(id="m1", source="a", destination="b")
        event = MessageRouted(message=m, route_id="r1", route_name="R1")
        assert event.event_type == "integration.message.routed"

    def test_fields(self) -> None:
        m = IntegrationMessage(id="m1", source="a", destination="b")
        event = MessageRouted(message=m, route_id="r1", route_name="Test Route")
        assert event.route_id == "r1"
        assert event.route_name == "Test Route"


class TestMessageTransformed:
    def test_event_type(self) -> None:
        m = IntegrationMessage(id="m1", source="a", destination="b")
        event = MessageTransformed(message=m, transformation_id="t1", transformation_name="T1")
        assert event.event_type == "integration.message.transformed"

    def test_fields(self) -> None:
        m = IntegrationMessage(id="m1", source="a", destination="b")
        event = MessageTransformed(
            message=m, transformation_id="t1", transformation_name="MapFields"
        )
        assert event.transformation_id == "t1"
        assert event.transformation_name == "MapFields"


class TestWebhookTriggered:
    def test_event_type(self) -> None:
        event = WebhookTriggered(webhook_id="w1", webhook_name="Hook1", payload_size=100)
        assert event.event_type == "integration.webhook.triggered"

    def test_fields(self) -> None:
        event = WebhookTriggered(webhook_id="w1", webhook_name="Order Webhook", payload_size=512)
        assert event.webhook_id == "w1"
        assert event.payload_size == 512


class TestWebhookDelivered:
    def test_event_type(self) -> None:
        event = WebhookDelivered(
            webhook_id="w1", webhook_name="Hook1", status_code=200, duration_ms=10.5
        )
        assert event.event_type == "integration.webhook.delivered"

    def test_fields(self) -> None:
        event = WebhookDelivered(
            webhook_id="w1", webhook_name="Order Webhook", status_code=200, duration_ms=42.0
        )
        assert event.status_code == 200
        assert event.duration_ms == 42.0


class TestRouteRegistered:
    def test_event_type(self) -> None:
        r = MessageRoute(id="r1", name="R1", source_pattern="a", destination_pattern="b")
        event = RouteRegistered(route=r)
        assert event.event_type == "integration.route.registered"

    def test_route_content(self) -> None:
        r = MessageRoute(
            id="r1",
            name="Orders to Warehouse",
            source_pattern="orders.*",
            destination_pattern="warehouse",
        )
        event = RouteRegistered(route=r)
        assert event.route.id == "r1"
        assert event.route.source_pattern == "orders.*"


class TestTransformationApplied:
    def test_event_type(self) -> None:
        t = Transformation(id="t1", name="T1", type="mapping")
        event = TransformationApplied(transformation=t, message_id="m1")
        assert event.event_type == "integration.transformation.applied"

    def test_fields(self) -> None:
        t = Transformation(id="t1", name="MapFields", type="mapping")
        event = TransformationApplied(transformation=t, message_id="m1")
        assert event.transformation.name == "MapFields"
        assert event.message_id == "m1"


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(ConnectorRegistered, DomainEvent)
        assert issubclass(ConnectorUnregistered, DomainEvent)
        assert issubclass(MessageSent, DomainEvent)
        assert issubclass(MessageReceived, DomainEvent)
        assert issubclass(MessageRouted, DomainEvent)
        assert issubclass(MessageTransformed, DomainEvent)
        assert issubclass(WebhookTriggered, DomainEvent)
        assert issubclass(WebhookDelivered, DomainEvent)
        assert issubclass(RouteRegistered, DomainEvent)
        assert issubclass(TransformationApplied, DomainEvent)
