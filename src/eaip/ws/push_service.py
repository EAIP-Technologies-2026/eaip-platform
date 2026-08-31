"""PushService — publish messages to channels, users, or broadcast with active socket delivery."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from eaip.logging.context import get_logger
from eaip.ws.channel_manager import ChannelManager
from eaip.ws.connection_manager import ConnectionManager
from eaip.ws.models import Message

log = get_logger("eaip.ws.push_service")

SocketSend = Callable[[str], Any]


class PushService:
    """Handles message publishing and delivery to connections.

    Maintains a registry of active socket send functions for real-time delivery.
    """

    def __init__(
        self,
        channel_manager: ChannelManager,
        connection_manager: ConnectionManager,
        enable_history: bool = True,
        max_history: int = 100,
    ) -> None:
        self._channel_manager = channel_manager
        self._connection_manager = connection_manager
        self._enable_history = enable_history
        self._max_history = max_history
        self._history: dict[str, list[Message]] = {}
        self._socket_senders: dict[str, SocketSend] = {}
        self._pending: dict[str, list[dict[str, Any]]] = {}

    def register_socket(self, connection_id: str, send_fn: SocketSend) -> None:
        """Register an active socket sender for real-time message delivery."""
        self._socket_senders[connection_id] = send_fn
        if connection_id in self._pending:
            for msg in self._pending.pop(connection_id, []):
                try:
                    send_fn(json.dumps(msg))
                except Exception:
                    pass

    def unregister_socket(self, connection_id: str) -> None:
        """Remove a socket sender on disconnect."""
        self._socket_senders.pop(connection_id, None)
        self._pending.pop(connection_id, None)

    async def push(
        self,
        channel: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        sender_id: str = "",
    ) -> Message:
        """Push a message to all connections on a channel."""
        msg = Message(
            id=f"msg-{channel}-{id(payload)}",
            channel=channel,
            event_type=event_type,
            payload=payload or {},
            sender_id=sender_id,
        )
        msg_data = {
            "type": "message",
            "channel": channel,
            "event_type": event_type,
            "payload": payload or {},
            "sender_id": sender_id,
            "timestamp": msg.created_at.isoformat() if hasattr(msg, "created_at") else "",
        }
        connections = self._connection_manager.get_connections_by_channel(channel)
        for conn in connections:
            sender = self._socket_senders.get(conn.id)
            if sender:
                try:
                    sender(json.dumps(msg_data))
                except Exception:
                    self._pending.setdefault(conn.id, []).append(msg_data)
            else:
                self._pending.setdefault(conn.id, []).append(msg_data)
        if self._enable_history:
            self._add_to_history(channel, msg)
        return msg

    async def push_to_user(
        self,
        user_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> list[Message]:
        """Push a message to all connections for a specific user."""
        connections = self._connection_manager.get_connections_by_user(user_id)
        messages: list[Message] = []
        for conn in connections:
            msg = await self.push(conn.channel, event_type, payload, user_id)
            messages.append(msg)
        return messages

    async def push_to_all(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        sender_id: str = "",
    ) -> list[Message]:
        """Push a message to all connections across all channels."""
        channels = self._channel_manager.list_channels()
        messages: list[Message] = []
        for channel in channels:
            msg = await self.push(channel.id, event_type, payload, sender_id)
            messages.append(msg)
        return messages

    async def broadcast(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        sender_id: str = "",
        except_channels: tuple[str, ...] | None = None,
    ) -> list[Message]:
        """Broadcast to all channels, optionally excluding some."""
        except_channels = except_channels or ()
        channels = self._channel_manager.list_channels()
        messages: list[Message] = []
        for channel in channels:
            if channel.id in except_channels:
                continue
            msg = await self.push(channel.id, event_type, payload, sender_id)
            messages.append(msg)
        return messages

    def get_channel_history(self, channel: str, limit: int = 50) -> list[Message]:
        """Return recent history for a channel."""
        history = self._history.get(channel, [])
        return history[-limit:]

    def get_metrics(self) -> dict[str, Any]:
        """Return push service metrics."""
        return {
            "active_sockets": len(self._socket_senders),
            "pending_messages": sum(len(v) for v in self._pending.values()),
            "channels_with_history": len(self._history),
            "total_history_messages": sum(len(v) for v in self._history.values()),
        }

    def _add_to_history(self, channel: str, msg: Message) -> None:
        if channel not in self._history:
            self._history[channel] = []
        self._history[channel].append(msg)
        if len(self._history[channel]) > self._max_history:
            self._history[channel] = self._history[channel][-self._max_history :]


__all__ = ["PushService"]
