"""SessionManager — in-memory session lifecycle management with TTL-based expiry."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from eaip.logging.context import get_logger
from eaip.session.events import (
    SessionClosed,
    SessionCreated,
    SessionExpired,
    SessionResumed,
    SessionSuspended,
    SessionUpdated,
)
from eaip.session.exceptions import SessionExpiredError, SessionLimitError, SessionNotFoundError
from eaip.session.models import Session, SessionConfig, SessionStatus, SessionType
from eaip.shared.time import utc_now


class SessionManager:
    """Manages session lifecycle with an in-memory store and TTL-based expiry.

    Provides create, read, update, close, suspend, resume, and expire
    operations, along with filtering and event publishing.
    """

    def __init__(
        self,
        config: SessionConfig | None = None,
        event_publisher: Any = None,
    ) -> None:
        """Initialize the SessionManager.

        Args:
            config: Optional SessionConfig; defaults to stock settings.
            event_publisher: Optional callable for publishing domain events.
        """
        self._config = config or SessionConfig()
        self._event_publisher = event_publisher or (lambda _: None)
        self._sessions: dict[str, Session] = {}
        self._log = get_logger("eaip.session.manager")

    @property
    def config(self) -> SessionConfig:
        """Return the current configuration."""
        return self._config

    async def create_session(
        self,
        session_type: str = "user",
        **kwargs: Any,
    ) -> Session:
        """Create a new session.

        Args:
            session_type: One of "user", "workflow", "agent", "system".
            **kwargs: Additional session fields (tenant_id, user_id, etc.).

        Returns:
            The newly created Session.

        Raises:
            SessionLimitError: If user has exceeded max sessions.
        """
        uid = str(uuid.uuid4())
        now = utc_now()

        session_type_enum = SessionType(session_type)
        user_id = kwargs.get("user_id")

        if user_id and self._config.max_sessions_per_user > 0:
            user_active = await self.get_active_sessions(user_id=user_id)
            if len(user_active) >= self._config.max_sessions_per_user:
                raise SessionLimitError(
                    f"User {user_id} has reached the maximum of "
                    f"{self._config.max_sessions_per_user} active sessions"
                )

        ttl = kwargs.pop("ttl_seconds", self._config.default_ttl_seconds)
        expires_at: datetime | None = None
        if ttl is not None:
            expires_at = now + timedelta(seconds=ttl)

        session = Session(
            id=uid,
            type=session_type_enum,
            tenant_id=kwargs.pop("tenant_id", None),
            user_id=user_id,
            workflow_id=kwargs.pop("workflow_id", None),
            parent_session_id=kwargs.pop("parent_session_id", None),
            metadata=kwargs.pop("metadata", {}),
            tags=tuple(kwargs.pop("tags", ())),
            context_snapshot=kwargs.pop("context_snapshot", {}),
            ttl_seconds=ttl,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
        )

        self._sessions[uid] = session

        self._event_publisher(
            SessionCreated(
                session_id=uid,
                session_type=session_type,
                tenant_id=session.tenant_id,
                user_id=session.user_id,
            )
        )

        self._log.info("session.created", session_id=uid, session_type=session_type)
        return session

    async def get_session(self, session_id: str) -> Session:
        """Get a session by ID.

        Args:
            session_id: The session identifier.

        Returns:
            The matching Session.

        Raises:
            SessionNotFoundError: If the session does not exist.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session {session_id!r} not found")
        if session.status is SessionStatus.EXPIRED:
            raise SessionExpiredError(f"Session {session_id!r} has expired")
        return session

    async def update_session(self, session_id: str, updates: dict[str, Any]) -> Session:
        """Update session attributes.

        Args:
            session_id: The session identifier.
            updates: Dictionary of fields to update.

        Returns:
            The updated Session.
        """
        session = await self.get_session(session_id)

        allowed_updates = {
            "metadata",
            "tags",
            "context_snapshot",
            "ttl_seconds",
            "expires_at",
            "workflow_id",
            "user_id",
        }
        filtered = {k: v for k, v in updates.items() if k in allowed_updates}

        if "tags" in filtered:
            filtered["tags"] = tuple(filtered["tags"])

        new_data = session.model_dump()
        new_data.update(filtered)
        new_data["updated_at"] = utc_now()

        updated = Session(**new_data)
        self._sessions[session_id] = updated

        self._event_publisher(SessionUpdated(session_id=session_id, changes=filtered))

        self._log.info("session.updated", session_id=session_id)
        return updated

    async def close_session(self, session_id: str) -> Session:
        """Close a session.

        Args:
            session_id: The session identifier.

        Returns:
            The closed Session.
        """
        session = await self.get_session(session_id)
        new_data = session.model_dump()
        new_data["status"] = SessionStatus.CLOSED
        new_data["updated_at"] = utc_now()
        closed = Session(**new_data)
        self._sessions[session_id] = closed

        self._event_publisher(SessionClosed(session_id=session_id))
        self._log.info("session.closed", session_id=session_id)
        return closed

    async def suspend_session(self, session_id: str) -> Session:
        """Suspend a session.

        Args:
            session_id: The session identifier.

        Returns:
            The suspended Session.
        """
        session = await self.get_session(session_id)
        new_data = session.model_dump()
        new_data["status"] = SessionStatus.SUSPENDED
        new_data["updated_at"] = utc_now()
        suspended = Session(**new_data)
        self._sessions[session_id] = suspended

        self._event_publisher(SessionSuspended(session_id=session_id))
        self._log.info("session.suspended", session_id=session_id)
        return suspended

    async def resume_session(self, session_id: str) -> Session:
        """Resume a suspended session.

        Args:
            session_id: The session identifier.

        Returns:
            The resumed Session.
        """
        session = await self.get_session(session_id)
        if session.status is not SessionStatus.SUSPENDED:
            return session
        new_data = session.model_dump()
        new_data["status"] = SessionStatus.ACTIVE
        new_data["updated_at"] = utc_now()
        resumed = Session(**new_data)
        self._sessions[session_id] = resumed

        self._event_publisher(SessionResumed(session_id=session_id))
        self._log.info("session.resumed", session_id=session_id)
        return resumed

    async def expire_session(self, session_id: str) -> Session:
        """Expire a session.

        Args:
            session_id: The session identifier.

        Returns:
            The expired Session.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session {session_id!r} not found")
        new_data = session.model_dump()
        new_data["status"] = SessionStatus.EXPIRED
        new_data["updated_at"] = utc_now()
        expired = Session(**new_data)
        self._sessions[session_id] = expired

        self._event_publisher(SessionExpired(session_id=session_id))
        self._log.info("session.expired", session_id=session_id)
        return expired

    async def list_sessions(
        self,
        type: str | None = None,
        status: str | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
    ) -> list[Session]:
        """List sessions with optional filters.

        Args:
            type: Optional session type filter.
            status: Optional session status filter.
            tenant_id: Optional tenant ID filter.
            user_id: Optional user ID filter.

        Returns:
            A list of matching Session objects.
        """
        results: list[Session] = list(self._sessions.values())

        if type is not None:
            results = [s for s in results if s.type.value == type]

        if status is not None:
            results = [s for s in results if s.status.value == status]

        if tenant_id is not None:
            results = [s for s in results if s.tenant_id == tenant_id]

        if user_id is not None:
            results = [s for s in results if s.user_id == user_id]

        return results

    async def get_active_sessions(self, user_id: str | None = None) -> list[Session]:
        """Get all active sessions, optionally filtered by user.

        Args:
            user_id: Optional user ID filter.

        Returns:
            A list of active Session objects.
        """
        results = [s for s in self._sessions.values() if s.status is SessionStatus.ACTIVE]

        if user_id is not None:
            results = [s for s in results if s.user_id == user_id]

        return results

    async def _expire_stale_sessions(self) -> int:
        """Expire sessions whose TTL has elapsed.

        Returns:
            The number of sessions expired.
        """
        now = utc_now()
        expired_count = 0
        for sid, session in list(self._sessions.items()):
            if (
                session.status is SessionStatus.ACTIVE
                and session.expires_at is not None
                and now >= session.expires_at
            ):
                await self.expire_session(sid)
                expired_count += 1
        return expired_count

    def _session_count(self) -> int:
        """Return the total number of sessions in the store."""
        return len(self._sessions)


__all__ = ["SessionManager"]
