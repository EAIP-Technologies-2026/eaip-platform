"""Domain events for the integration hub."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent
from eaip.integration.models import (
    ConnectorDefinition,
    IntegrationMessage,
    MessageRoute,
    Transformation,
)


class ConnectorRegistered(DomainEvent):
    event_type: ClassVar[str] = "integration.connector.registered"
    connector: ConnectorDefinition


class ConnectorUnregistered(DomainEvent):
    event_type: ClassVar[str] = "integration.connector.unregistered"
    connector_id: str
    connector_name: str


class MessageSent(DomainEvent):
    event_type: ClassVar[str] = "integration.message.sent"
    message: IntegrationMessage


class MessageReceived(DomainEvent):
    event_type: ClassVar[str] = "integration.message.received"
    message: IntegrationMessage


class MessageRouted(DomainEvent):
    event_type: ClassVar[str] = "integration.message.routed"
    message: IntegrationMessage
    route_id: str
    route_name: str


class MessageTransformed(DomainEvent):
    event_type: ClassVar[str] = "integration.message.transformed"
    message: IntegrationMessage
    transformation_id: str
    transformation_name: str


class WebhookTriggered(DomainEvent):
    event_type: ClassVar[str] = "integration.webhook.triggered"
    webhook_id: str
    webhook_name: str
    payload_size: int


class WebhookDelivered(DomainEvent):
    event_type: ClassVar[str] = "integration.webhook.delivered"
    webhook_id: str
    webhook_name: str
    status_code: int
    duration_ms: float


class RouteRegistered(DomainEvent):
    event_type: ClassVar[str] = "integration.route.registered"
    route: MessageRoute


class TransformationApplied(DomainEvent):
    event_type: ClassVar[str] = "integration.transformation.applied"
    transformation: Transformation
    message_id: str


__all__ = [
    "ConnectorRegistered",
    "ConnectorUnregistered",
    "MessageReceived",
    "MessageRouted",
    "MessageSent",
    "MessageTransformed",
    "RouteRegistered",
    "TransformationApplied",
    "WebhookDelivered",
    "WebhookTriggered",
]
