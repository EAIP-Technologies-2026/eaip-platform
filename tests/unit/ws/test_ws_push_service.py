from __future__ import annotations

import anyio
import pytest

from eaip.ws.channel_manager import ChannelManager
from eaip.ws.connection_manager import ConnectionManager
from eaip.ws.models import Channel, WebSocketConnection
from eaip.ws.push_service import PushService


class _Fixture:
    def __init__(self) -> None:
        self.channel_manager = ChannelManager()
        self.connection_manager = ConnectionManager()
        self.service = PushService(
            channel_manager=self.channel_manager,
            connection_manager=self.connection_manager,
        )


@pytest.fixture
def fixture() -> _Fixture:
    fxt = _Fixture()
    fxt.channel_manager.create(Channel(id="ch1", name="general"))
    fxt.channel_manager.create(Channel(id="ch2", name="random"))
    fxt.connection_manager.register(
        WebSocketConnection(id="c1", channel="ch1", user_id="u1"),
    )
    fxt.connection_manager.register(
        WebSocketConnection(id="c2", channel="ch2", user_id="u2"),
    )
    return fxt


class TestPushService:
    @pytest.mark.asyncio
    async def test_push(self, fixture: _Fixture) -> None:
        msg = await fixture.service.push("ch1", "chat", {"text": "hello"}, sender_id="u1")
        assert msg.channel == "ch1"
        assert msg.event_type == "chat"
        assert msg.payload["text"] == "hello"
        assert msg.sender_id == "u1"

    @pytest.mark.asyncio
    async def test_push_default_payload(self, fixture: _Fixture) -> None:
        msg = await fixture.service.push("ch1", "ping", sender_id="system")
        assert msg.payload == {}

    @pytest.mark.asyncio
    async def test_push_to_user(self, fixture: _Fixture) -> None:
        messages = await fixture.service.push_to_user("u1", "private", {"msg": "secret"})
        assert len(messages) >= 1
        for m in messages:
            assert m.sender_id == "u1"

    @pytest.mark.asyncio
    async def test_push_to_user_no_connections(self, fixture: _Fixture) -> None:
        messages = await fixture.service.push_to_user("unknown", "test")
        assert messages == []

    @pytest.mark.asyncio
    async def test_push_to_all(self, fixture: _Fixture) -> None:
        messages = await fixture.service.push_to_all(
            "announcement", {"text": "all"}, sender_id="admin"
        )
        assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_broadcast_except_channels(self, fixture: _Fixture) -> None:
        messages = await fixture.service.broadcast(
            "event",
            {"x": 1},
            sender_id="admin",
            except_channels=("ch2",),
        )
        channels = {m.channel for m in messages}
        assert "ch2" not in channels
        assert "ch1" in channels

    @pytest.mark.asyncio
    async def test_broadcast_no_exclusions(self, fixture: _Fixture) -> None:
        messages = await fixture.service.broadcast("event", sender_id="admin")
        assert len(messages) == 2

    def test_get_channel_history(self, fixture: _Fixture) -> None:
        anyio.run(fixture.service.push, "ch1", "chat", {"text": "h1"}, "u1")
        anyio.run(fixture.service.push, "ch1", "chat", {"text": "h2"}, "u1")
        history = fixture.service.get_channel_history("ch1")
        assert len(history) == 2

    def test_get_channel_history_empty(self, fixture: _Fixture) -> None:
        history = fixture.service.get_channel_history("nonexistent")
        assert history == []

    def test_get_channel_history_limit(self, fixture: _Fixture) -> None:
        for i in range(10):
            anyio.run(fixture.service.push, "ch1", "chat", {"n": i}, "u1")
        history = fixture.service.get_channel_history("ch1", limit=3)
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_push_without_history(self, fixture: _Fixture) -> None:
        svc = PushService(
            channel_manager=fixture.channel_manager,
            connection_manager=fixture.connection_manager,
            enable_history=False,
        )
        msg = await svc.push("ch1", "event", sender_id="u1")
        assert msg.event_type == "event"
        assert svc.get_channel_history("ch1") == []

    @pytest.mark.asyncio
    async def test_push_to_user_multiple_connections(self, fixture: _Fixture) -> None:
        fixture.connection_manager.register(
            WebSocketConnection(id="c3", channel="ch1", user_id="u1"),
        )
        messages = await fixture.service.push_to_user("u1", "test")
        assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_history_max_size(self, fixture: _Fixture) -> None:
        svc = PushService(
            channel_manager=fixture.channel_manager,
            connection_manager=fixture.connection_manager,
            enable_history=True,
            max_history=5,
        )
        for i in range(10):
            await svc.push("ch1", "chat", {"n": i}, "u1")
        history = svc.get_channel_history("ch1")
        assert len(history) == 5
