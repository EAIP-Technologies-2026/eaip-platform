"""Health check for the knowledge curation service."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class CurationHealthCheck:
    """Health check for the knowledge curation service."""

    name: str = "curation"

    def __init__(self, pending_count: int = 0, total_submissions: int = 0) -> None:
        self._pending_count = pending_count
        self._total_submissions = total_submissions

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        details = {
            "pending_count": self._pending_count,
            "total_submissions": self._total_submissions,
        }
        if self._pending_count < 10:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=f"{self._total_submissions} submission(s), {self._pending_count} pending",
                details=details,
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message=f"{self._pending_count} submissions pending review",
            details=details,
        )


__all__ = ["CurationHealthCheck"]
