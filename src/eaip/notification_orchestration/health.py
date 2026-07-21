"""Notification orchestration health check — reports rule, batch, and escalation stats."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.notification_orchestration.service import NotificationOrchestrationService


class NotificationOrchestrationHealthCheck(HealthCheck):
    """Reports notification orchestration health based on rule and batch counts."""

    name: str = "eaip.notification_orchestration"

    def __init__(self, service: NotificationOrchestrationService | None = None) -> None:
        """Initialize the health check with an optional service instance."""
        self._service = service or NotificationOrchestrationService()

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        rules = await self._service.list_rules()
        batches = await self._service.list_batches()

        active_count = sum(1 for r in rules if r.status.value == "active")
        failed_batches = sum(1 for b in batches if b.status.value == "failed")

        details = {
            "total_rules": len(rules),
            "active_rules": active_count,
            "total_batches": len(batches),
            "failed_batches": failed_batches,
        }

        if failed_batches > 0:
            return HealthReport(
                component="NotificationOrchestration",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{failed_batches} failed batch(es) detected",
            )
        return HealthReport(
            component="NotificationOrchestration",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["NotificationOrchestrationHealthCheck"]
