"""Health check for data labeling."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class LabelingHealthCheck:
    """Health check for data labeling."""

    name: str = "labeling"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Labeling engine healthy",
        )


__all__ = ["LabelingHealthCheck"]
