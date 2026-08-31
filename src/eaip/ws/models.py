"""WebSocket models — connections, channels, messages, subscriptions, config."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class WsConfig(BaseModel):
    """Configuration for the WebSocket subsystem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    heartbeat_interval_seconds: int = Field(default=30, ge=5, le=300)
    max_connections_per_user: int = Field(default=10, ge=1, le=1000)
    message_queue_size: int = Field(default=1000, ge=1, le=100000)
    enable_presence: bool = Field(default=True)
    enable_history: bool = Field(default=True)


class WebSocketConnection(BaseModel):
    """Represents a single WebSocket connection."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    channel: str
    user_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    connected_at: datetime = Field(default_factory=utc_now)
    last_heartbeat: datetime = Field(default_factory=utc_now)
    status: Literal["active", "idle", "disconnected"] = Field(default="active")


class Channel(BaseModel):
    """A pub/sub channel for real-time messaging."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: Literal["public", "private", "presence"] = Field(default="public")
    description: str = Field(default="")
    allowed_roles: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    """A message published to a channel."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    channel: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    sender_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Subscription(BaseModel):
    """A user's subscription to a channel with optional filters."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    channel_id: str
    user_id: str
    filters: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "Channel",
    "Message",
    "Subscription",
    "WebSocketConnection",
    "WsConfig",
]
