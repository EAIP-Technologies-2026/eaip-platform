"""Tests for SessionManager."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from eaip.session.exceptions import SessionExpiredError, SessionLimitError, SessionNotFoundError
from eaip.session.manager import SessionManager
from eaip.session.models import SessionConfig, SessionStatus, SessionType


class TestSessionManager:
    def test_create_session(self) -> None:
        mgr = SessionManager()
        s = asyncio.run(mgr.create_session("user", user_id="u1"))
        assert s.id is not None
        assert s.type is SessionType.USER
        assert s.status is SessionStatus.ACTIVE
        assert s.user_id == "u1"

    def test_create_session_with_type(self) -> None:
        mgr = SessionManager()
        s = asyncio.run(mgr.create_session("workflow", workflow_id="wf1"))
        assert s.type is SessionType.WORKFLOW
        assert s.workflow_id == "wf1"

    def test_create_session_with_ttl(self) -> None:
        mgr = SessionManager()
        s = asyncio.run(mgr.create_session("user", ttl_seconds=60))
        assert s.ttl_seconds == 60
        assert s.expires_at is not None

    def test_get_session(self) -> None:
        mgr = SessionManager()
        created = asyncio.run(mgr.create_session("user"))
        fetched = asyncio.run(mgr.get_session(created.id))
        assert fetched.id == created.id

    def test_get_session_not_found(self) -> None:
        mgr = SessionManager()
        try:
            asyncio.run(mgr.get_session("nonexistent"))
            raise AssertionError()
        except SessionNotFoundError:
            pass

    def test_get_session_expired(self) -> None:
        mgr = SessionManager()
        s = asyncio.run(mgr.create_session("user"))
        asyncio.run(mgr.expire_session(s.id))
        try:
            asyncio.run(mgr.get_session(s.id))
            raise AssertionError()
        except SessionExpiredError:
            pass

    def test_update_session(self) -> None:
        mgr = SessionManager()
        s = asyncio.run(mgr.create_session("user"))
        updated = asyncio.run(mgr.update_session(s.id, {"metadata": {"key": "val"}}))
        assert updated.metadata["key"] == "val"
        assert updated.updated_at > s.updated_at

    def test_close_session(self) -> None:
        mgr = SessionManager()
        s = asyncio.run(mgr.create_session("user"))
        closed = asyncio.run(mgr.close_session(s.id))
        assert closed.status is SessionStatus.CLOSED

    def test_suspend_session(self) -> None:
        mgr = SessionManager()
        s = asyncio.run(mgr.create_session("user"))
        suspended = asyncio.run(mgr.suspend_session(s.id))
        assert suspended.status is SessionStatus.SUSPENDED

    def test_resume_session(self) -> None:
        mgr = SessionManager()
        s = asyncio.run(mgr.create_session("user"))
        asyncio.run(mgr.suspend_session(s.id))
        resumed = asyncio.run(mgr.resume_session(s.id))
        assert resumed.status is SessionStatus.ACTIVE

    def test_resume_non_suspended_noop(self) -> None:
        mgr = SessionManager()
        s = asyncio.run(mgr.create_session("user"))
        result = asyncio.run(mgr.resume_session(s.id))
        assert result.status is SessionStatus.ACTIVE

    def test_expire_session(self) -> None:
        mgr = SessionManager()
        s = asyncio.run(mgr.create_session("user"))
        expired = asyncio.run(mgr.expire_session(s.id))
        assert expired.status is SessionStatus.EXPIRED

    def test_list_sessions_no_filter(self) -> None:
        mgr = SessionManager()
        asyncio.run(mgr.create_session("user", user_id="u1"))
        asyncio.run(mgr.create_session("user", user_id="u2"))
        all_s = asyncio.run(mgr.list_sessions())
        assert len(all_s) == 2

    def test_list_sessions_by_type(self) -> None:
        mgr = SessionManager()
        asyncio.run(mgr.create_session("user"))
        asyncio.run(mgr.create_session("workflow"))
        results = asyncio.run(mgr.list_sessions(type="workflow"))
        assert len(results) == 1
        assert results[0].type is SessionType.WORKFLOW

    def test_list_sessions_by_status(self) -> None:
        mgr = SessionManager()
        s = asyncio.run(mgr.create_session("user"))
        asyncio.run(mgr.close_session(s.id))
        results = asyncio.run(mgr.list_sessions(status="closed"))
        assert len(results) == 1
        assert results[0].status is SessionStatus.CLOSED

    def test_list_sessions_by_tenant(self) -> None:
        mgr = SessionManager()
        asyncio.run(mgr.create_session("user", tenant_id="t1"))
        asyncio.run(mgr.create_session("user", tenant_id="t2"))
        results = asyncio.run(mgr.list_sessions(tenant_id="t1"))
        assert len(results) == 1

    def test_list_sessions_by_user(self) -> None:
        mgr = SessionManager()
        asyncio.run(mgr.create_session("user", user_id="u1"))
        asyncio.run(mgr.create_session("user", user_id="u2"))
        results = asyncio.run(mgr.list_sessions(user_id="u1"))
        assert len(results) == 1

    def test_get_active_sessions(self) -> None:
        mgr = SessionManager()
        s1 = asyncio.run(mgr.create_session("user"))
        s2 = asyncio.run(mgr.create_session("user"))
        asyncio.run(mgr.close_session(s1.id))
        active = asyncio.run(mgr.get_active_sessions())
        assert len(active) == 1
        assert active[0].id == s2.id

    def test_get_active_sessions_by_user(self) -> None:
        mgr = SessionManager()
        asyncio.run(mgr.create_session("user", user_id="u1"))
        asyncio.run(mgr.create_session("user", user_id="u2"))
        active = asyncio.run(mgr.get_active_sessions(user_id="u1"))
        assert len(active) == 1

    def test_session_limit(self) -> None:
        cfg = SessionConfig(max_sessions_per_user=1)
        mgr = SessionManager(config=cfg)
        asyncio.run(mgr.create_session("user", user_id="u1"))
        try:
            asyncio.run(mgr.create_session("user", user_id="u1"))
            raise AssertionError()
        except SessionLimitError:
            pass

    def test_config_property(self) -> None:
        cfg = SessionConfig(default_ttl_seconds=7200)
        mgr = SessionManager(config=cfg)
        assert mgr.config.default_ttl_seconds == 7200

    def test_expire_stale_sessions(self) -> None:
        datetime.now() - timedelta(hours=1)
        mgr = SessionManager()
        asyncio.run(mgr.create_session("user", ttl_seconds=1))
        count = asyncio.run(mgr._expire_stale_sessions())
        assert count == 0
