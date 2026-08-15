"""ApprovalService — in-memory store for Conductor approval requests."""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from eaip.copilot.events import ApprovalRequested, ApprovalResolved
from eaip.copilot.models import ApprovalRequest, ApprovalStatus, RiskTier
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now

DEFAULT_TTL_SECONDS = 3600


class ApprovalNotFoundError(KeyError):
    """Raised when an approval id is unknown or no longer pending."""


class ApprovalService:
    """Tracks governed tool approvals and applies human decisions.

    Approvals live in memory for the lifetime of the platform instance and
    expire after a configurable TTL when left undecided.
    """

    def __init__(
        self,
        event_bus: EventBus | None = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        """Initialize the approval service.

        Args:
            event_bus: Optional event bus for approval lifecycle events.
            ttl_seconds: How long pending approvals remain valid.
        """
        self._requests: dict[str, ApprovalRequest] = {}
        self._event_bus = event_bus
        self._ttl = timedelta(seconds=ttl_seconds)
        self._log = get_logger("eaip.copilot.approvals")

    async def create(
        self,
        *,
        tool_name: str,
        arguments: dict[str, Any],
        requester_id: str,
        risk: RiskTier,
    ) -> ApprovalRequest:
        """Create a new pending approval request.

        Args:
            tool_name: The governed tool that awaits approval.
            arguments: The arguments the tool would run with.
            requester_id: The actor that requested the action.
            risk: The tool's risk tier.

        Returns:
            The created :class:`ApprovalRequest`.
        """
        request = ApprovalRequest(
            id=f"appr-{uuid.uuid4().hex[:12]}",
            tool_name=tool_name,
            arguments=arguments,
            requester_id=requester_id,
            risk=risk,
        )
        self._requests[request.id] = request
        self._log.info(
            "approval.requested",
            approval_id=request.id,
            tool=tool_name,
            requester=requester_id,
        )
        await self._publish(
            ApprovalRequested(
                approval_id=request.id,
                tool_name=tool_name,
                requester_id=requester_id,
                arguments=arguments,
            )
        )
        return request

    def get(self, approval_id: str) -> ApprovalRequest | None:
        """Retrieve an approval request by id.

        Args:
            approval_id: The approval id.

        Returns:
            The request, or None when unknown.
        """
        return self._requests.get(approval_id)

    def list_pending(self, requester_id: str | None = None) -> list[ApprovalRequest]:
        """List undecided approval requests, newest first.

        Args:
            requester_id: Optional filter to a single requester.

        Returns:
            Pending approval requests.
        """
        self._expire_stale()
        results = [r for r in self._requests.values() if r.status is ApprovalStatus.PENDING]
        if requester_id is not None:
            results = [r for r in results if r.requester_id == requester_id]
        results.sort(key=lambda r: r.created_at, reverse=True)
        return results

    async def decide(
        self,
        approval_id: str,
        *,
        decided_by: str,
        approve: bool,
    ) -> ApprovalRequest:
        """Decide a pending approval request.

        Args:
            approval_id: The approval id.
            decided_by: The actor making the decision.
            approve: True to approve, False to reject.

        Returns:
            The updated :class:`ApprovalRequest`.

        Raises:
            ApprovalNotFoundError: If the id is unknown or not pending.
        """
        self._expire_stale()
        request = self._requests.get(approval_id)
        if request is None or request.status is not ApprovalStatus.PENDING:
            raise ApprovalNotFoundError(f"approval {approval_id!r} is not pending")
        decided = request.model_copy(
            update={
                "status": ApprovalStatus.APPROVED if approve else ApprovalStatus.REJECTED,
                "decided_at": utc_now(),
                "decided_by": decided_by,
            }
        )
        self._requests[approval_id] = decided
        self._log.info(
            "approval.decided",
            approval_id=approval_id,
            approve=approve,
            by=decided_by,
        )
        await self._publish(
            ApprovalResolved(approval_id=approval_id, approved=approve, decided_by=decided_by)
        )
        return decided

    def _expire_stale(self) -> None:
        now = utc_now()
        for request in list(self._requests.values()):
            if request.status is ApprovalStatus.PENDING and now - request.created_at > self._ttl:
                self._requests[request.id] = request.model_copy(
                    update={"status": ApprovalStatus.EXPIRED}
                )

    async def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)


__all__ = ["DEFAULT_TTL_SECONDS", "ApprovalNotFoundError", "ApprovalService"]
