"""Tests for SessionSerializer."""

from __future__ import annotations

from datetime import datetime

from eaip.session.models import Session, SessionContext, SessionStatus, SessionType
from eaip.session.serialization import SessionSerializer


class TestSessionSerializer:
    def test_serialize_session(self) -> None:
        s = Session(
            id="s1",
            type=SessionType.USER,
            status=SessionStatus.ACTIVE,
            tenant_id="t1",
            user_id="u1",
            tags=("a", "b"),
            metadata={"env": "prod"},
            context_snapshot={"mem": "val"},
        )
        ser = SessionSerializer()
        data = ser.serialize(s)
        assert data["id"] == "s1"
        assert data["type"] == "user"
        assert data["status"] == "active"
        assert data["tenant_id"] == "t1"
        assert data["user_id"] == "u1"
        assert data["tags"] == ["a", "b"]
        assert data["metadata"]["env"] == "prod"
        assert data["context_snapshot"]["mem"] == "val"
        assert isinstance(data["created_at"], str)

    def test_serialize_session_with_expires(self) -> None:
        s = Session(id="s1", ttl_seconds=300, expires_at=datetime.now())
        ser = SessionSerializer()
        data = ser.serialize(s)
        assert data["ttl_seconds"] == 300
        assert isinstance(data["expires_at"], str)

    def test_deserialize_session(self) -> None:
        data = {
            "id": "s1",
            "type": "workflow",
            "status": "suspended",
            "created_at": "2025-01-01T00:00:00+00:00",
            "updated_at": "2025-01-01T00:00:00+00:00",
            "expires_at": None,
            "ttl_seconds": None,
            "tenant_id": "t1",
            "user_id": None,
            "workflow_id": "wf1",
            "metadata": {},
            "tags": ["urgent"],
            "parent_session_id": None,
            "context_snapshot": {},
        }
        ser = SessionSerializer()
        s = ser.deserialize(data)
        assert s.id == "s1"
        assert s.type is SessionType.WORKFLOW
        assert s.status is SessionStatus.SUSPENDED
        assert s.tenant_id == "t1"
        assert s.workflow_id == "wf1"
        assert s.tags == ("urgent",)

    def test_roundtrip(self) -> None:
        original = Session(
            id="s1",
            type=SessionType.AGENT,
            status=SessionStatus.ACTIVE,
            tenant_id="t1",
            user_id="u1",
            tags=("fast", "prod"),
            metadata={"region": "us-east"},
            context_snapshot={"key": "value"},
        )
        ser = SessionSerializer()
        data = ser.serialize(original)
        restored = ser.deserialize(data)
        assert restored.id == original.id
        assert restored.type is original.type
        assert restored.status is original.status
        assert restored.tags == original.tags
        assert restored.metadata == original.metadata
        assert restored.context_snapshot == original.context_snapshot

    def test_export_context(self) -> None:
        ctx = SessionContext(
            session_id="s1",
            correlation_id="corr-1",
            tenant_id="t1",
            user_id="u1",
            attributes={"role": "admin"},
        )
        ser = SessionSerializer()
        data = ser.export_context(ctx)
        assert data["session_id"] == "s1"
        assert data["correlation_id"] == "corr-1"
        assert data["tenant_id"] == "t1"
        assert data["user_id"] == "u1"
        assert data["attributes"]["role"] == "admin"
        assert isinstance(data["created_at"], str)

    def test_import_context(self) -> None:
        data = {
            "session_id": "s1",
            "correlation_id": "corr-1",
            "tenant_id": "t1",
            "user_id": "u1",
            "workflow_id": None,
            "attributes": {"role": "admin"},
            "created_at": "2025-01-01T00:00:00+00:00",
        }
        ser = SessionSerializer()
        ctx = ser.import_context(data)
        assert ctx.session_id == "s1"
        assert ctx.correlation_id == "corr-1"
        assert ctx.tenant_id == "t1"
        assert ctx.user_id == "u1"
        assert ctx.attributes["role"] == "admin"

    def test_context_roundtrip(self) -> None:
        original = SessionContext(
            session_id="s1",
            correlation_id="corr-1",
            tenant_id="t1",
            user_id="u1",
            workflow_id="wf1",
            attributes={"region": "eu", "priority": 1},
        )
        ser = SessionSerializer()
        data = ser.export_context(original)
        restored = ser.import_context(data)
        assert restored.session_id == original.session_id
        assert restored.correlation_id == original.correlation_id
        assert restored.attributes == original.attributes

    def test_deserialize_handles_datetime_obj(self) -> None:
        now = datetime.now()
        data = {
            "id": "s1",
            "type": "user",
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "expires_at": None,
            "ttl_seconds": None,
            "tenant_id": None,
            "user_id": None,
            "workflow_id": None,
            "metadata": {},
            "tags": [],
            "parent_session_id": None,
            "context_snapshot": {},
        }
        ser = SessionSerializer()
        s = ser.deserialize(data)
        assert s.id == "s1"
