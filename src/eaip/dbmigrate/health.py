"""Health check for database migration."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class DatabaseMigrationHealthCheck:
    """Health check for the database migration assistant."""

    name: str = "dbmigrate"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Database migration service healthy",
        )


__all__ = ["DatabaseMigrationHealthCheck"]
