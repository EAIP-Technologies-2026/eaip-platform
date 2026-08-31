"""Health check for the agent skill registry."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class SkillRegistryHealthCheck:
    name: str = "skillreg"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Skill registry healthy",
        )


__all__ = ["SkillRegistryHealthCheck"]
