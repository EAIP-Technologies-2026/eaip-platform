"""Health check for the diagnostic data collector."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class DiagnosticHealthCheck:
    """Health check for the diagnostic collector service."""

    name: str = "diagnostic"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Diagnostic collector service healthy",
        )


__all__ = ["DiagnosticHealthCheck"]
