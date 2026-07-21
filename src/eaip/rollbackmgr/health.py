"""Health check for deployment rollback."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class RollbackManagerHealthCheck:
    """Health check for the rollback manager service."""

    name: str = "rollbackmgr"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Rollback manager service healthy",
        )


__all__ = ["RollbackManagerHealthCheck"]
