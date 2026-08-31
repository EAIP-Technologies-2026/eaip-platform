"""Health check for the masking policy module."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.maskpolicy.engine import MaskingPolicyEngine


class MaskPolicyHealthCheck(HealthCheck):
    name: str = "maskpolicy"

    def __init__(
        self,
        engine: MaskingPolicyEngine | None = None,
    ) -> None:
        self._engine = engine or MaskingPolicyEngine()

    async def check(self) -> HealthReport:
        policies = await self._engine.list_policies()
        active = [p for p in policies if p.status.value == "active"]
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message=f"{len(policies)} polic(ies), {len(active)} active",
            details={
                "policies_total": len(policies),
                "policies_active": len(active),
                "max_policies": self._engine.config.max_policies,
            },
        )


__all__ = ["MaskPolicyHealthCheck"]
