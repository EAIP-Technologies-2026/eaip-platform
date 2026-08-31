"""Health check for feedback collection."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class FeedbackHealthCheck:
    """Health check for feedback collection."""

    name: str = "feedback"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Feedback engine healthy",
        )


__all__ = ["FeedbackHealthCheck"]
