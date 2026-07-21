"""Health check for the document redaction service."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class RedactionHealthCheck:
    """Health check for the document redaction service."""

    name: str = "docredact"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Document redaction service healthy",
        )


__all__ = ["RedactionHealthCheck"]
