"""Health check for AI validation."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class AIValidatorHealthCheck:
    """Health check for the AI validator service."""

    name: str = "aivalidator"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="AI validator service healthy",
        )


__all__ = ["AIValidatorHealthCheck"]
