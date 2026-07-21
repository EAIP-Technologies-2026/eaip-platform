from __future__ import annotations

import pytest

from eaip.ws.connection_manager import ConnectionManager
from eaip.ws.exceptions import ConnectionNotFoundError
from eaip.ws.models import WebSocketConnection


class TestConnectionManager:
    def test_register(self) -> None:
        mgr = ConnectionManager()
        conn = WebSocketConnection(id="c1", channel="ch1", user_id="u1")
        result = mgr.register(conn)
        assert result.id == "c1"
        assert mgr.get("c1") is conn

    def test_unregister(self) -> None:
        mgr = ConnectionManager()
        conn = WebSocketConnection(id="c1", channel="ch1", user_id="u1")
        mgr.register(conn)
        result = mgr.unregister("c1")
        assert result.id == "c1"
        assert mgr.get("c1") is None

    def test_unregister_not_found(self) -> None:
        mgr = ConnectionManager()
        with pytest.raises(ConnectionNotFoundError):
            mgr.unregister("unknown")

    def test_get_returns_none(self) -> None:
        mgr = ConnectionManager()
        assert mgr.get("unknown") is None

    def test_get_connection(self) -> None:
        mgr = ConnectionManager()
        conn = WebSocketConnection(id="c1", channel="ch1", user_id="u1")
        mgr.register(conn)
        assert mgr.get_connection("c1") is conn

    def test_get_connection_not_found(self) -> None:
        mgr = ConnectionManager()
        with pytest.raises(ConnectionNotFoundError):
            mgr.get_connection("unknown")

    def test_list_connections_empty(self) -> None:
        mgr = ConnectionManager()
        assert mgr.list_connections() == []

    def test_list_connections(self) -> None:
        mgr = ConnectionManager()
        mgr.register(WebSocketConnection(id="c1", channel="ch1", user_id="u1"))
        mgr.register(WebSocketConnection(id="c2", channel="ch2", user_id="u2"))
        assert len(mgr.list_connections()) == 2

    def test_get_connections_by_user(self) -> None:
        mgr = ConnectionManager()
        mgr.register(WebSocketConnection(id="c1", channel="ch1", user_id="u1"))
        mgr.register(WebSocketConnection(id="c2", channel="ch2", user_id="u1"))
        conns = mgr.get_connections_by_user("u1")
        assert len(conns) == 2

    def test_get_connections_by_user_empty(self) -> None:
        mgr = ConnectionManager()
        assert mgr.get_connections_by_user("unknown") == []

    def test_get_connections_by_channel(self) -> None:
        mgr = ConnectionManager()
        mgr.register(WebSocketConnection(id="c1", channel="ch1", user_id="u1"))
        mgr.register(WebSocketConnection(id="c2", channel="ch1", user_id="u2"))
        conns = mgr.get_connections_by_channel("ch1")
        assert len(conns) == 2

    def test_heartbeat(self) -> None:
        mgr = ConnectionManager()
        conn = WebSocketConnection(id="c1", channel="ch1", user_id="u1")
        mgr.register(conn)
        updated = mgr.heartbeat("c1")
        assert updated.status == "active"
        assert updated.last_heartbeat >= conn.last_heartbeat

    def test_heartbeat_not_found(self) -> None:
        mgr = ConnectionManager()
        with pytest.raises(ConnectionNotFoundError):
            mgr.heartbeat("unknown")

    def test_get_active_count(self) -> None:
        mgr = ConnectionManager()
        conn = WebSocketConnection(id="c1", channel="ch1", user_id="u1")
        mgr.register(conn)
        count = mgr.get_active_count()
        assert count >= 1

    def test_purge_stale(self) -> None:
        mgr = ConnectionManager()
        mgr.register(WebSocketConnection(id="c1", channel="ch1", user_id="u1"))
        stale = mgr.purge_stale()
        assert isinstance(stale, list)

    def test_update_status(self) -> None:
        mgr = ConnectionManager()
        conn = WebSocketConnection(id="c1", channel="ch1", user_id="u1")
        mgr.register(conn)
        updated = mgr.update_status("c1", "idle")
        assert updated.status == "idle"

    def test_update_status_not_found(self) -> None:
        mgr = ConnectionManager()
        with pytest.raises(ConnectionNotFoundError):
            mgr.update_status("unknown", "idle")

    def test_get_active_count_no_connections(self) -> None:
        mgr = ConnectionManager()
        assert mgr.get_active_count() == 0

    def test_register_duplicate_overwrites(self) -> None:
        mgr = ConnectionManager()
        c1 = WebSocketConnection(id="c1", channel="ch1", user_id="u1")
        c2 = WebSocketConnection(id="c1", channel="ch2", user_id="u2")
        mgr.register(c1)
        mgr.register(c2)
        assert mgr.get("c1").channel == "ch2"
