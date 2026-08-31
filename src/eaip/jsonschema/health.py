"""Health check for the JSON schema service."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.jsonschema.service import JSONSchemaService


class SchemaHealthCheck:
    name: str = "jsonschema"

    def __init__(self, service: JSONSchemaService) -> None:
        self._service = service

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            schemas = await self._service.list_schemas()
            details["schema_count"] = len(schemas)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"JSON schema service unavailable: {exc}",
                details={"error": str(exc)},
            )

        active = sum(1 for s in schemas if s.status.value == "active")
        details["active_schemas"] = active

        status = HealthStatus.HEALTHY
        messages: list[str] = []

        if active == 0 and len(schemas) > 0:
            status = HealthStatus.DEGRADED
            messages.append("No active schemas")

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "JSON schema service healthy",
            details=details,
        )


__all__ = ["SchemaHealthCheck"]
