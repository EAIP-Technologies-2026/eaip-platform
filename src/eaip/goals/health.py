"""Goal health check — reports goal engine and tracker health."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class GoalHealthCheck(HealthCheck):
    """Reports goal subsystem health based on goal and KPI state."""

    name: str = "eaip.goals"

    def __init__(
        self,
        goal_count: int = 0,
        active_goal_count: int = 0,
        failed_goal_count: int = 0,
        tracked_kpis: int = 0,
    ) -> None:
        self._goal_count = goal_count
        self._active_goal_count = active_goal_count
        self._failed_goal_count = failed_goal_count
        self._tracked_kpis = tracked_kpis

    async def check(self) -> HealthReport:
        details = {
            "goals_total": self._goal_count,
            "goals_active": self._active_goal_count,
            "goals_failed": self._failed_goal_count,
            "kpis_tracked": self._tracked_kpis,
        }
        if self._failed_goal_count > 0:
            return HealthReport(
                component="GoalEngine",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{self._failed_goal_count} failed goal(s) detected",
            )
        if self._active_goal_count == 0 and self._goal_count > 0:
            return HealthReport(
                component="GoalEngine",
                status=HealthStatus.DEGRADED,
                details=details,
                message="no active goals",
            )
        return HealthReport(
            component="GoalEngine",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["GoalHealthCheck"]
