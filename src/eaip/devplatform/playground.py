"""API playground — test sessions for developers to experiment with endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from eaip.devplatform.events import PlaygroundSessionCreated
from eaip.devplatform.exceptions import PlaygroundError
from eaip.devplatform.models import PlaygroundSession


class ApiPlayground:
    """Manages interactive playground sessions for testing API endpoints."""

    def __init__(self) -> None:
        """Initialize ApiPlayground with an empty session store."""
        self._sessions: dict[str, PlaygroundSession] = {}
        self._event_handlers: list[Any] = []

    def on_event(self, handler: Any) -> None:
        """Register an event handler for playground events.

        Args:
            handler: A callable that accepts event instances.
        """
        self._event_handlers.append(handler)

    def _emit(self, event: Any) -> None:
        """Emit an event to all registered handlers.

        Args:
            event: The event instance to emit.
        """
        for handler in self._event_handlers:
            handler(event)

    async def create_session(self, developer_id: str, endpoint_id: str) -> PlaygroundSession:
        """Create a new playground session.

        Args:
            developer_id: The developer ID.
            endpoint_id: The endpoint ID to test.

        Returns:
            The created PlaygroundSession.
        """
        session = PlaygroundSession(
            id=f"{developer_id}:{endpoint_id}",
            developer_id=developer_id,
            endpoint_id=endpoint_id,
        )
        self._sessions[session.id] = session
        self._emit(
            PlaygroundSessionCreated(
                session_id=session.id,
                developer_id=developer_id,
                endpoint_id=endpoint_id,
            )
        )
        return session

    async def execute_test_request(
        self,
        session_id: str,
        request: dict[str, Any],
    ) -> PlaygroundSession:
        """Execute a test request within a playground session.

        Args:
            session_id: The session ID.
            request: The request preview data.

        Returns:
            The updated PlaygroundSession with request and response previews.

        Raises:
            PlaygroundError: If the session is not found.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise PlaygroundError(
                f"Playground session {session_id!r} not found",
                context={"session_id": session_id},
            )
        now = datetime.now(UTC)
        updated = PlaygroundSession(
            id=session.id,
            developer_id=session.developer_id,
            endpoint_id=session.endpoint_id,
            request_preview=request,
            response_preview={"status": "ok", "echo": request},
            created_at=session.created_at,
            last_activity=now,
            metadata=session.metadata,
        )
        self._sessions[session_id] = updated
        return updated

    async def get_session(self, session_id: str) -> PlaygroundSession:
        """Get a playground session by ID.

        Args:
            session_id: The session ID.

        Returns:
            The matching PlaygroundSession.

        Raises:
            PlaygroundError: If the session is not found.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise PlaygroundError(
                f"Playground session {session_id!r} not found",
                context={"session_id": session_id},
            )
        return session

    async def list_sessions(self, developer_id: str) -> tuple[PlaygroundSession, ...]:
        """List all playground sessions for a developer.

        Args:
            developer_id: The developer ID.

        Returns:
            A tuple of matching PlaygroundSession instances.
        """
        return tuple(s for s in self._sessions.values() if s.developer_id == developer_id)

    async def clear_session(self, session_id: str) -> None:
        """Clear / remove a playground session.

        Args:
            session_id: The session ID to clear.

        Raises:
            PlaygroundError: If the session is not found.
        """
        if session_id not in self._sessions:
            raise PlaygroundError(
                f"Playground session {session_id!r} not found",
                context={"session_id": session_id},
            )
        del self._sessions[session_id]


__all__ = ["ApiPlayground"]
