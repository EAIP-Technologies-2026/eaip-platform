"""ApprovalWorkflowEngine — governed approval requests with expiry."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class ApprovalRequest(BaseModel):
    """A governed approval request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    requester: str
    target_type: str
    target_id: str = ""
    reason: str = ""
    status: str = "pending"
    approver: str = ""
    decision_reason: str = ""
    created_at: str = ""
    decided_at: str | None = None
    expires_at: str | None = None


class ApprovalWorkflowEngine:
    """Manages approval workflows with governance.

    Supports approve, reject, defer, and automatic expiry.
    All operations are tenant-scoped.
    """

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}
        self._log = get_logger("eaip.governance_center.approval")

    def _key(self, tenant_id: str, request_id: str) -> str:
        return f"{tenant_id}:{request_id}"

    def create_approval_request(
        self,
        tenant_id: str,
        requester: str,
        target_type: str,
        target_id: str = "",
        reason: str = "",
        expires_at: str | None = None,
    ) -> ApprovalRequest:
        """Create a new approval request."""
        request_id = f"apr-{uuid.uuid4().hex[:10]}"
        request = ApprovalRequest(
            id=request_id,
            tenant_id=tenant_id,
            requester=requester,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            status="pending",
            created_at=utc_now().isoformat(),
            expires_at=expires_at,
        )
        self._requests[self._key(tenant_id, request_id)] = request
        self._log.info("approval.created", request_id=request_id, target_type=target_type)
        return request

    def approve(
        self,
        tenant_id: str,
        request_id: str,
        approver: str,
        reason: str = "",
    ) -> ApprovalRequest:
        """Approve a request."""
        request = self._requests.get(self._key(tenant_id, request_id))
        if request is None:
            raise ValueError(f"Approval request {request_id} not found")
        if request.status != "pending":
            raise ValueError(f"Request {request_id} is already {request.status}")
        updated = request.model_copy(update={
            "status": "approved",
            "approver": approver,
            "decision_reason": reason,
            "decided_at": utc_now().isoformat(),
        })
        self._requests[self._key(tenant_id, request_id)] = updated
        self._log.info("approval.approved", request_id=request_id, approver=approver)
        return updated

    def reject(
        self,
        tenant_id: str,
        request_id: str,
        approver: str,
        reason: str = "",
    ) -> ApprovalRequest:
        """Reject a request."""
        request = self._requests.get(self._key(tenant_id, request_id))
        if request is None:
            raise ValueError(f"Approval request {request_id} not found")
        if request.status != "pending":
            raise ValueError(f"Request {request_id} is already {request.status}")
        updated = request.model_copy(update={
            "status": "rejected",
            "approver": approver,
            "decision_reason": reason,
            "decided_at": utc_now().isoformat(),
        })
        self._requests[self._key(tenant_id, request_id)] = updated
        self._log.info("approval.rejected", request_id=request_id, approver=approver)
        return updated

    def defer(
        self,
        tenant_id: str,
        request_id: str,
        approver: str,
        reason: str = "",
    ) -> ApprovalRequest:
        """Defer a request."""
        request = self._requests.get(self._key(tenant_id, request_id))
        if request is None:
            raise ValueError(f"Approval request {request_id} not found")
        if request.status != "pending":
            raise ValueError(f"Request {request_id} is already {request.status}")
        updated = request.model_copy(update={
            "status": "deferred",
            "approver": approver,
            "decision_reason": reason,
            "decided_at": utc_now().isoformat(),
        })
        self._requests[self._key(tenant_id, request_id)] = updated
        self._log.info("approval.deferred", request_id=request_id, approver=approver)
        return updated

    def get_pending_approvals(self, tenant_id: str) -> list[ApprovalRequest]:
        """Get all pending approval requests for a tenant."""
        return [
            r for k, r in self._requests.items()
            if k.startswith(f"{tenant_id}:") and r.status == "pending"
        ]

    def check_approval_status(self, tenant_id: str, request_id: str) -> ApprovalRequest | None:
        """Check the status of an approval request."""
        return self._requests.get(self._key(tenant_id, request_id))

    def expire_approvals(self, tenant_id: str) -> list[ApprovalRequest]:
        """Expire approvals that have passed their expiry time."""
        now = utc_now().isoformat()
        expired: list[ApprovalRequest] = []
        for key, request in list(self._requests.items()):
            if (
                key.startswith(f"{tenant_id}:")
                and request.status == "pending"
                and request.expires_at
                and request.expires_at <= now
            ):
                updated = request.model_copy(update={
                    "status": "expired",
                    "decided_at": now,
                    "decision_reason": "expired",
                })
                self._requests[key] = updated
                expired.append(updated)
                self._log.info("approval.expired", request_id=request.id)
        return expired


__all__ = ["ApprovalRequest", "ApprovalWorkflowEngine"]
