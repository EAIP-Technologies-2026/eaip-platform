"""PolicyHealthCheck — reports the health of the policy subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.policy.registry import PolicyRegistry


class PolicyHealthCheck(HealthCheck):
    """Health check for the policy subsystem."""

    name: str = "policy"

    def __init__(self, registry: PolicyRegistry) -> None:
        """Initialize the PolicyHealthCheck.

        Args:
            registry: The policy registry to check.
        """
        self._registry = registry

    async def check(self) -> HealthReport:
        """Produce a health report for the policy subsystem."""
        all_policies = self._registry.all()
        total = len(all_policies)
        enabled_count = len(self._registry.enabled())
        disabled_count = total - enabled_count

        if total == 0:
            return HealthReport(
                component="policy",
                status=HealthStatus.HEALTHY,
                message="No policies registered",
                details={"total": 0, "enabled": 0, "disabled": 0},
            )

        if disabled_count == 0:
            return HealthReport(
                component="policy",
                status=HealthStatus.HEALTHY,
                message=f"{enabled_count}/{total} policies enabled",
                details={
                    "total": total,
                    "enabled": enabled_count,
                    "disabled": disabled_count,
                },
            )

        return HealthReport(
            component="policy",
            status=HealthStatus.DEGRADED,
            message=f"{disabled_count} of {total} policies disabled",
            details={
                "total": total,
                "enabled": enabled_count,
                "disabled": disabled_count,
            },
        )


__all__ = ["PolicyHealthCheck"]
