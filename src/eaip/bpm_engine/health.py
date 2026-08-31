"""Health check for the BPM engine."""

from __future__ import annotations

from eaip.bpm_engine.models import ProcessStatus
from eaip.bpm_engine.service import BpmService
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class BpmHealthCheck(HealthCheck):
    """Reports BPM engine health based on definition and instance counts."""

    name: str = "eaip.bpm_engine"

    def __init__(self, service: BpmService | None = None) -> None:
        self._service = service or BpmService()

    async def check(self) -> HealthReport:
        definitions = await self._service.list_definitions()
        instances = await self._service.list_instances()
        running = await self._service.list_instances(status=ProcessStatus.RUNNING)
        failed = await self._service.list_instances(status=ProcessStatus.FAILED)

        details = {
            "definitions_deployed": len(definitions),
            "instances_total": len(instances),
            "instances_running": len(running),
            "instances_failed": len(failed),
        }

        if len(failed) > 0:
            return HealthReport(
                component="BpmEngine",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{len(failed)} failed process instance(s) detected",
            )
        return HealthReport(
            component="BpmEngine",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["BpmHealthCheck"]
