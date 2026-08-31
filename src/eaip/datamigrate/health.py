"""Health check for the data migration module."""

from __future__ import annotations

from eaip.datamigrate.engine import MigrationEngine
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class MigrationHealthCheck(HealthCheck):
    name: str = "datamigrate"

    def __init__(
        self,
        engine: MigrationEngine | None = None,
    ) -> None:
        self._engine = engine or MigrationEngine()

    async def check(self) -> HealthReport:
        total = len(self._engine._migrations)
        completed = sum(
            1 for m in self._engine._migrations.values() if m.status.value == "completed"
        )
        failed = sum(1 for m in self._engine._migrations.values() if m.status.value == "failed")
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message=f"{total} migration(s), {completed} completed, {failed} failed",
            details={
                "migrations_total": total,
                "migrations_completed": completed,
                "migrations_failed": failed,
                "batches_total": len(self._engine._batches),
            },
        )


__all__ = ["MigrationHealthCheck"]
