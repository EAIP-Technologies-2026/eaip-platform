"""Health check for the document lifecycle subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class DocumentLifecycleHealthCheck(HealthCheck):
    """Health check for the document lifecycle subsystem."""

    name: str = "eaip.document_lifecycle"

    def __init__(
        self,
        total_documents: int = 0,
        active_count: int = 0,
        archived_count: int = 0,
        expired_count: int = 0,
        pending_reviews: int = 0,
        pending_approvals: int = 0,
        expiring_soon: int = 0,
    ) -> None:
        self._total_documents = total_documents
        self._active_count = active_count
        self._archived_count = archived_count
        self._expired_count = expired_count
        self._pending_reviews = pending_reviews
        self._pending_approvals = pending_approvals
        self._expiring_soon = expiring_soon

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        details = {
            "total_documents": self._total_documents,
            "active": self._active_count,
            "archived": self._archived_count,
            "expired": self._expired_count,
            "pending_reviews": self._pending_reviews,
            "pending_approvals": self._pending_approvals,
            "expiring_soon": self._expiring_soon,
        }
        if self._pending_approvals > 0:
            return HealthReport(
                component="DocumentLifecycle",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{self._pending_approvals} pending approval(s)",
            )
        if self._pending_reviews > 0:
            return HealthReport(
                component="DocumentLifecycle",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{self._pending_reviews} pending review(s)",
            )
        if self._expiring_soon > 0:
            return HealthReport(
                component="DocumentLifecycle",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{self._expiring_soon} document(s) expiring soon",
            )
        return HealthReport(
            component="DocumentLifecycle",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = [
    "DocumentLifecycleHealthCheck",
]
