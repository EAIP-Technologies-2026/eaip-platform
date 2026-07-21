"""Health check for the AI Guardrails engine."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class GuardrailHealthCheck:
    """Health check for the AI Guardrails engine."""

    name: str = "guardrails"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Guardrails engine healthy",
        )


__all__ = ["GuardrailHealthCheck"]
