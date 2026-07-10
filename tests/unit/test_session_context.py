"""Tests for EnterpriseContextManager."""

from __future__ import annotations

import asyncio

from eaip.session.context_manager import EnterpriseContextManager, ScopedStore
from eaip.session.models import ContextPropagationConfig, ContextScope, Session, SessionContext


class TestScopedStore:
    def test_get_context_creates_empty(self) -> None:
        store = ScopedStore()
        ctx = store.get_context("user", "u1")
        assert ctx == {}

    def test_set_and_get_attribute(self) -> None:
        store = ScopedStore()
        store.set_attribute("user", "u1", "role", "admin")
        assert store.get_attribute("user", "u1", "role") == "admin"

    def test_get_attribute_missing(self) -> None:
        store = ScopedStore()
        assert store.get_attribute("user", "u1", "missing") is None

    def test_clear_context(self) -> None:
        store = ScopedStore()
        store.set_attribute("user", "u1", "role", "admin")
        store.clear_context("user", "u1")
        assert store.get_attribute("user", "u1", "role") is None

    def test_clear_all(self) -> None:
        store = ScopedStore()
        store.set_attribute("user", "u1", "a", "1")
        store.set_attribute("user", "u2", "b", "2")
        store.clear_all()
        assert store.get_attribute("user", "u1", "a") is None
        assert store.get_attribute("user", "u2", "b") is None


class TestEnterpriseContextManager:
    def test_get_context_empty(self) -> None:
        mgr = EnterpriseContextManager()
        ctx = asyncio.run(mgr.get_context("user", "u1"))
        assert ctx == {}

    def test_set_and_get_attribute(self) -> None:
        mgr = EnterpriseContextManager()
        asyncio.run(mgr.set_attribute("user", "u1", "role", "admin"))
        val = asyncio.run(mgr.get_attribute("user", "u1", "role"))
        assert val == "admin"

    def test_get_attribute_missing(self) -> None:
        mgr = EnterpriseContextManager()
        val = asyncio.run(mgr.get_attribute("user", "u1", "missing"))
        assert val is None

    def test_get_context_with_data(self) -> None:
        mgr = EnterpriseContextManager()
        asyncio.run(mgr.set_attribute("user", "u1", "role", "admin"))
        asyncio.run(mgr.set_attribute("user", "u1", "level", "5"))
        ctx = asyncio.run(mgr.get_context("user", "u1"))
        assert ctx["role"] == "admin"
        assert ctx["level"] == "5"

    def test_clear_context(self) -> None:
        mgr = EnterpriseContextManager()
        asyncio.run(mgr.set_attribute("user", "u1", "role", "admin"))
        asyncio.run(mgr.clear_context("user", "u1"))
        ctx = asyncio.run(mgr.get_context("user", "u1"))
        assert ctx == {}

    def test_get_context_invalid_scope(self) -> None:
        mgr = EnterpriseContextManager()
        try:
            asyncio.run(mgr.get_context("invalid", "x"))
            assert False
        except ValueError:
            pass

    def test_set_attribute_invalid_scope(self) -> None:
        mgr = EnterpriseContextManager()
        try:
            asyncio.run(mgr.set_attribute("invalid", "x", "k", "v"))
            assert False
        except ValueError:
            pass

    def test_propagate_context(self) -> None:
        source = Session(
            id="s1",
            context_snapshot={"memory": "data", "intent": "greet"},
        )
        mgr = EnterpriseContextManager()
        asyncio.run(mgr.propagate_context(source, ["s2", "s3"]))
        ctx2 = asyncio.run(mgr.get_context("execution", "s2"))
        assert ctx2["memory"] == "data"
        assert ctx2["intent"] == "greet"
        ctx3 = asyncio.run(mgr.get_context("execution", "s3"))
        assert ctx3["memory"] == "data"

    def test_propagate_context_with_allowed_attributes(self) -> None:
        source = Session(
            id="s1",
            context_snapshot={"memory": "data", "secret": "hidden"},
        )
        cfg = ContextPropagationConfig(allowed_attributes=["memory"])
        mgr = EnterpriseContextManager()
        asyncio.run(mgr.propagate_context(source, ["s2"], config=cfg))
        ctx = asyncio.run(mgr.get_context("execution", "s2"))
        assert ctx["memory"] == "data"
        assert "secret" not in ctx

    def test_propagate_context_respects_max_depth(self) -> None:
        source = Session(
            id="s1",
            context_snapshot={"a": "1", "b": "2"},
        )
        cfg = ContextPropagationConfig(max_depth=1)
        mgr = EnterpriseContextManager()
        asyncio.run(mgr.propagate_context(source, ["s2", "s3"], config=cfg))
        ctx2 = asyncio.run(mgr.get_context("execution", "s2"))
        assert ctx2["a"] == "1"
        ctx3 = asyncio.run(mgr.get_context("execution", "s3"))
        assert ctx3 == {}

    def test_build_session_context(self) -> None:
        mgr = EnterpriseContextManager()
        asyncio.run(mgr.set_attribute("user", "s1", "role", "admin"))
        asyncio.run(mgr.set_attribute("workflow", "s1", "step", "1"))
        ctx = asyncio.run(mgr.build_session_context("s1"))
        assert isinstance(ctx, SessionContext)
        assert ctx.session_id == "s1"
        assert ctx.attributes["role"] == "admin"
        assert ctx.attributes["step"] == "1"

    def test_build_session_context_empty(self) -> None:
        mgr = EnterpriseContextManager()
        ctx = asyncio.run(mgr.build_session_context("s1"))
        assert ctx.session_id == "s1"
        assert ctx.attributes == {}

    def test_events_published(self) -> None:
        events: list = []
        mgr = EnterpriseContextManager(event_publisher=events.append)
        asyncio.run(mgr.set_attribute("user", "u1", "key", "val"))
        assert len(events) == 1
        assert events[0].key == "key"
        assert events[0].value == "val"
