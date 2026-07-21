"""Health check for the platform audit viewer."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class AuditViewHealthCheck:
    name: str = "auditview"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Audit viewer service healthy",
        )


__all__ = ["AuditViewHealthCheck"]
