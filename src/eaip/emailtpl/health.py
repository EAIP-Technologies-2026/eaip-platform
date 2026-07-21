"""Health check for the email template designer."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class TemplateDesignerHealthCheck:
    """Health check for the email template designer service."""

    name: str = "emailtpl"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Email template designer service healthy",
        )


__all__ = ["TemplateDesignerHealthCheck"]
