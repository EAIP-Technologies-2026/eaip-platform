"""Health check for the Health Aggregator itself."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.health.checks import HealthReport, HealthStatus

if TYPE_CHECKING:
    from eaip.healthagg.aggregator import HealthAggregator


class HealthAggHealthCheck:
    name: str = "healthagg"

    def __init__(self, aggregator: HealthAggregator) -> None:
        self._aggregator = aggregator

    async def check(self) -> HealthReport:
        components = self._aggregator._checks
        snapshots = self._aggregator._snapshots
        error_details: list[str] = []

        if not components:
            error_details.append("No components registered")

        status = HealthStatus.DEGRADED if error_details else HealthStatus.HEALTHY

        return HealthReport(
            component="healthagg",
            status=status,
            message="; ".join(error_details)
            if error_details
            else "Health Aggregator is operational",
            details={
                "components_total": len(components),
                "snapshots_total": len(snapshots),
                "dependencies_total": len(self._aggregator.dependency_graph._dependencies),
            },
        )


__all__ = ["HealthAggHealthCheck"]
