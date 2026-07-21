"""Health check for the archival subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class ArchiveHealthCheck(HealthCheck):
    """Health check that reports archive storage statistics."""

    name: str = "eaip.archive"

    def __init__(
        self,
        total_archives: int = 0,
        total_size_bytes: int = 0,
        pending_cleanups: int = 0,
    ) -> None:
        """Initialize the health check with archive statistics."""
        self._total_archives = total_archives
        self._total_size_bytes = total_size_bytes
        self._pending_cleanups = pending_cleanups

    async def check(self) -> HealthReport:
        """Run the health check and return a HealthReport."""
        details = {
            "total_archives": self._total_archives,
            "total_size_bytes": self._total_size_bytes,
            "pending_cleanups": self._pending_cleanups,
        }
        if self._pending_cleanups > 0:
            return HealthReport(
                component="Archive",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{self._pending_cleanups} pending cleanup(s)",
            )
        return HealthReport(
            component="Archive",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = [
    "ArchiveHealthCheck",
]
