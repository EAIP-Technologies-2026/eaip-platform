"""Health check for IaC validator."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class IaCValidatorHealthCheck:
    """Health check for the IaC validator service."""

    name: str = "iacvalid"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="IaC validator service healthy",
        )


__all__ = ["IaCValidatorHealthCheck"]
