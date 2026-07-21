"""ConnectionManager — register, unregister, list, heartbeat management."""

from __future__ import annotations

from datetime import timedelta
from typing import Literal, cast

from eaip.shared.time import utc_now
from eaip.ws.exceptions import ConnectionNotFoundError
from eaip.ws.models import WebSocketConnection


class ConnectionManager:
    """Manages WebSocket connections with registration and heartbeat tracking."""

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._connections: dict[str, WebSocketConnection] = {}
        self._heartbeat_timeout: timedelta = timedelta(seconds=60)

    def register(self, connection: WebSocketConnection) -> WebSocketConnection:
        """Register a new connection."""
        self._connections[connection.id] = connection
        return connection

    def unregister(self, connection_id: str) -> WebSocketConnection:
        """Unregister a connection by id."""
        conn = self._connections.pop(connection_id, None)
        if conn is None:
            raise ConnectionNotFoundError(
                f"Connection {connection_id!r} not found.",
                context={"connection_id": connection_id},
            )
        return conn

    def get(self, connection_id: str) -> WebSocketConnection | None:
        """Get a connection by id, or None."""
        return self._connections.get(connection_id)

    def get_connection(self, connection_id: str) -> WebSocketConnection:
        """Get a connection by id, raising if not found."""
        conn = self.get(connection_id)
        if conn is None:
            raise ConnectionNotFoundError(
                f"Connection {connection_id!r} not found.",
                context={"connection_id": connection_id},
            )
        return conn

    def list_connections(self) -> list[WebSocketConnection]:
        """Return all registered connections."""
        return list(self._connections.values())

    def get_connections_by_user(self, user_id: str) -> list[WebSocketConnection]:
        """Return all connections for a given user."""
        return [c for c in self._connections.values() if c.user_id == user_id]

    def get_connections_by_channel(self, channel: str) -> list[WebSocketConnection]:
        """Return all connections on a given channel."""
        return [c for c in self._connections.values() if c.channel == channel]

    def heartbeat(self, connection_id: str) -> WebSocketConnection:
        """Update the last_heartbeat timestamp for a connection."""
        conn = self.get_connection(connection_id)
        updated = WebSocketConnection(
            id=conn.id,
            channel=conn.channel,
            user_id=conn.user_id,
            metadata=conn.metadata,
            connected_at=conn.connected_at,
            last_heartbeat=utc_now(),
            status="active",
        )
        self._connections[connection_id] = updated
        return updated

    def get_active_count(self) -> int:
        """Return the number of connections with recent heartbeats."""
        now = utc_now()
        return sum(
            1
            for c in self._connections.values()
            if (now - c.last_heartbeat) < self._heartbeat_timeout
        )

    def purge_stale(self) -> list[str]:
        """Remove stale connections and return their ids."""
        now = utc_now()
        stale_ids = [
            cid
            for cid, c in self._connections.items()
            if (now - c.last_heartbeat) >= self._heartbeat_timeout
        ]
        for cid in stale_ids:
            self._connections.pop(cid, None)
        return stale_ids

    def update_status(self, connection_id: str, status: str) -> WebSocketConnection:
        """Update the status of a connection."""
        conn = self.get_connection(connection_id)
        updated = WebSocketConnection(
            id=conn.id,
            channel=conn.channel,
            user_id=conn.user_id,
            metadata=conn.metadata,
            connected_at=conn.connected_at,
            last_heartbeat=conn.last_heartbeat,
            status=cast("Literal['active', 'idle', 'disconnected']", status),
        )
        self._connections[connection_id] = updated
        return updated


__all__ = ["ConnectionManager"]
