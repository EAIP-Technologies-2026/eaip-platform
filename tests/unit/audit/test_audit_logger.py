"""Tests for AuditLogger."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from eaip.audit.exceptions import AuditEventNotFoundError
from eaip.audit.logger import AuditLogger
from eaip.audit.models import ActorType, AuditEvent, Severity


class TestAuditLogger:
    async def test_log_event(self) -> None:
        logger = AuditLogger()
        event = AuditEvent(
            id="evt1",
            event_type="user.login",
            actor_id="u1",
            actor_type=ActorType.USER,
            action="login",
            resource_type="session",
            resource_id="sess-1",
        )
        result = await logger.log(event)
        assert result.id == "evt1"
        stored = await logger.get_by_id("evt1")
        assert stored.id == "evt1"

    async def test_log_event_frozen(self) -> None:
        logger = AuditLogger()
        event = AuditEvent(
            id="evt1",
            event_type="test",
            actor_id="u1",
            actor_type=ActorType.SYSTEM,
            action="act",
            resource_type="rt",
            resource_id="ri",
        )
        await logger.log(event)
        stored = await logger.get_by_id("evt1")
        with pytest.raises(ValidationError):
            stored.action = "changed"

    async def test_log_action_convenience(self) -> None:
        logger = AuditLogger()
        event = await logger.log_action(
            actor_id="user-1",
            action="document.update",
            resource_type="document",
            resource_id="doc-123",
        )
        assert event.actor_id == "user-1"
        assert event.action == "document.update"
        assert event.resource_type == "document"
        assert event.resource_id == "doc-123"
        assert event.severity == Severity.INFO
        assert event.event_type == "audit.action"

    async def test_log_action_full(self) -> None:
        logger = AuditLogger()
        event = await logger.log_action(
            actor_id="system-1",
            action="config.change",
            resource_type="config",
            resource_id="cfg-1",
            event_type="audit.config.change",
            actor_type="system",
            details={"key": "value"},
            severity=Severity.HIGH,
            correlation_id="corr-1",
            ip_address="10.0.0.1",
            user_agent="test",
            session_id="sess-1",
            tags=("prod",),
            metadata={"env": "prod"},
        )
        assert event.event_type == "audit.config.change"
        assert event.details == {"key": "value"}
        assert event.severity == Severity.HIGH
        assert event.correlation_id == "corr-1"
        assert event.ip_address == "10.0.0.1"
        assert event.user_agent == "test"
        assert event.session_id == "sess-1"
        assert event.tags == ("prod",)
        assert event.metadata == {"env": "prod"}

    async def test_query_by_event_type(self) -> None:
        logger = AuditLogger()
        events = [
            AuditEvent(
                id=f"e{i}",
                event_type="user.login",
                actor_id="u1",
                actor_type=ActorType.USER,
                action="login",
                resource_type="session",
                resource_id=f"sess-{i}",
            )
            for i in range(3)
        ]
        events.append(
            AuditEvent(
                id="e3",
                event_type="data.update",
                actor_id="u1",
                actor_type=ActorType.USER,
                action="update",
                resource_type="doc",
                resource_id="doc-1",
            )
        )
        for ev in events:
            await logger.log(ev)

        results = await logger.query({"event_type": "user.login"})
        assert len(results) == 3

        results = await logger.query({"event_type": "data.update"})
        assert len(results) == 1

    async def test_query_by_actor_id(self) -> None:
        logger = AuditLogger()
        await logger.log_action(actor_id="u1", action="read", resource_type="doc", resource_id="d1")
        await logger.log_action(
            actor_id="u2", action="write", resource_type="doc", resource_id="d2"
        )
        await logger.log_action(
            actor_id="u1", action="delete", resource_type="doc", resource_id="d3"
        )

        results = await logger.query({"actor_id": "u1"})
        assert len(results) == 2

        results = await logger.query({"actor_id": "u2"})
        assert len(results) == 1

    async def test_query_by_severity(self) -> None:
        logger = AuditLogger()
        await logger.log_action(
            actor_id="u1",
            action="read",
            resource_type="doc",
            resource_id="d1",
            severity=Severity.INFO,
        )
        await logger.log_action(
            actor_id="u2",
            action="write",
            resource_type="doc",
            resource_id="d2",
            severity=Severity.HIGH,
        )

        results = await logger.query({"severity": "high"})
        assert len(results) == 1

    async def test_query_by_correlation_id(self) -> None:
        logger = AuditLogger()
        await logger.log_action(
            actor_id="u1",
            action="read",
            resource_type="doc",
            resource_id="d1",
            correlation_id="corr-x",
        )
        await logger.log_action(
            actor_id="u2",
            action="write",
            resource_type="doc",
            resource_id="d2",
            correlation_id="corr-y",
        )

        results = await logger.query({"correlation_id": "corr-x"})
        assert len(results) == 1

    async def test_query_by_actor_type(self) -> None:
        logger = AuditLogger()
        await logger.log_action(
            actor_id="u1", action="act", resource_type="rt", resource_id="r1", actor_type="user"
        )
        ev = AuditEvent(
            id="evt-sys",
            event_type="sys",
            actor_id="sys-1",
            actor_type=ActorType.SYSTEM,
            action="sys.act",
            resource_type="sys",
            resource_id="sr1",
        )
        await logger.log(ev)

        results = await logger.query({"actor_type": "user"})
        assert len(results) == 1

    async def test_get_by_id_not_found(self) -> None:
        logger = AuditLogger()
        with pytest.raises(AuditEventNotFoundError):
            await logger.get_by_id("nonexistent")

    async def test_get_by_resource(self) -> None:
        logger = AuditLogger()
        await logger.log_action(
            actor_id="u1", action="read", resource_type="doc", resource_id="doc-1"
        )
        await logger.log_action(
            actor_id="u2", action="write", resource_type="doc", resource_id="doc-1"
        )
        await logger.log_action(
            actor_id="u1", action="read", resource_type="report", resource_id="rpt-1"
        )

        results = await logger.get_by_resource("doc", "doc-1")
        assert len(results) == 2

    async def test_get_by_actor(self) -> None:
        logger = AuditLogger()
        await logger.log_action(actor_id="u1", action="read", resource_type="doc", resource_id="d1")
        await logger.log_action(
            actor_id="u1", action="write", resource_type="doc", resource_id="d2"
        )
        await logger.log_action(actor_id="u2", action="read", resource_type="doc", resource_id="d3")

        results = await logger.get_by_actor("u1")
        assert len(results) == 2

    async def test_get_by_timerange(self) -> None:
        logger = AuditLogger()
        now = datetime.now(UTC)
        past = now - timedelta(days=10)
        future = now + timedelta(days=10)

        ev1 = AuditEvent(
            id="e1",
            event_type="t",
            actor_id="u1",
            actor_type=ActorType.USER,
            action="act",
            resource_type="rt",
            resource_id="r1",
            timestamp=past,
        )
        ev2 = AuditEvent(
            id="e2",
            event_type="t",
            actor_id="u2",
            actor_type=ActorType.USER,
            action="act",
            resource_type="rt",
            resource_id="r2",
        )
        await logger.log(ev1)
        await logger.log(ev2)

        results = await logger.get_by_timerange(now, future)
        assert len(results) == 1
        assert results[0].id == "e2"

        results = await logger.get_by_timerange(past - timedelta(days=1), past + timedelta(days=1))
        assert len(results) == 1
        assert results[0].id == "e1"

    async def test_export_json(self) -> None:
        logger = AuditLogger()
        await logger.log_action(actor_id="u1", action="read", resource_type="doc", resource_id="d1")
        events = await logger.get_by_actor("u1")
        exported = await logger.export(events, format="json")
        assert isinstance(exported, list)
        assert len(exported) == 1
        assert exported[0]["actor_id"] == "u1"

    async def test_export_dict(self) -> None:
        logger = AuditLogger()
        await logger.log_action(actor_id="u1", action="read", resource_type="doc", resource_id="d1")
        events = await logger.get_by_actor("u1")
        exported = await logger.export(events, format="dict")
        assert isinstance(exported, list)
        assert len(exported) == 1

    async def test_export_invalid_format(self) -> None:
        logger = AuditLogger()
        await logger.log_action(actor_id="u1", action="read", resource_type="doc", resource_id="d1")
        events = await logger.get_by_actor("u1")
        with pytest.raises(ValueError):
            await logger.export(events, format="xml")
