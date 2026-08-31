from __future__ import annotations

import pydantic
import pytest

from eaip.ws.models import Channel, Message, Subscription, WebSocketConnection, WsConfig


class TestWsConfig:
    def test_defaults(self) -> None:
        cfg = WsConfig()
        assert cfg.heartbeat_interval_seconds == 30
        assert cfg.max_connections_per_user == 10
        assert cfg.message_queue_size == 1000
        assert cfg.enable_presence is True
        assert cfg.enable_history is True

    def test_frozen(self) -> None:
        cfg = WsConfig()
        with pytest.raises(pydantic.ValidationError):
            cfg.heartbeat_interval_seconds = 60  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            WsConfig(unknown=True)  # type: ignore[call-arg]

    def test_heartbeat_range(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            WsConfig(heartbeat_interval_seconds=1)

    def test_max_connections_per_user_range(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            WsConfig(max_connections_per_user=0)


class TestWebSocketConnection:
    def test_defaults(self) -> None:
        conn = WebSocketConnection(id="c1", channel="ch1", user_id="u1")
        assert conn.id == "c1"
        assert conn.channel == "ch1"
        assert conn.user_id == "u1"
        assert conn.metadata == {}
        assert conn.status == "active"

    def test_frozen(self) -> None:
        conn = WebSocketConnection(id="c1", channel="ch1", user_id="u1")
        with pytest.raises(pydantic.ValidationError):
            conn.status = "disconnected"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            WebSocketConnection(id="c1", channel="ch1", user_id="u1", unknown="x")  # type: ignore[call-arg]

    def test_invalid_status(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            WebSocketConnection(id="c1", channel="ch1", user_id="u1", status="unknown")

    def test_all_fields(self) -> None:
        conn = WebSocketConnection(
            id="c1",
            channel="ch1",
            user_id="u1",
            metadata={"ip": "127.0.0.1"},
            status="idle",
        )
        assert conn.metadata["ip"] == "127.0.0.1"
        assert conn.status == "idle"


class TestChannel:
    def test_defaults(self) -> None:
        ch = Channel(id="ch1", name="general")
        assert ch.id == "ch1"
        assert ch.name == "general"
        assert ch.type == "public"
        assert ch.description == ""
        assert ch.allowed_roles == ()
        assert ch.metadata == {}

    def test_frozen(self) -> None:
        ch = Channel(id="ch1", name="general")
        with pytest.raises(pydantic.ValidationError):
            ch.name = "modified"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            Channel(id="ch1", name="general", unknown="x")  # type: ignore[call-arg]

    def test_private_channel(self) -> None:
        ch = Channel(id="ch1", name="private-chat", type="private", allowed_roles=("admin",))
        assert ch.type == "private"
        assert ch.allowed_roles == ("admin",)

    def test_presence_channel(self) -> None:
        ch = Channel(
            id="ch1", name="presence-room", type="presence", description="Presence channel"
        )
        assert ch.type == "presence"
        assert ch.description == "Presence channel"

    def test_invalid_type(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            Channel(id="ch1", name="x", type="invalid")


class TestMessage:
    def test_defaults(self) -> None:
        msg = Message(id="m1", channel="ch1", event_type="test", sender_id="u1")
        assert msg.id == "m1"
        assert msg.channel == "ch1"
        assert msg.event_type == "test"
        assert msg.payload == {}
        assert msg.metadata == {}

    def test_frozen(self) -> None:
        msg = Message(id="m1", channel="ch1", event_type="test", sender_id="u1")
        with pytest.raises(pydantic.ValidationError):
            msg.payload = {"key": "val"}  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            Message(id="m1", channel="ch1", event_type="test", sender_id="u1", unknown="x")  # type: ignore[call-arg]

    def test_with_payload(self) -> None:
        msg = Message(
            id="m1", channel="ch1", event_type="chat", sender_id="u1", payload={"text": "hello"}
        )
        assert msg.payload["text"] == "hello"


class TestSubscription:
    def test_defaults(self) -> None:
        sub = Subscription(id="s1", channel_id="ch1", user_id="u1")
        assert sub.id == "s1"
        assert sub.channel_id == "ch1"
        assert sub.user_id == "u1"
        assert sub.filters == {}

    def test_frozen(self) -> None:
        sub = Subscription(id="s1", channel_id="ch1", user_id="u1")
        with pytest.raises(pydantic.ValidationError):
            sub.user_id = "u2"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            Subscription(id="s1", channel_id="ch1", user_id="u1", unknown="x")  # type: ignore[call-arg]

    def test_with_filters(self) -> None:
        sub = Subscription(id="s1", channel_id="ch1", user_id="u1", filters={"event_type": "chat"})
        assert sub.filters["event_type"] == "chat"
