"""Agent registry — lifecycle management for agent definitions.

Supports CRUD, versioning, status transitions, and event publishing
for every lifecycle state change.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from eaip.agents.events import (
    AgentCreated,
    AgentDeleted,
    AgentFailed,
    AgentPaused,
    AgentStarted,
    AgentStopped,
    AgentUpdated,
)
from eaip.agents.exceptions import AgentNotFoundError
from eaip.agents.models import AgentSpec, AgentStatus
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger


class AgentRegistry:
    """In-memory registry for agent definitions with lifecycle management.

    Supports full CRUD, status transitions (Draft → Registered → Ready →
    Running → Paused/Stopped/Failed → Archived), and event publishing.
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._agents: dict[str, AgentSpec] = {}
        self._statuses: dict[str, AgentStatus] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.agents.registry")

    # ── CRUD ────────────────────────────────────────────────────────

    async def create(self, agent: AgentSpec, metadata: dict[str, Any] | None = None) -> AgentSpec:
        """Register a new agent definition.

        Args:
            agent: The agent specification.
            metadata: Optional metadata (labels, tags, ownership).

        Returns:
            The registered agent.
        """
        self._agents[agent.id] = agent
        self._statuses[agent.id] = AgentStatus.DRAFT
        if metadata:
            self._metadata[agent.id] = metadata
        await self._publish(
            AgentCreated(agent_id=agent.id, name=agent.name, version=agent.version)
        )
        self._log.info("agent.created", agent_id=agent.id, name=agent.name)
        return agent

    async def update(self, agent_id: str, **updates: Any) -> AgentSpec:
        """Update an existing agent definition.

        Args:
            agent_id: The agent identifier.
            **updates: Fields to update on the AgentSpec.

        Returns:
            The updated agent.

        Raises:
            AgentNotFoundError: If the agent does not exist.
        """
        agent = self._agents.get(agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent {agent_id!r} not found")
        updated = agent.model_copy(update=updates)
        self._agents[agent_id] = updated
        await self._publish(
            AgentUpdated(
                agent_id=agent_id,
                name=updated.name,
                changes=tuple(updates.keys()),
            )
        )
        self._log.info("agent.updated", agent_id=agent_id, changes=list(updates.keys()))
        return updated

    async def delete(self, agent_id: str) -> None:
        """Delete an agent definition.

        Args:
            agent_id: The agent identifier.

        Raises:
            AgentNotFoundError: If the agent does not exist.
        """
        agent = self._agents.pop(agent_id, None)
        if agent is None:
            raise AgentNotFoundError(f"Agent {agent_id!r} not found")
        self._statuses.pop(agent_id, None)
        self._metadata.pop(agent_id, None)
        await self._publish(AgentDeleted(agent_id=agent_id, name=agent.name))
        self._log.info("agent.deleted", agent_id=agent_id)

    async def get(self, agent_id: str) -> AgentSpec | None:
        """Retrieve an agent by ID.

        Args:
            agent_id: The agent identifier.

        Returns:
            The agent spec, or ``None`` if not found.
        """
        return self._agents.get(agent_id)

    async def list_agents(
        self,
        status: AgentStatus | None = None,
        tag: str | None = None,
    ) -> Sequence[AgentSpec]:
        """List agents, optionally filtered.

        Args:
            status: Optional status filter.
            tag: Optional tag filter.

        Returns:
            A list of matching agent definitions.
        """
        results = list(self._agents.values())
        if status is not None:
            results = [a for a in results if self._statuses.get(a.id) == status]
        if tag is not None:
            results = [
                a
                for a in results
                if tag in self._metadata.get(a.id, {}).get("tags", [])
            ]
        return results

    # ── Lifecycle transitions ───────────────────────────────────────

    async def transition_to(
        self, agent_id: str, new_status: AgentStatus
    ) -> AgentSpec:
        """Transition an agent to a new lifecycle state.

        Args:
            agent_id: The agent identifier.
            new_status: The target lifecycle status.

        Returns:
            The agent spec.

        Raises:
            AgentNotFoundError: If the agent does not exist.
        """
        agent = self._agents.get(agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent {agent_id!r} not found")
        self._statuses[agent_id] = new_status

        if new_status == AgentStatus.RUNNING:
            await self._publish(AgentStarted(agent_id=agent_id, run_id=""))
        elif new_status == AgentStatus.PAUSED:
            await self._publish(AgentPaused(agent_id=agent_id, run_id=""))
        elif new_status == AgentStatus.STOPPED:
            await self._publish(AgentStopped(agent_id=agent_id, run_id=""))
        elif new_status == AgentStatus.FAILED:
            await self._publish(AgentFailed(agent_id=agent_id, run_id="", error=""))

        self._log.info(
            "agent.status_changed",
            agent_id=agent_id,
            new_status=new_status.value,
        )
        return agent

    async def get_status(self, agent_id: str) -> AgentStatus | None:
        """Get the current lifecycle status of an agent.

        Args:
            agent_id: The agent identifier.

        Returns:
            The agent's status, or ``None`` if not found.
        """
        return self._statuses.get(agent_id)

    # ── Metadata ────────────────────────────────────────────────────

    async def set_metadata(self, agent_id: str, metadata: dict[str, Any]) -> None:
        """Set metadata for an agent.

        Args:
            agent_id: The agent identifier.
            metadata: Metadata dict (labels, tags, ownership, etc.).
        """
        self._metadata[agent_id] = metadata

    async def get_metadata(self, agent_id: str) -> dict[str, Any]:
        """Get metadata for an agent.

        Args:
            agent_id: The agent identifier.

        Returns:
            The metadata dict, or empty if not found.
        """
        return self._metadata.get(agent_id, {})

    # ── Internal ────────────────────────────────────────────────────

    async def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)


__all__ = ["AgentRegistry"]
