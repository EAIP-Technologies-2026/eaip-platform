"""ExperimentTrackingHealthCheck — reports experiment tracking subsystem health."""

from __future__ import annotations

from eaip.experiment_tracking.service import ExperimentTrackingService
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class ExperimentTrackingHealthCheck(HealthCheck):
    """Reports experiment tracking subsystem health based on experiments and service state."""

    name: str = "eaip.experiment_tracking"

    def __init__(self, service: ExperimentTrackingService | None = None) -> None:
        self._service = service or ExperimentTrackingService()

    async def check(self) -> HealthReport:
        experiments = await self._service.list_experiments()
        active_count = sum(1 for e in experiments if e.status.value == "active")

        details = {
            "experiments_total": len(experiments),
            "experiments_active": active_count,
            "min_sample_size": self._service.config.min_sample_size,
            "confidence_level": self._service.config.confidence_level,
            "auto_stop": self._service.config.auto_stop,
        }

        if not experiments:
            return HealthReport(
                component="ExperimentTrackingService",
                status=HealthStatus.DEGRADED,
                details=details,
                message="no experiments registered",
            )

        return HealthReport(
            component="ExperimentTrackingService",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["ExperimentTrackingHealthCheck"]
