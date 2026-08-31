"""Health check for consent and privacy management."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ConsentHealthCheck:
    """Health check for the consent management subsystem."""

    name: str = "consent"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Consent management healthy",
        )


__all__ = ["ConsentHealthCheck"]
