"""Health check for the compliance subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ComplianceHealthCheck:
    """Health check for the compliance subsystem."""

    name: str = "compliance"

    def __init__(
        self,
        regulation_count: int = 0,
        control_count: int = 0,
        last_scan_passed: bool = True,
    ) -> None:
        """Initialize the compliance health check."""
        self._regulation_count = regulation_count
        self._control_count = control_count
        self._last_scan_passed = last_scan_passed

    @property
    def regulation_count(self) -> int:
        """Return the number of regulations."""
        return self._regulation_count

    @property
    def control_count(self) -> int:
        """Return the number of controls."""
        return self._control_count

    @property
    def last_scan_passed(self) -> bool:
        """Return whether the last scan passed."""
        return self._last_scan_passed

    async def check(self) -> HealthReport:
        """Check compliance health and return a report."""
        details = {
            "regulation_count": self._regulation_count,
            "control_count": self._control_count,
            "last_scan_passed": self._last_scan_passed,
        }
        if self._regulation_count > 0 and self._last_scan_passed:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=(
                    f"{self._regulation_count} regulation(s), {self._control_count} control(s)."
                ),
                details=details,
            )
        if self._regulation_count == 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.DEGRADED,
                message="No regulations configured.",
                details=details,
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message="Last compliance scan failed.",
            details=details,
        )


__all__ = ["ComplianceHealthCheck"]
