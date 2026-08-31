"""Health check for disaster recovery module."""

from __future__ import annotations

from eaip.dr.failover import FailoverManager
from eaip.dr.models import PlanStatus
from eaip.dr.plans import DrPlanManager
from eaip.health.checks import HealthReport, HealthStatus


class DrHealthCheck:
    name: str = "eaip.dr"

    def __init__(
        self,
        plan_manager: DrPlanManager | None = None,
        failover_manager: FailoverManager | None = None,
    ) -> None:
        self._plan_manager = plan_manager
        self._failover_manager = failover_manager

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        issues: list[str] = []

        if self._plan_manager is not None:
            plans = self._plan_manager.list_plans()
            active_plans = [p for p in plans if p.status == PlanStatus.ACTIVE]
            untested_plans = [p for p in active_plans if p.last_tested_at is None]
            details["total_plans"] = len(plans)
            details["active_plans"] = len(active_plans)
            details["untested_plans"] = len(untested_plans)
            if untested_plans:
                issues.append(f"{len(untested_plans)} active plan(s) have never been tested")
        else:
            details["plans"] = "not_available"

        if self._failover_manager is not None:
            all_events = []
            if hasattr(self._failover_manager, "_events"):
                all_events = list(self._failover_manager._events.values())
            details["failover_events"] = len(all_events)
        else:
            details["failover"] = "not_available"

        status = HealthStatus.HEALTHY
        if issues:
            status = HealthStatus.DEGRADED

        return HealthReport(
            component="dr",
            status=status,
            message="; ".join(issues) if issues else "Disaster Recovery is operational",
            details=details,
        )


__all__ = ["DrHealthCheck"]
