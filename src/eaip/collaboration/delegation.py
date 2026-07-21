"""Task delegation service — delegate tasks between agents."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from eaip.collaboration.events import (
    DelegationAccepted,
    DelegationRejected,
    DelegationRequested,
)
from eaip.collaboration.exceptions import DelegationError
from eaip.collaboration.models import DelegationRequest, DelegationStatus
from eaip.logging.context import get_logger


class TaskDelegationService:
    """Manages task delegation between agents.

    Supports full lifecycle: delegate, accept, reject, complete.
    Also provides agent discovery based on capabilities.
    """

    def __init__(self, event_bus: Any = None) -> None:
        self._event_bus = event_bus
        self._delegations: dict[str, DelegationRequest] = {}
        self._log = get_logger("eaip.collaboration.delegation")

    async def delegate_task(self, request: DelegationRequest) -> DelegationRequest:
        """Delegate a task to another agent.

        Args:
            request: The delegation request.

        Returns:
            The created delegation request.
        """
        delegation = DelegationRequest(
            id=request.id or str(uuid.uuid4()),
            from_agent_id=request.from_agent_id,
            to_agent_id=request.to_agent_id,
            task_description=request.task_description,
            context=request.context,
            priority=request.priority,
            deadline=request.deadline,
            status=DelegationStatus.PENDING,
            created_at=datetime.now(),
        )
        self._delegations[delegation.id] = delegation

        self._publish(
            DelegationRequested(
                delegation_id=delegation.id,
                from_agent_id=delegation.from_agent_id,
                to_agent_id=delegation.to_agent_id,
                task_description=delegation.task_description,
            ),
        )
        self._log.info(
            "delegation.created",
            delegation_id=delegation.id,
            from_agent=delegation.from_agent_id,
            to_agent=delegation.to_agent_id,
        )
        return delegation

    async def accept_task(self, delegation_id: str) -> DelegationRequest:
        """Accept a pending delegation.

        Args:
            delegation_id: The delegation ID.

        Returns:
            The updated delegation request.

        Raises:
            DelegationError: If the delegation is not found or not pending.
        """
        delegation = self._delegations.get(delegation_id)
        if delegation is None:
            raise DelegationError(delegation_id, "not found")
        if delegation.status is not DelegationStatus.PENDING:
            raise DelegationError(delegation_id, f"cannot accept — status is {delegation.status}")

        accepted = delegation.model_copy(
            update={
                "status": DelegationStatus.ACCEPTED,
            }
        )
        self._delegations[delegation_id] = accepted

        self._publish(
            DelegationAccepted(
                delegation_id=delegation_id,
                to_agent_id=delegation.to_agent_id,
            ),
        )
        self._log.info("delegation.accepted", delegation_id=delegation_id)
        return accepted

    async def reject_task(self, delegation_id: str, reason: str) -> DelegationRequest:
        """Reject a pending delegation.

        Args:
            delegation_id: The delegation ID.
            reason: The reason for rejection.

        Returns:
            The updated delegation request.

        Raises:
            DelegationError: If the delegation is not found or not pending.
        """
        delegation = self._delegations.get(delegation_id)
        if delegation is None:
            raise DelegationError(delegation_id, "not found")
        if delegation.status is not DelegationStatus.PENDING:
            raise DelegationError(delegation_id, f"cannot reject — status is {delegation.status}")

        rejected = delegation.model_copy(
            update={
                "status": DelegationStatus.REJECTED,
                "response": reason,
            }
        )
        self._delegations[delegation_id] = rejected

        self._publish(
            DelegationRejected(
                delegation_id=delegation_id,
                to_agent_id=delegation.to_agent_id,
                reason=reason,
            ),
        )
        self._log.info("delegation.rejected", delegation_id=delegation_id, reason=reason)
        return rejected

    async def complete_task(self, delegation_id: str, result: str) -> DelegationRequest:
        """Mark a delegation as completed with a result.

        Args:
            delegation_id: The delegation ID.
            result: The result output.

        Returns:
            The updated delegation request.

        Raises:
            DelegationError: If the delegation is not found.
        """
        delegation = self._delegations.get(delegation_id)
        if delegation is None:
            raise DelegationError(delegation_id, "not found")
        if delegation.status is not DelegationStatus.ACCEPTED:
            raise DelegationError(delegation_id, f"cannot complete — status is {delegation.status}")

        completed = delegation.model_copy(
            update={
                "status": DelegationStatus.COMPLETED,
                "response": result,
            }
        )
        self._delegations[delegation_id] = completed
        self._log.info("delegation.completed", delegation_id=delegation_id)
        return completed

    async def get_delegation(self, delegation_id: str) -> DelegationRequest | None:
        """Get the current status of a delegation.

        Args:
            delegation_id: The delegation ID.

        Returns:
            The delegation request, or None.
        """
        return self._delegations.get(delegation_id)

    async def list_delegations(
        self,
        agent_id: str | None = None,
        status: DelegationStatus | None = None,
    ) -> list[DelegationRequest]:
        """List delegations, optionally filtered.

        Args:
            agent_id: Optional agent ID filter (matches from or to).
            status: Optional status filter.

        Returns:
            A list of matching delegation requests.
        """
        results = list(self._delegations.values())
        if agent_id is not None:
            results = [d for d in results if agent_id in (d.from_agent_id, d.to_agent_id)]
        if status is not None:
            results = [d for d in results if d.status is status]
        return results

    async def query_available_agents(
        self,
        capability: str,
        known_agents: dict[str, list[str]] | None = None,
    ) -> list[str]:
        """Find agents capable of a given capability.

        Args:
            capability: The required capability.
            known_agents: Optional mapping of agent_id -> list of capabilities.

        Returns:
            A list of agent IDs matching the capability.
        """
        if known_agents is None:
            return []
        return [agent_id for agent_id, caps in known_agents.items() if capability in caps]

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            try:
                self._event_bus.publish(event)
            except Exception:
                self._log.warning("event.publish.failed", event_type=type(event).__name__)


__all__ = ["TaskDelegationService"]
