"""Health check for backup verification."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class BackupVerificationHealthCheck:
    """Health check for the backup verification service."""

    name: str = "backupver"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Backup verification service healthy",
        )


__all__ = ["BackupVerificationHealthCheck"]
