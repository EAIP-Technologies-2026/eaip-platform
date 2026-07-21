"""WebSocket & Real-time Push — connection management, channels, push delivery.

Bundle-077 of the EAIP Platform Foundation Milestone.
"""

from __future__ import annotations

from eaip.ws.channel_manager import ChannelManager
from eaip.ws.connection_manager import ConnectionManager
from eaip.ws.events import (
    ChannelCreated,
    ChannelDeleted,
    ClientConnected,
    ClientDisconnected,
    MessageBroadcast,
    MessagePublished,
    UserSubscribed,
    UserUnsubscribed,
)
from eaip.ws.exceptions import (
    ChannelNotFoundError,
    ConnectionNotFoundError,
    SubscriptionError,
    WsError,
)
from eaip.ws.health import WsHealthCheck
from eaip.ws.integration import WsRuntimeModule
from eaip.ws.models import (
    Channel,
    Message,
    Subscription,
    WebSocketConnection,
    WsConfig,
)
from eaip.ws.push_service import PushService

__all__ = [
    "Channel",
    "ChannelCreated",
    "ChannelDeleted",
    "ChannelManager",
    "ChannelNotFoundError",
    "ClientConnected",
    "ClientDisconnected",
    "ConnectionManager",
    "ConnectionNotFoundError",
    "Message",
    "MessageBroadcast",
    "MessagePublished",
    "PushService",
    "Subscription",
    "SubscriptionError",
    "UserSubscribed",
    "UserUnsubscribed",
    "WebSocketConnection",
    "WsConfig",
    "WsError",
    "WsHealthCheck",
    "WsRuntimeModule",
]
