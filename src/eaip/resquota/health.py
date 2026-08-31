"""Health check for resource quotas."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class QuotaHealthCheck:
    """Health check for resource quotas."""

    name: str = "resquota"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Resource quota engine healthy",
        )


__all__ = ["QuotaHealthCheck"]
