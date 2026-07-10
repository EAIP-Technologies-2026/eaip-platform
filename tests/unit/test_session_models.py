"""Tests for session models."""

from __future__ import annotations

from datetime import datetime, timedelta

from eaip.session.models import (
    ContextPropagationConfig,
    ContextScope,
    ExecutionContext,
    Session,
    SessionConfig,
    SessionContext,
    SessionStatus,
    SessionType,
)


class TestSession:
    def test_defaults(self) -> None:
        s = Session(id="s1")
        assert s.id == "s1"
        assert s.type is SessionType.USER
        assert s.status is SessionStatus.ACTIVE
        assert s.metadata == {}
        assert s.tags == ()
        assert s.context_snapshot == {}

    def test_with_all_fields(self) -> None:
        now = datetime.now()
        s = Session(
            id="s2",
            type=SessionType.WORKFLOW,
            status=SessionStatus.SUSPENDED,
            tenant_id="tenant-1",
            user_id="user-1",
            workflow_id="wf-1",
            metadata={"key": "val"},
            tags=("urgent", "prod"),
            parent_session_id="s1",
            context_snapshot={"memory": "snapshot"},
            ttl_seconds=300,
            expires_at=now + timedelta(seconds=300),
            created_at=now,
            updated_at=now,
        )
        assert s.id == "s2"
        assert s.type is SessionType.WORKFLOW
        assert s.status is SessionStatus.SUSPENDED
        assert s.tenant_id == "tenant-1"
        assert s.user_id == "user-1"
        assert s.workflow_id == "wf-1"
        assert s.metadata["key"] == "val"
        assert s.tags == ("urgent", "prod")
        assert s.parent_session_id == "s1"
        assert s.context_snapshot["memory"] == "snapshot"
        assert s.ttl_seconds == 300

    def test_frozen(self) -> None:
        s = Session(id="s1")
        try:
            s.id = "s2"
            assert False
        except Exception:
            pass

    def test_extra_forbidden(self) -> None:
        try:
            Session(id="s1", unknown_field="x")  # type: ignore[call-arg]
            assert False
        except Exception:
            pass


class TestSessionContext:
    def test_defaults(self) -> None:
        ctx = SessionContext(session_id="s1")
        assert ctx.session_id == "s1"
        assert ctx.attributes == {}

    def test_with_fields(self) -> None:
        ctx = SessionContext(
            session_id="s1",
            correlation_id="corr-1",
            tenant_id="tenant-1",
            user_id="user-1",
            workflow_id="wf-1",
            attributes={"role": "admin"},
        )
        assert ctx.correlation_id == "corr-1"
        assert ctx.tenant_id == "tenant-1"
        assert ctx.user_id == "user-1"
        assert ctx.workflow_id == "wf-1"
        assert ctx.attributes["role"] == "admin"

    def test_frozen(self) -> None:
        ctx = SessionContext(session_id="s1")
        try:
            ctx.session_id = "s2"
            assert False
        except Exception:
            pass


class TestContextScope:
    def test_values(self) -> None:
        assert ContextScope.ENTERPRISE.value == "enterprise"
        assert ContextScope.TENANT.value == "tenant"
        assert ContextScope.USER.value == "user"
        assert ContextScope.WORKFLOW.value == "workflow"
        assert ContextScope.AGENT.value == "agent"
        assert ContextScope.EXECUTION.value == "execution"

    def test_members(self) -> None:
        assert len(ContextScope) == 6


class TestContextPropagationConfig:
    def test_defaults(self) -> None:
        cfg = ContextPropagationConfig()
        assert cfg.propagate_to_children is True
        assert cfg.propagate_to_agents is False
        assert cfg.propagate_to_workflows is True
        assert cfg.max_depth == 5
        assert cfg.allowed_attributes == []

    def test_custom(self) -> None:
        cfg = ContextPropagationConfig(
            propagate_to_children=False,
            propagate_to_agents=True,
            max_depth=3,
            allowed_attributes=["attr1"],
        )
        assert cfg.propagate_to_children is False
        assert cfg.propagate_to_agents is True
        assert cfg.max_depth == 3
        assert cfg.allowed_attributes == ["attr1"]

    def test_frozen(self) -> None:
        cfg = ContextPropagationConfig()
        try:
            cfg.max_depth = 10
            assert False
        except Exception:
            pass


class TestSessionConfig:
    def test_defaults(self) -> None:
        cfg = SessionConfig()
        assert cfg.default_ttl_seconds == 3600
        assert cfg.max_sessions_per_user == 100
        assert cfg.enable_auto_expiry is True
        assert cfg.enable_persistence is False

    def test_custom(self) -> None:
        cfg = SessionConfig(
            default_ttl_seconds=7200,
            max_sessions_per_user=50,
            enable_auto_expiry=False,
            enable_persistence=True,
        )
        assert cfg.default_ttl_seconds == 7200
        assert cfg.max_sessions_per_user == 50
        assert cfg.enable_auto_expiry is False
        assert cfg.enable_persistence is True


class TestExecutionContext:
    def test_defaults(self) -> None:
        ec = ExecutionContext(id="e1", name="test-exec", session_id="s1")
        assert ec.id == "e1"
        assert ec.name == "test-exec"
        assert ec.session_id == "s1"
        assert ec.parent_id is None
        assert ec.scope is ContextScope.EXECUTION
        assert ec.attributes == {}

    def test_with_all_fields(self) -> None:
        ec = ExecutionContext(
            id="e2",
            name="child-exec",
            session_id="s1",
            parent_id="e1",
            scope=ContextScope.WORKFLOW,
            attributes={"retry_count": 3},
        )
        assert ec.parent_id == "e1"
        assert ec.scope is ContextScope.WORKFLOW
        assert ec.attributes["retry_count"] == 3

    def test_frozen(self) -> None:
        ec = ExecutionContext(id="e1", name="test", session_id="s1")
        try:
            ec.name = "changed"
            assert False
        except Exception:
            pass


class TestSessionType:
    def test_values(self) -> None:
        assert SessionType.USER.value == "user"
        assert SessionType.WORKFLOW.value == "workflow"
        assert SessionType.AGENT.value == "agent"
        assert SessionType.SYSTEM.value == "system"


class TestSessionStatus:
    def test_values(self) -> None:
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.SUSPENDED.value == "suspended"
        assert SessionStatus.EXPIRED.value == "expired"
        assert SessionStatus.CLOSED.value == "closed"
