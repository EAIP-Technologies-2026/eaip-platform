"""WebSocket domain events."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class WsEvent(DomainEvent):
    """Base event for all WebSocket events."""

    event_type: ClassVar[str] = "eaip.ws.event"


class ClientConnected(WsEvent):
    """Published when a WebSocket client connects."""

    event_type: ClassVar[str] = "eaip.ws.client.connected"
    connection_id: str
    user_id: str
    channel: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClientDisconnected(WsEvent):
    """Published when a WebSocket client disconnects."""

    event_type: ClassVar[str] = "eaip.ws.client.disconnected"
    connection_id: str
    user_id: str
    channel: str
    reason: str = ""


class ChannelCreated(WsEvent):
    """Published when a channel is created."""

    event_type: ClassVar[str] = "eaip.ws.channel.created"
    channel_id: str
    channel_name: str
    channel_type: str = "public"


class ChannelDeleted(WsEvent):
    """Published when a channel is deleted."""

    event_type: ClassVar[str] = "eaip.ws.channel.deleted"
    channel_id: str
    channel_name: str


class UserSubscribed(WsEvent):
    """Published when a user subscribes to a channel."""

    event_type: ClassVar[str] = "eaip.ws.user.subscribed"
    user_id: str
    channel_id: str
    subscription_id: str


class UserUnsubscribed(WsEvent):
    """Published when a user unsubscribes from a channel."""

    event_type: ClassVar[str] = "eaip.ws.user.unsubscribed"
    user_id: str
    channel_id: str
    subscription_id: str


class MessagePublished(WsEvent):
    """Published when a message is sent to a channel."""

    event_type: ClassVar[str] = "eaip.ws.message.published"
    message_id: str
    channel: str
    event_type_name: str
    sender_id: str


class MessageBroadcast(WsEvent):
    """Published when a message is broadcast to all channels."""

    event_type: ClassVar[str] = "eaip.ws.message.broadcast"
    message_id: str
    sender_id: str
    except_channels: tuple[str, ...] = ()


__all__ = [
    "ChannelCreated",
    "ChannelDeleted",
    "ClientConnected",
    "ClientDisconnected",
    "MessageBroadcast",
    "MessagePublished",
    "UserSubscribed",
    "UserUnsubscribed",
    "WsEvent",
]
