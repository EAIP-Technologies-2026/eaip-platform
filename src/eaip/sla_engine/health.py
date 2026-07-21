"""SLA health check — reports counts for definitions, monitors, and violations."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.sla_engine.service import SlaService


class SlaHealthCheck(HealthCheck):
    """Reports SLA engine health based on monitor and violation counts."""

    name: str = "eaip.sla_engine"

    def __init__(self, service: SlaService | None = None) -> None:
        self._service = service or SlaService()

    async def check(self) -> HealthReport:
        definitions = await self._service.list_definitions()
        monitors = await self._service.list_monitors()
        violations = await self._service.get_violations()

        breached = sum(1 for m in monitors if m.status.value == "breached")
        warnings = sum(1 for m in monitors if m.status.value == "warning")
        unresolved = sum(1 for v in violations if not v.resolved)

        details = {
            "total_definitions": len(definitions),
            "total_monitors": len(monitors),
            "total_violations": len(violations),
            "breached": breached,
            "warnings": warnings,
            "unresolved_violations": unresolved,
        }

        if breached > 0:
            return HealthReport(
                component="SlaEngine",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{breached} breached SLA(s) detected",
            )
        if unresolved > 0:
            return HealthReport(
                component="SlaEngine",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{unresolved} unresolved violation(s)",
            )
        return HealthReport(
            component="SlaEngine",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = [
    "SlaHealthCheck",
]
