"""Health check for the knowledge governance subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class KnowledgeGovernanceHealthCheck:
    """Health check for the knowledge governance subsystem."""

    name: str = "knowledge_governance"

    def __init__(
        self,
        policy_count: int = 0,
        active_policies: int = 0,
        quality_checks_enabled: bool = True,
    ) -> None:
        """Initialize the knowledge governance health check.

        Args:
            policy_count: Number of governance policies.
            active_policies: Number of active policies.
            quality_checks_enabled: Whether quality checks are enabled.
        """
        self._policy_count = policy_count
        self._active_policies = active_policies
        self._quality_checks_enabled = quality_checks_enabled

    @property
    def policy_count(self) -> int:
        """Return the number of governance policies."""
        return self._policy_count

    @property
    def active_policies(self) -> int:
        """Return the number of active policies."""
        return self._active_policies

    @property
    def quality_checks_enabled(self) -> bool:
        """Return whether quality checks are enabled."""
        return self._quality_checks_enabled

    async def check(self) -> HealthReport:
        """Check knowledge governance health and return a report."""
        details = {
            "policy_count": self._policy_count,
            "active_policies": self._active_policies,
            "quality_checks_enabled": self._quality_checks_enabled,
        }
        if self._policy_count > 0 and self._active_policies > 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=(f"{self._policy_count} policy(ies), {self._active_policies} active."),
                details=details,
            )
        if self._policy_count == 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.DEGRADED,
                message="No governance policies configured.",
                details=details,
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message="No active governance policies.",
            details=details,
        )


__all__ = ["KnowledgeGovernanceHealthCheck"]
