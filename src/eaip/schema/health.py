"""Health check for the schema registry subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.schema.registry import SchemaRegistry


class SchemaHealthCheck:
    name: str = "schema"

    def __init__(self, registry: SchemaRegistry) -> None:
        self._registry = registry

    async def check(self) -> HealthReport:
        error_details: list[str] = []
        total_schemas = len(self._registry._schemas)
        total_versions = sum(len(v) for v in self._registry._versions.values())

        if total_schemas == 0:
            error_details.append("No schemas registered")

        status = HealthStatus.HEALTHY
        if error_details:
            status = HealthStatus.DEGRADED

        return HealthReport(
            component="schema",
            status=status,
            message="; ".join(error_details) if error_details else "Schema registry is operational",
            details={
                "total_schemas": total_schemas,
                "total_versions": total_versions,
            },
        )


__all__ = ["SchemaHealthCheck"]
