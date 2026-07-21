"""Tests for :mod:`eaip.devplatform.playground`."""

from __future__ import annotations

import pytest

from eaip.devplatform.events import PlaygroundSessionCreated
from eaip.devplatform.exceptions import PlaygroundError
from eaip.devplatform.playground import ApiPlayground


@pytest.fixture
def playground() -> ApiPlayground:
    return ApiPlayground()


class TestApiPlayground:
    async def test_create_session(self, playground: ApiPlayground) -> None:
        session = await playground.create_session("d1", "e1")
        assert session.developer_id == "d1"
        assert session.endpoint_id == "e1"
        assert session.id == "d1:e1"

    async def test_create_session_emits_event(self, playground: ApiPlayground) -> None:
        events: list[PlaygroundSessionCreated] = []
        playground.on_event(events.append)
        await playground.create_session("d1", "e1")
        assert len(events) == 1
        assert events[0].developer_id == "d1"
        assert events[0].endpoint_id == "e1"

    async def test_get_session(self, playground: ApiPlayground) -> None:
        created = await playground.create_session("d1", "e1")
        session = await playground.get_session(created.id)
        assert session.id == created.id

    async def test_get_session_not_found(self, playground: ApiPlayground) -> None:
        with pytest.raises(PlaygroundError):
            await playground.get_session("nonexistent")

    async def test_execute_test_request(self, playground: ApiPlayground) -> None:
        session = await playground.create_session("d1", "e1")
        request = {"method": "GET", "path": "/users"}
        updated = await playground.execute_test_request(session.id, request)
        assert updated.request_preview == request
        assert updated.response_preview["status"] == "ok"

    async def test_execute_test_request_not_found(self, playground: ApiPlayground) -> None:
        with pytest.raises(PlaygroundError):
            await playground.execute_test_request("nonexistent", {})

    async def test_list_sessions(self, playground: ApiPlayground) -> None:
        await playground.create_session("d1", "e1")
        await playground.create_session("d1", "e2")
        await playground.create_session("d2", "e1")
        sessions = await playground.list_sessions("d1")
        assert len(sessions) == 2

    async def test_list_sessions_empty(self, playground: ApiPlayground) -> None:
        sessions = await playground.list_sessions("d1")
        assert sessions == ()

    async def test_clear_session(self, playground: ApiPlayground) -> None:
        session = await playground.create_session("d1", "e1")
        await playground.clear_session(session.id)
        with pytest.raises(PlaygroundError):
            await playground.get_session(session.id)

    async def test_clear_session_not_found(self, playground: ApiPlayground) -> None:
        with pytest.raises(PlaygroundError):
            await playground.clear_session("nonexistent")
