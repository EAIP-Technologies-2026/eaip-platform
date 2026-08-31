"""EmergencyAccessManager — manage emergency access requests and approvals."""

from __future__ import annotations

from datetime import timedelta

from eaip.emergency.events import AccessApproved, AccessExpired, AccessRejected, AccessRequested
from eaip.emergency.exceptions import EmergencyError, RequestNotFoundError
from eaip.emergency.models import (
    EmergencyApproval,
    EmergencyConfig,
    EmergencyRequest,
    EmergencyRequestStatus,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class EmergencyAccessManager:
    """Central service for handling emergency access requests."""

    def __init__(self, config: EmergencyConfig | None = None) -> None:
        self._config = config or EmergencyConfig()
        self._requests: dict[str, EmergencyRequest] = {}
        self._approvals: dict[str, EmergencyApproval] = {}
        self._log = get_logger("eaip.emergency.manager")

    @property
    def config(self) -> EmergencyConfig:
        return self._config

    async def request_access(self, request: EmergencyRequest) -> EmergencyRequest:
        """Create a new emergency access request."""
        if request.duration_minutes > self._config.max_duration_minutes:
            raise EmergencyError(
                f"Duration {request.duration_minutes}m exceeds max {self._config.max_duration_minutes}m"
            )
        if self._config.require_justification and not request.justification:
            raise EmergencyError("Justification is required for emergency access requests")

        updated = request.model_copy(
            update={"expires_at": utc_now() + timedelta(minutes=request.duration_minutes)}
        )
        self._requests[request.id] = updated

        AccessRequested(
            request_id=request.id,
            requester_id=request.requester_id,
            resource=request.resource,
            duration_minutes=request.duration_minutes,
        )
        self._log.info(
            "emergency.access.requested", request_id=request.id, resource=request.resource
        )
        return updated

    async def get_request(self, request_id: str) -> EmergencyRequest:
        """Get an emergency access request by ID."""
        request = self._requests.get(request_id)
        if request is None:
            raise RequestNotFoundError(f"Emergency request not found: {request_id}")
        return self._check_expiry(request)

    async def list_requests(
        self, status: EmergencyRequestStatus | None = None, resource: str | None = None
    ) -> list[EmergencyRequest]:
        """List emergency requests, optionally filtered."""
        result = list(self._requests.values())
        if status is not None:
            result = [r for r in result if r.status == status]
        if resource is not None:
            result = [r for r in result if r.resource == resource]
        return sorted(result, key=lambda r: r.requested_at, reverse=True)

    async def approve_request(
        self, request_id: str, approval: EmergencyApproval
    ) -> EmergencyRequest:
        """Approve an emergency access request."""
        request = self._requests.get(request_id)
        if request is None:
            raise RequestNotFoundError(f"Emergency request not found: {request_id}")

        request = self._check_expiry(request)
        if request.status != EmergencyRequestStatus.PENDING:
            raise EmergencyError(f"Cannot approve request in status: {request.status}")

        updated = request.model_copy(update={"status": EmergencyRequestStatus.APPROVED})
        self._requests[request_id] = updated
        self._approvals[approval.id] = approval

        AccessApproved(request_id=request_id, approver_id=approval.approver_id)
        self._log.info("emergency.access.approved", request_id=request_id)
        return updated

    async def reject_request(
        self, request_id: str, approval: EmergencyApproval
    ) -> EmergencyRequest:
        """Reject an emergency access request."""
        request = self._requests.get(request_id)
        if request is None:
            raise RequestNotFoundError(f"Emergency request not found: {request_id}")

        request = self._check_expiry(request)
        if request.status != EmergencyRequestStatus.PENDING:
            raise EmergencyError(f"Cannot reject request in status: {request.status}")

        updated = request.model_copy(update={"status": EmergencyRequestStatus.REJECTED})
        self._requests[request_id] = updated
        self._approvals[approval.id] = approval

        AccessRejected(
            request_id=request_id,
            approver_id=approval.approver_id,
            reason=approval.comment,
        )
        self._log.info("emergency.access.rejected", request_id=request_id)
        return updated

    async def expire_request(self, request_id: str) -> EmergencyRequest:
        """Mark an emergency access request as expired."""
        request = self._requests.get(request_id)
        if request is None:
            raise RequestNotFoundError(f"Emergency request not found: {request_id}")

        updated = request.model_copy(update={"status": EmergencyRequestStatus.EXPIRED})
        self._requests[request_id] = updated

        AccessExpired(request_id=request_id)
        self._log.info("emergency.access.expired", request_id=request_id)
        return updated

    def _check_expiry(self, request: EmergencyRequest) -> EmergencyRequest:
        """Check if a pending request has expired and update status."""
        if request.status == EmergencyRequestStatus.PENDING and utc_now() >= request.expires_at:
            updated = request.model_copy(update={"status": EmergencyRequestStatus.EXPIRED})
            self._requests[request.id] = updated
            return updated
        return request

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about emergency requests."""
        return {
            "total_requests": len(self._requests),
            "pending": sum(
                1 for r in self._requests.values() if r.status == EmergencyRequestStatus.PENDING
            ),
            "approved": sum(
                1 for r in self._requests.values() if r.status == EmergencyRequestStatus.APPROVED
            ),
            "rejected": sum(
                1 for r in self._requests.values() if r.status == EmergencyRequestStatus.REJECTED
            ),
            "expired": sum(
                1 for r in self._requests.values() if r.status == EmergencyRequestStatus.EXPIRED
            ),
        }


__all__ = ["EmergencyAccessManager"]
