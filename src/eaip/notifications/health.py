"""Health check for the notification engine."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.notifications.engine import NotificationEngine


class NotificationHealthCheck:
    """Health check for notification engine components."""

    name: str = "notifications"

    def __init__(self, engine: NotificationEngine) -> None:
        self._engine = engine

    async def check(self) -> HealthReport:
        details = {
            "notifications_total": len(self._engine.list_notifications()),
            "notifications_pending": len(
                [n for n in self._engine.list_notifications() if n.status.value == "pending"]
            ),
            "notifications_failed": len(
                [n for n in self._engine.list_notifications() if n.status.value == "failed"]
            ),
        }
        status = HealthStatus.HEALTHY
        message = "Notification engine is operational"
        if details["notifications_failed"] > 10:
            status = HealthStatus.DEGRADED
            message = f"{details['notifications_failed']} failed notifications"

        return HealthReport(
            component="notifications",
            status=status,
            message=message,
            details=details,
        )


__all__ = ["NotificationHealthCheck"]
