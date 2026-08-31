"""Health check for the audit subsystem."""

from __future__ import annotations

from eaip.audit.logger import AuditLogger
from eaip.health.checks import HealthReport, HealthStatus


class AuditHealthCheck:
    name: str = "audit"

    def __init__(self, logger: AuditLogger) -> None:
        self._logger = logger

    async def check(self) -> HealthReport:
        error_details: list[str] = []
        total_events = len(self._logger._store)

        if total_events == 0:
            error_details.append("No audit events recorded")

        status = HealthStatus.HEALTHY
        if error_details:
            status = HealthStatus.DEGRADED

        return HealthReport(
            component="audit",
            status=status,
            message="; ".join(error_details) if error_details else "Audit subsystem is operational",
            details={
                "total_events": total_events,
            },
        )


__all__ = ["AuditHealthCheck"]
