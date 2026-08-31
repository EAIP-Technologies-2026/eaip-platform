"""Data quality health check — implements the HealthCheck protocol."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class DataQualityHealthCheck:
    """Health check for the data quality subsystem."""

    name: str = "dataquality"

    def __init__(
        self,
        active_rules: int = 0,
        active_checks: int = 0,
        last_check_passed: bool = True,
    ) -> None:
        """Initialize the data quality health check."""
        self._active_rules = active_rules
        self._active_checks = active_checks
        self._last_check_passed = last_check_passed

    @property
    def active_rules(self) -> int:
        """Return the number of active rules."""
        return self._active_rules

    @property
    def active_checks(self) -> int:
        """Return the number of active checks."""
        return self._active_checks

    @property
    def last_check_passed(self) -> bool:
        """Return whether the last check passed."""
        return self._last_check_passed

    async def check(self) -> HealthReport:
        """Check data quality health and return a report."""
        details = {
            "active_rules": self._active_rules,
            "active_checks": self._active_checks,
            "last_check_passed": self._last_check_passed,
        }
        if self._active_rules > 0 and self._last_check_passed:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=f"{self._active_rules} rule(s), {self._active_checks} check(s).",
                details=details,
            )
        if self._active_rules == 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.DEGRADED,
                message="No quality rules configured.",
                details=details,
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message="Last quality check failed.",
            details=details,
        )


__all__ = ["DataQualityHealthCheck"]
