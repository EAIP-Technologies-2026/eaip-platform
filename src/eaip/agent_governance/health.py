"""AgentGovernanceHealthCheck — reports the health of the agent governance subsystem."""

from __future__ import annotations

from eaip.agent_governance.service import AgentGovernanceService
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class AgentGovernanceHealthCheck(HealthCheck):
    """Health check for the agent governance subsystem."""

    name: str = "agent_governance"

    def __init__(self, service: AgentGovernanceService) -> None:
        """Initialize the AgentGovernanceHealthCheck.

        Args:
            service: The governance service to check.
        """
        self._service = service

    async def check(self) -> HealthReport:
        """Produce a health report for the agent governance subsystem."""
        policies = self._service.list_policies()
        total = len(policies)
        enabled_count = sum(1 for p in policies if p.enabled)
        disabled_count = total - enabled_count
        sop_count = len(self._service.list_sops())
        active_sops = sum(1 for s in self._service.list_sops() if s.status.name == "ACTIVE")

        if total == 0:
            return HealthReport(
                component="agent_governance",
                status=HealthStatus.HEALTHY,
                message="No governance policies registered",
                details={
                    "policies": {"total": 0, "enabled": 0, "disabled": 0},
                    "sops": {"total": sop_count, "active": active_sops},
                },
            )

        if disabled_count == 0:
            return HealthReport(
                component="agent_governance",
                status=HealthStatus.HEALTHY,
                message=f"{enabled_count}/{total} policies enabled",
                details={
                    "policies": {
                        "total": total,
                        "enabled": enabled_count,
                        "disabled": disabled_count,
                    },
                    "sops": {"total": sop_count, "active": active_sops},
                },
            )

        return HealthReport(
            component="agent_governance",
            status=HealthStatus.DEGRADED,
            message=f"{disabled_count} of {total} policies disabled",
            details={
                "policies": {
                    "total": total,
                    "enabled": enabled_count,
                    "disabled": disabled_count,
                },
                "sops": {"total": sop_count, "active": active_sops},
            },
        )


__all__ = ["AgentGovernanceHealthCheck"]
