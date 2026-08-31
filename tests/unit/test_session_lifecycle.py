"""Tests for SessionLifecycleManager."""

from __future__ import annotations

import asyncio

from eaip.session.lifecycle import SessionLifecycleManager
from eaip.session.manager import SessionManager


class TestSessionLifecycleManager:
    def test_run_expiry_cycle(self) -> None:
        mgr = SessionManager()
        lcm = SessionLifecycleManager(mgr)
        count = asyncio.run(lcm.run_expiry_cycle())
        assert count == 0

    def test_cleanup_tenant(self) -> None:
        mgr = SessionManager()
        asyncio.run(mgr.create_session("user", tenant_id="t1"))
        asyncio.run(mgr.create_session("user", tenant_id="t1"))
        asyncio.run(mgr.create_session("user", tenant_id="t2"))
        lcm = SessionLifecycleManager(mgr)
        count = asyncio.run(lcm.cleanup_tenant("t1"))
        assert count == 2
        remaining = asyncio.run(mgr.list_sessions(status="active"))
        assert len(remaining) == 1
        assert remaining[0].tenant_id == "t2"

    def test_cleanup_tenant_no_sessions(self) -> None:
        mgr = SessionManager()
        lcm = SessionLifecycleManager(mgr)
        count = asyncio.run(lcm.cleanup_tenant("nonexistent"))
        assert count == 0

    def test_transfer_session(self) -> None:
        mgr = SessionManager()
        s = asyncio.run(mgr.create_session("user", user_id="u1"))
        lcm = SessionLifecycleManager(mgr)
        transferred = asyncio.run(lcm.transfer_session(s.id, "u2"))
        assert transferred.user_id == "u2"

    def test_transfer_session_publishes_event(self) -> None:
        events: list = []
        mgr = SessionManager()
        s = asyncio.run(mgr.create_session("user", user_id="u1"))
        lcm = SessionLifecycleManager(mgr, event_publisher=events.append)
        asyncio.run(lcm.transfer_session(s.id, "u2"))
        assert len(events) == 1
        assert events[0].source_user_id == "u1"
        assert events[0].target_user_id == "u2"

    def test_merge_sessions(self) -> None:
        mgr = SessionManager()
        s1 = asyncio.run(
            mgr.create_session(
                "user",
                user_id="u1",
                metadata={"role": "admin"},
                tags=("a",),
            )
        )
        s2 = asyncio.run(
            mgr.create_session(
                "user",
                user_id="u1",
                metadata={"team": "alpha"},
                tags=("b",),
            )
        )
        lcm = SessionLifecycleManager(mgr)
        merged = asyncio.run(lcm.merge_sessions(s1.id, s2.id))
        assert merged.metadata["role"] == "admin"
        assert merged.metadata["team"] == "alpha"
        assert "a" in merged.tags
        assert "b" in merged.tags
        source = asyncio.run(mgr.list_sessions(status="closed"))
        assert len(source) == 1

    def test_merge_sessions_tags_union(self) -> None:
        mgr = SessionManager()
        s1 = asyncio.run(mgr.create_session("user", tags=("x", "y")))
        s2 = asyncio.run(mgr.create_session("user", tags=("y", "z")))
        lcm = SessionLifecycleManager(mgr)
        merged = asyncio.run(lcm.merge_sessions(s1.id, s2.id))
        assert set(merged.tags) == {"x", "y", "z"}
