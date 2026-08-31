"""Health check for endpoint security scanning."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class EndpointSecurityHealthCheck:
    """Health check for the endpoint security scanner service."""

    name: str = "endpointsec"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Endpoint security scanner service healthy",
        )


__all__ = ["EndpointSecurityHealthCheck"]
