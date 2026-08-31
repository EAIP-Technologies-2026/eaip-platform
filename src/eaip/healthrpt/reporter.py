"""HealthReporter — generate, track, and report on component health and SLA compliance."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from statistics import mean

from eaip.health.checks import HealthStatus
from eaip.healthrpt.events import (
    ComponentStatusChanged,
    ReportGenerated,
    SLAViolation,
)
from eaip.healthrpt.exceptions import (
    ComponentNotFoundError,
)
from eaip.healthrpt.models import (
    ComponentSummary,
    HealthReport,
    ReporterConfig,
    SLAResult,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class HealthReporter:
    """Central service for generating health reports and tracking SLA compliance."""

    def __init__(self, config: ReporterConfig | None = None) -> None:
        self._config = config or ReporterConfig()
        self._components: dict[str, ComponentSummary] = {}
        self._check_history: dict[str, list[HealthStatus]] = {}
        self._reports: list[HealthReport] = []
        self._component_statuses: dict[str, HealthStatus] = {}
        self._log = get_logger("eaip.healthrpt.reporter")

    @property
    def config(self) -> ReporterConfig:
        return self._config

    async def register_component(self, component: ComponentSummary) -> ComponentSummary:
        """Register a component for health tracking."""
        self._components[component.component_id] = component
        self._check_history[component.component_id] = []
        self._component_statuses[component.component_id] = component.status
        self._log.info("healthrpt.component.registered", component_id=component.component_id)
        return component

    async def unregister_component(self, component_id: str) -> None:
        """Unregister a component from health tracking."""
        if component_id not in self._components:
            raise ComponentNotFoundError(f"Component '{component_id}' not found")
        del self._components[component_id]
        self._check_history.pop(component_id, None)
        self._component_statuses.pop(component_id, None)
        self._log.info("healthrpt.component.unregistered", component_id=component_id)

    async def list_components(self) -> list[ComponentSummary]:
        """List all registered components."""
        return list(self._components.values())

    async def record_check(
        self,
        component_id: str,
        status: HealthStatus,
    ) -> ComponentSummary:
        """Record a health check result for a component."""
        component = self._components.get(component_id)
        if component is None:
            raise ComponentNotFoundError(f"Component '{component_id}' not found")

        previous_status = self._component_statuses.get(component_id, HealthStatus.HEALTHY)
        self._check_history.setdefault(component_id, []).append(status)

        check_count = len(self._check_history[component_id])
        pass_count = sum(1 for s in self._check_history[component_id] if s is HealthStatus.HEALTHY)
        fail_count = check_count - pass_count
        uptime = (pass_count / check_count * 100.0) if check_count > 0 else 100.0

        updated = component.model_copy(
            update={
                "status": status,
                "check_count": check_count,
                "pass_count": pass_count,
                "fail_count": fail_count,
                "last_checked_at": utc_now(),
                "uptime_percentage": round(uptime, 2),
            },
            deep=True,
        )
        self._components[component_id] = updated
        self._component_statuses[component_id] = status

        if status is not previous_status:
            event = ComponentStatusChanged(
                component_id=component_id,
                component_name=component.component_name,
                previous_status=previous_status.value,
                new_status=status.value,
            )
            self._log.info(
                "healthrpt.component.status_changed",
                component_id=component_id,
                previous=previous_status.value,
                new=status.value,
            )

        return updated

    async def generate_report(
        self, period_start: datetime | None = None, period_end: datetime | None = None
    ) -> HealthReport:
        """Generate a comprehensive health report."""
        now = utc_now()
        p_start = period_start or (now - timedelta(hours=self._config.report_interval_hours))
        p_end = period_end or now

        summaries = list(self._components.values())
        statuses = [s.status for s in summaries]
        uptimes = [s.uptime_percentage for s in summaries] if summaries else [100.0]
        overall_sla = round(mean(uptimes), 2)

        if overall_sla < self._config.unhealthy_threshold:
            overall_status = HealthStatus.UNHEALTHY
        elif overall_sla < self._config.degrade_threshold:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        report = HealthReport(
            report_id=str(uuid.uuid4()),
            period_start=p_start,
            period_end=p_end,
            component_summaries=tuple(summaries),
            overall_status=overall_status,
            sla_achievement=overall_sla,
        )
        self._reports.append(report)

        event = ReportGenerated(
            report_id=report.report_id,
            overall_status=overall_status.value,
            sla_achievement=overall_sla,
        )
        self._log.info(
            "healthrpt.report.generated",
            report_id=report.report_id,
            status=overall_status.value,
            sla=overall_sla,
        )

        for summary in summaries:
            if summary.uptime_percentage < self._config.sla_target_percentage:
                sla_event = SLAViolation(
                    component_id=summary.component_id,
                    component_name=summary.component_name,
                    sla_target=self._config.sla_target_percentage,
                    actual_achievement=summary.uptime_percentage,
                )
                self._log.warning(
                    "healthrpt.sla.violation",
                    component_id=summary.component_id,
                    uptime=summary.uptime_percentage,
                )

        return report

    async def get_sla_report(self, component_id: str) -> SLAResult:
        """Get the SLA report for a specific component."""
        component = self._components.get(component_id)
        if component is None:
            raise ComponentNotFoundError(f"Component '{component_id}' not found")
        now = utc_now()
        is_compliant = component.uptime_percentage >= self._config.sla_target_percentage
        return SLAResult(
            component_id=component_id,
            sla_target=self._config.sla_target_percentage,
            actual_achievement=component.uptime_percentage,
            compliant=is_compliant,
            period_start=now - timedelta(hours=self._config.report_interval_hours),
            period_end=now,
        )

    async def get_trend(self, component_id: str) -> list[HealthStatus]:
        """Get the health status trend for a component."""
        if component_id not in self._components:
            raise ComponentNotFoundError(f"Component '{component_id}' not found")
        return list(self._check_history.get(component_id, []))

    async def get_latest_report(self) -> HealthReport | None:
        """Get the most recently generated health report."""
        if not self._reports:
            return None
        return self._reports[-1]

    async def get_report_history(self) -> list[HealthReport]:
        """Get the full report history."""
        return list(self._reports)


__all__ = ["HealthReporter"]
