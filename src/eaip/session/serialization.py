"""SessionSerializer — serialize and deserialize sessions and contexts for transfer."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eaip.logging.context import get_logger
from eaip.session.models import Session, SessionContext, SessionStatus, SessionType


class SessionSerializer:
    """Serializes and deserializes Session and SessionContext objects."""

    def __init__(self) -> None:
        """Initialize the SessionSerializer."""
        self._log = get_logger("eaip.session.serialization")

    def serialize(self, session: Session) -> dict[str, Any]:
        """Serialize a Session to a JSON-safe dictionary.

        Args:
            session: The Session to serialize.

        Returns:
            A dictionary representation of the session.
        """
        return {
            "id": session.id,
            "type": session.type.value,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            "ttl_seconds": session.ttl_seconds,
            "tenant_id": session.tenant_id,
            "user_id": session.user_id,
            "workflow_id": session.workflow_id,
            "metadata": dict(session.metadata),
            "tags": list(session.tags),
            "parent_session_id": session.parent_session_id,
            "context_snapshot": dict(session.context_snapshot),
        }

    def deserialize(self, data: dict[str, Any]) -> Session:
        """Deserialize a dictionary into a Session.

        Args:
            data: A dictionary representation of a session.

        Returns:
            A Session object.
        """
        raw = dict(data)

        def _parse_dt(val: Any) -> datetime | None:
            if isinstance(val, str):
                return datetime.fromisoformat(val)
            if isinstance(val, datetime):
                return val
            return None

        raw["type"] = SessionType(raw.get("type", "user"))
        raw["status"] = SessionStatus(raw.get("status", "active"))

        for field in ("created_at", "updated_at", "expires_at"):
            raw[field] = _parse_dt(raw.get(field))

        if "tags" in raw and isinstance(raw["tags"], list):
            raw["tags"] = tuple(raw["tags"])

        return Session(**raw)

    def export_context(self, session_context: SessionContext) -> dict[str, Any]:
        """Export a SessionContext as a JSON-safe dictionary for transfer.

        Args:
            session_context: The SessionContext to export.

        Returns:
            A dictionary suitable for serialization.
        """
        return {
            "session_id": session_context.session_id,
            "correlation_id": session_context.correlation_id,
            "tenant_id": session_context.tenant_id,
            "user_id": session_context.user_id,
            "workflow_id": session_context.workflow_id,
            "attributes": dict(session_context.attributes),
            "created_at": session_context.created_at.isoformat(),
        }

    def import_context(self, data: dict[str, Any]) -> SessionContext:
        """Import a dictionary into a SessionContext.

        Args:
            data: A dictionary representation of a session context.

        Returns:
            A SessionContext object.
        """
        raw = dict(data)

        created = raw.get("created_at")
        if isinstance(created, str):
            raw["created_at"] = datetime.fromisoformat(created)

        return SessionContext(**raw)


__all__ = ["SessionSerializer"]
