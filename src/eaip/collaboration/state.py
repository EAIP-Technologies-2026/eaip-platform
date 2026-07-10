"""Shared state manager — versioned shared state for collaboration sessions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from eaip.collaboration.events import StateUpdated
from eaip.collaboration.exceptions import CollaborationError
from eaip.collaboration.models import SharedState
from eaip.logging.context import get_logger


class SharedStateManager:
    """Manages shared state for collaboration sessions with version tracking.

    Supports setting/getting variables, recording agent contributions,
    and merging states between sessions.
    """

    def __init__(self, event_bus: Any = None) -> None:
        self._event_bus = event_bus
        self._states: dict[str, SharedState] = {}
        self._log = get_logger("eaip.collaboration.state")

    async def create_state(self, session_id: str) -> SharedState:
        """Create a new shared state for a session.

        Args:
            session_id: The collaboration session ID.

        Returns:
            The created SharedState.
        """
        state = SharedState(
            id=str(uuid.uuid4()),
            session_id=session_id,
            variables={},
            agent_contributions={},
            version=1,
        )
        self._states[session_id] = state
        self._log.info("state.created", session_id=session_id, state_id=state.id)
        return state

    async def set_variable(
        self,
        session_id: str,
        key: str,
        value: Any,
        agent_id: str = "",
    ) -> SharedState:
        """Set a variable in shared state with version bump.

        Args:
            session_id: The session ID.
            key: The variable key.
            value: The variable value.
            agent_id: Optional agent ID making the change.

        Returns:
            The updated SharedState.

        Raises:
            CollaborationError: If the session has no state.
        """
        state = self._states.get(session_id)
        if state is None:
            raise CollaborationError(f"No shared state for session {session_id}")

        updated = state.model_copy(update={
            "variables": {**state.variables, key: value},
            "version": state.version + 1,
            "updated_at": datetime.now(),
        })
        self._states[session_id] = updated

        self._publish(
            StateUpdated(
                session_id=session_id,
                key=key,
                agent_id=agent_id,
                version=updated.version,
            ),
        )
        return updated

    async def get_variable(
        self,
        session_id: str,
        key: str,
    ) -> Any | None:
        """Get a variable from shared state.

        Args:
            session_id: The session ID.
            key: The variable key.

        Returns:
            The variable value, or None.
        """
        state = self._states.get(session_id)
        if state is None:
            return None
        return state.variables.get(key)

    async def get_all_variables(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        """Get all variables from shared state.

        Args:
            session_id: The session ID.

        Returns:
            A dict of all variables.
        """
        state = self._states.get(session_id)
        if state is None:
            return {}
        return dict(state.variables)

    async def record_contribution(
        self,
        session_id: str,
        agent_id: str,
        summary: str,
    ) -> SharedState:
        """Record an agent's contribution summary.

        Args:
            session_id: The session ID.
            agent_id: The agent ID.
            summary: The contribution summary.

        Returns:
            The updated SharedState.

        Raises:
            CollaborationError: If the session has no state.
        """
        state = self._states.get(session_id)
        if state is None:
            raise CollaborationError(f"No shared state for session {session_id}")

        updated = state.model_copy(update={
            "agent_contributions": {
                **state.agent_contributions,
                agent_id: summary,
            },
            "version": state.version + 1,
            "updated_at": datetime.now(),
        })
        self._states[session_id] = updated
        return updated

    async def get_shared_state(self, session_id: str) -> SharedState | None:
        """Get the full shared state for a session.

        Args:
            session_id: The session ID.

        Returns:
            The SharedState, or None.
        """
        return self._states.get(session_id)

    async def merge_states(
        self,
        target_id: str,
        source_id: str,
    ) -> SharedState:
        """Merge a source session's state into a target session's state.

        Variables from the source take precedence on conflict.
        Agent contributions are merged.

        Args:
            target_id: The target session ID.
            source_id: The source session ID.

        Returns:
            The merged SharedState.

        Raises:
            CollaborationError: If either session has no state.
        """
        target = self._states.get(target_id)
        source = self._states.get(source_id)

        if target is None:
            raise CollaborationError(f"No shared state for target session {target_id}")
        if source is None:
            raise CollaborationError(f"No shared state for source session {source_id}")

        merged = target.model_copy(update={
            "variables": {**target.variables, **source.variables},
            "agent_contributions": {
                **target.agent_contributions,
                **source.agent_contributions,
            },
            "version": max(target.version, source.version) + 1,
            "updated_at": datetime.now(),
        })
        self._states[target_id] = merged
        self._log.info(
            "state.merged",
            target_id=target_id,
            source_id=source_id,
            version=merged.version,
        )
        return merged

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            try:
                self._event_bus.publish(event)
            except Exception:
                self._log.warning("event.publish.failed", event_type=type(event).__name__)


__all__ = ["SharedStateManager"]
