"""Domain events for the cross-platform connector bridge."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ConnectorRegistered(DomainEvent):
    """Emitted when a new connector is registered."""

    event_type: ClassVar[str] = "eaip.xbridge.connector.registered"

    connector_id: str
    name: str
    protocol: str


class ConnectorUpdated(DomainEvent):
    """Emitted when a connector is updated."""

    event_type: ClassVar[str] = "eaip.xbridge.connector.updated"

    connector_id: str
    name: str


class ConnectorDeleted(DomainEvent):
    """Emitted when a connector is deleted."""

    event_type: ClassVar[str] = "eaip.xbridge.connector.deleted"

    connector_id: str
    name: str


class MessageSent(DomainEvent):
    """Emitted when a message is sent through the bridge."""

    event_type: ClassVar[str] = "eaip.xbridge.message.sent"

    message_id: str
    source: str
    target: str
    content_type: str


class MessageReceived(DomainEvent):
    """Emitted when a message is received by a target connector."""

    event_type: ClassVar[str] = "eaip.xbridge.message.received"

    message_id: str
    source: str
    target: str
    content_type: str


__all__ = [
    "ConnectorDeleted",
    "ConnectorRegistered",
    "ConnectorUpdated",
    "MessageReceived",
    "MessageSent",
]
