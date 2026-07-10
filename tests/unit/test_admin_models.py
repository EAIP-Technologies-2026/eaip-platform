"""Tests for :mod:`eaip.admin.models`."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from eaip.admin.models import AdminAction, AdminCapability, AuditEntry, AuditOutcome, RuntimeSnapshot


class TestAdminAction:
    def test_minimal(self) -> None:
        action = AdminAction(
            action_id="act-1",
            action_type="restart",
            target="runtime",
            performed_by="admin",
        )
        assert action.action_id == "act-1"
        assert action.action_type == "restart"
        assert action.result == "pending"
        assert isinstance(action.timestamp, datetime)

    def test_frozen(self) -> None:
        action = AdminAction(
            action_id="act-1",
            action_type="restart",
            target="runtime",
            performed_by="admin",
        )
        with pytest.raises(ValueError):  # noqa: PT011
            action.action_id = "changed"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValueError):  # noqa: PT011
            AdminAction(  # type: ignore[call-arg]
                action_id="a",
                action_type="t",
                target="t",
                performed_by="u",
                unknown_field="x",
            )

    def test_with_details(self) -> None:
        action = AdminAction(
            action_id="act-2",
            action_type="deploy",
            target="plugin:foo",
            performed_by="bot",
            details={"version": "1.0"},
            result="success",
        )
        assert action.details == {"version": "1.0"}
        assert action.result == "success"


class TestAuditEntry:
    def test_minimal(self) -> None:
        entry = AuditEntry(
            id="entry-1",
            actor_id="user-1",
            action="create",
            resource_type="plugin",
            resource_id="plugin-x",
            outcome=AuditOutcome.SUCCESS,
        )
        assert entry.id == "entry-1"
        assert entry.outcome is AuditOutcome.SUCCESS
        assert entry.correlation_id is None

    def test_frozen(self) -> None:
        entry = AuditEntry(
            id="e1",
            actor_id="u1",
            action="delete",
            resource_type="config",
            resource_id="cfg-1",
            outcome=AuditOutcome.FAILURE,
        )
        with pytest.raises(ValueError):  # noqa: PT011
            entry.id = "changed"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValueError):  # noqa: PT011
            AuditEntry(  # type: ignore[call-arg]
                id="e1",
                actor_id="u1",
                action="read",
                resource_type="log",
                resource_id="log-1",
                outcome=AuditOutcome.SUCCESS,
                bad_key="nope",
            )

    def test_with_correlation_id(self) -> None:
        entry = AuditEntry(
            id="e2",
            actor_id="u2",
            action="update",
            resource_type="capability",
            resource_id="cap-a",
            outcome=AuditOutcome.FAILURE,
            correlation_id="corr-123",
            details={"reason": "permission denied"},
        )
        assert entry.correlation_id == "corr-123"
        assert entry.details == {"reason": "permission denied"}


class TestRuntimeSnapshot:
    def test_minimal(self) -> None:
        snap = RuntimeSnapshot()
        assert snap.health_status == "unknown"
        assert snap.active_modules == []
        assert snap.active_capabilities == []
        assert snap.uptime_seconds == 0.0
        assert isinstance(snap.collected_at, datetime)

    def test_with_values(self) -> None:
        snap = RuntimeSnapshot(
            component_states={"http": "healthy", "db": "degraded"},
            health_status="degraded",
            active_modules=["http", "events"],
            active_capabilities=["logging", "metrics"],
            uptime_seconds=3600.0,
        )
        assert snap.component_states["http"] == "healthy"
        assert snap.health_status == "degraded"
        assert snap.uptime_seconds == 3600.0

    def test_frozen(self) -> None:
        snap = RuntimeSnapshot()
        with pytest.raises(ValueError):  # noqa: PT011
            snap.health_status = "healthy"  # type: ignore[misc]


class TestAdminCapability:
    def test_minimal(self) -> None:
        cap = AdminCapability(id="cap-1", name="audit.view")
        assert cap.description == ""
        assert cap.required_role == "admin"
        assert cap.enabled is True

    def test_with_all_fields(self) -> None:
        cap = AdminCapability(
            id="cap-2",
            name="config.edit",
            description="Edit configuration values",
            required_role="superadmin",
            enabled=False,
        )
        assert cap.name == "config.edit"
        assert cap.required_role == "superadmin"
        assert cap.enabled is False

    def test_frozen(self) -> None:
        cap = AdminCapability(id="c1", name="test")
        with pytest.raises(ValueError):  # noqa: PT011
            cap.name = "other"  # type: ignore[misc]
