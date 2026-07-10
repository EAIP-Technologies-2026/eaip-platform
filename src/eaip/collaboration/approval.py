"""Approval service — multi-party approval for collaboration workflows."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from eaip.collaboration.events import (
    ApprovalCompleted,
    ApprovalRejected,
    ApprovalRequested,
)
from eaip.collaboration.exceptions import ApprovalError
from eaip.logging.context import get_logger


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalRecord:
    """Internal record for a multi-party approval request."""

    def __init__(
        self,
        approval_id: str,
        session_id: str,
        step_id: str,
        payload: dict[str, Any],
        approvers: list[str],
    ) -> None:
        self.approval_id = approval_id
        self.session_id = session_id
        self.step_id = step_id
        self.payload = payload
        self.approvers = approvers
        self.status: ApprovalStatus = ApprovalStatus.PENDING
        self.responses: dict[str, bool] = {}
        self.errors: dict[str, str] = {}


class CollaborationApprovalService:
    """Manages multi-party approval workflows for collaboration sessions.

    Integrates with the existing StepApprovalHandler pattern.
    """

    def __init__(self, event_bus: Any = None) -> None:
        self._event_bus = event_bus
        self._approvals: dict[str, ApprovalRecord] = {}
        self._log = get_logger("eaip.collaboration.approval")

    async def request_approval(
        self,
        step_id: str,
        session_id: str,
        payload: dict[str, Any],
        approvers: list[str],
    ) -> str:
        """Request multi-party approval for a step.

        Args:
            step_id: The step requiring approval.
            session_id: The collaboration session ID.
            payload: The approval payload.
            approvers: List of approver IDs.

        Returns:
            The approval ID.

        Raises:
            ApprovalError: If approvers list is empty.
        """
        if not approvers:
            raise ApprovalError("none", "at least one approver is required")

        approval_id = f"app_{step_id}_{session_id[:8]}"
        record = ApprovalRecord(
            approval_id=approval_id,
            session_id=session_id,
            step_id=step_id,
            payload=payload,
            approvers=list(approvers),
        )
        self._approvals[approval_id] = record

        self._publish(
            ApprovalRequested(
                approval_id=approval_id,
                session_id=session_id,
                step_id=step_id,
                approver_count=len(approvers),
            ),
        )
        self._log.info(
            "approval.requested",
            approval_id=approval_id,
            step_id=step_id,
            approvers=approvers,
        )
        return approval_id

    async def approve(self, approval_id: str, approver_id: str) -> None:
        """Approve a pending approval request.

        Args:
            approval_id: The approval ID.
            approver_id: The approver's ID.

        Raises:
            ApprovalError: If the approval request is not found.
        """
        record = self._approvals.get(approval_id)
        if record is None:
            raise ApprovalError(approval_id, "not found")
        if record.status is ApprovalStatus.APPROVED:
            return
        if approver_id not in record.approvers:
            raise ApprovalError(approval_id, f"approver {approver_id} not authorized")

        record.responses[approver_id] = True

        if self._is_fully_approved(record):
            record.status = ApprovalStatus.APPROVED
            self._publish(
                ApprovalCompleted(
                    approval_id=approval_id,
                    approver_id=approver_id,
                ),
            )
            self._log.info("approval.completed", approval_id=approval_id)

    async def reject(self, approval_id: str, approver_id: str, reason: str) -> None:
        """Reject a pending approval request.

        Args:
            approval_id: The approval ID.
            approver_id: The approver's ID.
            reason: The rejection reason.

        Raises:
            ApprovalError: If the approval request is not found.
        """
        record = self._approvals.get(approval_id)
        if record is None:
            raise ApprovalError(approval_id, "not found")
        if record.status is ApprovalStatus.REJECTED:
            return
        if approver_id not in record.approvers:
            raise ApprovalError(approval_id, f"approver {approver_id} not authorized")

        record.responses[approver_id] = False
        record.errors[approver_id] = reason
        record.status = ApprovalStatus.REJECTED

        self._publish(
            ApprovalRejected(
                approval_id=approval_id,
                approver_id=approver_id,
                reason=reason,
            ),
        )
        self._log.info(
            "approval.rejected",
            approval_id=approval_id,
            approver_id=approver_id,
            reason=reason,
        )

    async def get_approval_status(self, approval_id: str) -> dict[str, Any] | None:
        """Check the status of an approval request.

        Args:
            approval_id: The approval ID.

        Returns:
            A dict with status information, or None.
        """
        record = self._approvals.get(approval_id)
        if record is None:
            return None
        return {
            "approval_id": record.approval_id,
            "session_id": record.session_id,
            "step_id": record.step_id,
            "status": record.status,
            "approvers": record.approvers,
            "responses": dict(record.responses),
            "errors": dict(record.errors),
        }

    async def list_pending_approvals(
        self,
        approver_id: str,
    ) -> list[dict[str, Any]]:
        """List all pending approvals for a given approver.

        Args:
            approver_id: The approver's ID.

        Returns:
            A list of pending approval records.
        """
        pending: list[dict[str, Any]] = []
        for record in self._approvals.values():
            if record.status is ApprovalStatus.PENDING and approver_id in record.approvers:
                pending.append({
                    "approval_id": record.approval_id,
                    "session_id": record.session_id,
                    "step_id": record.step_id,
                    "approvers": record.approvers,
                    "responded": approver_id in record.responses,
                })
        return pending

    def _is_fully_approved(self, record: ApprovalRecord) -> bool:
        return all(
            approver in record.responses and record.responses[approver]
            for approver in record.approvers
        )

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            try:
                self._event_bus.publish(event)
            except Exception:
                self._log.warning("event.publish.failed", event_type=type(event).__name__)


__all__ = ["CollaborationApprovalService"]
