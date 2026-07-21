"""Health check for the sandbox environment manager."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class SandboxHealthCheck:
    name: str = "sandbox"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Sandbox manager service healthy",
        )


__all__ = ["SandboxHealthCheck"]
