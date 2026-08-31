"""Health check for agent templates."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class AgentTemplateHealthCheck:
    """Health check for agent templates."""

    name: str = "agenttpl"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Agent template engine healthy",
        )


__all__ = ["AgentTemplateHealthCheck"]
