"""Health check for the content moderation service."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ContentModerationHealthCheck:
    name: str = "contentmod"

    def __init__(self, rule_count: int = 0, pending_count: int = 0) -> None:
        self._rule_count = rule_count
        self._pending_count = pending_count

    async def check(self) -> HealthReport:
        details = {
            "rule_count": self._rule_count,
            "pending_count": self._pending_count,
        }
        status = HealthStatus.HEALTHY
        message = "Content moderation service is operational"

        if self._rule_count == 0:
            status = HealthStatus.DEGRADED
            message = "No moderation rules configured"

        return HealthReport(
            component="contentmod",
            status=status,
            message=message,
            details=details,
        )


__all__ = ["ContentModerationHealthCheck"]
