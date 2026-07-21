"""Health check for the AI Governance & Compliance subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class AiGovernanceHealthCheck:
    """Health check for the AI Governance subsystem."""

    name: str = "ai_governance"

    def __init__(
        self,
        policy_count: int = 0,
        requirement_count: int = 0,
        last_check_passed: bool = True,
    ) -> None:
        """Initialize the health check.

        Args:
            policy_count: Number of governance policies.
            requirement_count: Number of compliance requirements.
            last_check_passed: Whether the last check passed.
        """
        self._policy_count = policy_count
        self._requirement_count = requirement_count
        self._last_check_passed = last_check_passed

    @property
    def policy_count(self) -> int:
        """Return the number of policies."""
        return self._policy_count

    @property
    def requirement_count(self) -> int:
        """Return the number of requirements."""
        return self._requirement_count

    @property
    def last_check_passed(self) -> bool:
        """Return whether the last check passed."""
        return self._last_check_passed

    async def check(self) -> HealthReport:
        """Check AI Governance health and return a report."""
        details = {
            "policy_count": self._policy_count,
            "requirement_count": self._requirement_count,
            "last_check_passed": self._last_check_passed,
        }

        if self._policy_count > 0 and self._last_check_passed:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=(
                    f"{self._policy_count} policy(ies), {self._requirement_count} requirement(s)."
                ),
                details=details,
            )

        if self._policy_count == 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.DEGRADED,
                message="No AI governance policies configured.",
                details=details,
            )

        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message="Last governance check failed.",
            details=details,
        )


__all__ = ["AiGovernanceHealthCheck"]
