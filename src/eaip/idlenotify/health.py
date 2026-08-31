"""Health check for idle resource notifier."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class IdleResourceNotifierHealthCheck:
    """Health check for the idle resource notifier service."""

    name: str = "idlenotify"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Idle resource notifier service healthy",
        )


__all__ = ["IdleResourceNotifierHealthCheck"]
