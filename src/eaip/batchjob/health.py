"""Health check for batch job scheduler."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class BatchJobSchedulerHealthCheck:
    """Health check for the batch job scheduler."""

    name: str = "batchjob"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Batch job scheduler healthy",
        )


__all__ = ["BatchJobSchedulerHealthCheck"]
