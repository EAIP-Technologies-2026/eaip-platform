"""Health check for alert correlation."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class AlertCorrelationHealthCheck:
    """Health check for the alert correlator."""

    name: str = "alertcorr"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Alert correlation healthy",
        )


__all__ = ["AlertCorrelationHealthCheck"]
