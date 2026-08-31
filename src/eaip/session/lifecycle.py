"""SessionLifecycleManager — expiry cycles, tenant cleanup, session transfer and merge."""

from __future__ import annotations

from typing import Any

from eaip.logging.context import get_logger
from eaip.session.events import SessionTransferred
from eaip.session.manager import SessionManager
from eaip.session.models import Session, SessionStatus


class SessionLifecycleManager:
    """Manages advanced session lifecycle operations.

    Provides expiry cycling, tenant-wide cleanup, session transfer
    between users, and session merging.
    """

    def __init__(
        self,
        manager: SessionManager,
        event_publisher: Any = None,
    ) -> None:
        """Initialize the SessionLifecycleManager.

        Args:
            manager: The SessionManager instance.
            event_publisher: Optional callable for publishing domain events.
        """
        self._manager = manager
        self._event_publisher = event_publisher or (lambda _: None)
        self._log = get_logger("eaip.session.lifecycle")

    async def run_expiry_cycle(self) -> int:
        """Check all active sessions and expire those past their TTL.

        Returns:
            The number of sessions expired in this cycle.
        """
        count = await self._manager._expire_stale_sessions()
        if count:
            self._log.info("expiry.cycle.complete", expired=count)
        return count

    async def cleanup_tenant(self, tenant_id: str) -> int:
        """Close all sessions belonging to a given tenant.

        Args:
            tenant_id: The tenant identifier.

        Returns:
            The number of sessions closed.
        """
        tenant_sessions = await self._manager.list_sessions(tenant_id=tenant_id)
        count = 0
        for s in tenant_sessions:
            if s.status is not SessionStatus.CLOSED and s.status is not SessionStatus.EXPIRED:
                await self._manager.close_session(s.id)
                count += 1
        self._log.info("tenant.cleanup.complete", tenant_id=tenant_id, closed=count)
        return count

    async def transfer_session(
        self,
        session_id: str,
        target_user_id: str,
    ) -> Session:
        """Transfer a session to a different user.

        Args:
            session_id: The session identifier.
            target_user_id: The target user identifier.

        Returns:
            The transferred Session.

        Raises:
            SessionNotFoundError: If the session does not exist.
        """
        session = await self._manager.get_session(session_id)
        source_user = session.user_id

        updates: dict[str, Any] = {"user_id": target_user_id}
        updated = await self._manager.update_session(session_id, updates)

        self._event_publisher(
            SessionTransferred(
                session_id=session_id,
                source_user_id=source_user,
                target_user_id=target_user_id,
            )
        )

        self._log.info(
            "session.transferred",
            session_id=session_id,
            from_user=source_user,
            to_user=target_user_id,
        )
        return updated

    async def merge_sessions(self, source_id: str, target_id: str) -> Session:
        """Merge source session data into the target session.

        Combines metadata and tags from the source into the target,
        then closes the source session.

        Args:
            source_id: The source session identifier.
            target_id: The target session identifier.

        Returns:
            The merged (target) Session.

        Raises:
            SessionNotFoundError: If either session is not found.
        """
        source = await self._manager.get_session(source_id)
        target = await self._manager.get_session(target_id)

        merged_meta = {**target.metadata, **source.metadata}
        merged_tags = tuple(set(target.tags) | set(source.tags))

        updates: dict[str, Any] = {
            "metadata": merged_meta,
            "tags": merged_tags,
        }
        merged = await self._manager.update_session(target_id, updates)
        await self._manager.close_session(source_id)

        self._log.info(
            "session.merged",
            source=source_id,
            target=target_id,
        )
        return merged


__all__ = ["SessionLifecycleManager"]
