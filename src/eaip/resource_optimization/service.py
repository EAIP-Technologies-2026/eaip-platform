"""ResourceOptimizationService — metrics, rules, recommendations, actions, forecasts, dashboards."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from eaip.logging.context import get_logger
from eaip.resource_optimization.exceptions import (
    ResourceActionError,
    ResourceAllocationError,
    ResourceConstraintError,
    ResourceDemandForecastError,
    ResourceMetricsError,
    ResourceOptimizationConfigError,
    ResourceRecommendationError,
)
from eaip.resource_optimization.models import (
    OptimizationStrategy,
    RecommendationPriority,
    ResourceAction,
    ResourceActionStatus,
    ResourceAllocation,
    ResourceConstraint,
    ResourceDemandForecast,
    ResourceMetrics,
    ResourceOptimizationConfig,
    ResourceOptimizationDashboard,
    ResourceOptimizationHistory,
    ResourceOptimizationReport,
    ResourceOptimizationRule,
    ResourceOptimizationSchedule,
    ResourceRecommendation,
    ResourceType,
    ResourceUtilization,
)
from eaip.shared.time import utc_now


class ResourceOptimizationService:
    """Central service for resource optimization: metrics, rules, recommendations, and actions."""

    def __init__(self, config: ResourceOptimizationConfig | None = None) -> None:
        self._config = config or ResourceOptimizationConfig()
        self._metrics: dict[str, ResourceMetrics] = {}
        self._utilizations: dict[str, ResourceUtilization] = {}
        self._rules: dict[str, ResourceOptimizationRule] = {}
        self._recommendations: dict[str, ResourceRecommendation] = {}
        self._actions: dict[str, ResourceAction] = {}
        self._reports: dict[str, ResourceOptimizationReport] = {}
        self._schedules: dict[str, ResourceOptimizationSchedule] = {}
        self._history: list[ResourceOptimizationHistory] = []
        self._allocations: dict[str, ResourceAllocation] = {}
        self._forecasts: dict[str, ResourceDemandForecast] = {}
        self._dashboards: dict[str, ResourceOptimizationDashboard] = {}
        self._constraints: list[ResourceConstraint] = []
        self._log = get_logger("eaip.resource_optimization.service")

    @property
    def config(self) -> ResourceOptimizationConfig:
        return self._config

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    async def update_config(self, **changes: Any) -> ResourceOptimizationConfig:
        merged = {**self._config.model_dump(), **changes}
        self._config = ResourceOptimizationConfig(**merged)
        self._log.info("resource_optimization.config.updated", changes=changes)
        return self._config

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    async def record_metrics(
        self,
        metrics_id: str,
        resource_id: str,
        resource_type: ResourceType,
        cpu_utilization: float = 0.0,
        memory_utilization: float = 0.0,
        disk_utilization: float = 0.0,
        network_in_bytes: int = 0,
        network_out_bytes: int = 0,
        request_count: int = 0,
        error_count: int = 0,
        latency_p99_ms: float = 0.0,
        cost_per_hour: float = 0.0,
        metadata: dict[str, str] | None = None,
    ) -> ResourceMetrics:
        metrics = ResourceMetrics(
            id=metrics_id,
            resource_id=resource_id,
            resource_type=resource_type,
            cpu_utilization=cpu_utilization,
            memory_utilization=memory_utilization,
            disk_utilization=disk_utilization,
            network_in_bytes=network_in_bytes,
            network_out_bytes=network_out_bytes,
            request_count=request_count,
            error_count=error_count,
            latency_p99_ms=latency_p99_ms,
            cost_per_hour=cost_per_hour,
            metadata=metadata or {},
        )
        self._metrics[metrics_id] = metrics
        self._log.info("resource_optimization.metrics.recorded", metrics_id=metrics_id)
        return metrics

    async def get_metrics(self, metrics_id: str) -> ResourceMetrics:
        metrics = self._metrics.get(metrics_id)
        if metrics is None:
            raise ResourceMetricsError(f"metrics not found: {metrics_id!r}")
        return metrics

    async def list_metrics(
        self,
        resource_id: str | None = None,
        resource_type: ResourceType | None = None,
    ) -> list[ResourceMetrics]:
        result = list(self._metrics.values())
        if resource_id:
            result = [m for m in result if m.resource_id == resource_id]
        if resource_type:
            result = [m for m in result if m.resource_type == resource_type]
        return result

    # ------------------------------------------------------------------
    # Utilization
    # ------------------------------------------------------------------

    async def analyze_utilization(
        self,
        resource_id: str,
        resource_type: ResourceType,
        metrics_list: list[ResourceMetrics],
    ) -> ResourceUtilization:
        if not metrics_list:
            raise ResourceMetricsError("at least one metrics data point is required")

        cpu_values = [m.cpu_utilization for m in metrics_list]
        mem_values = [m.memory_utilization for m in metrics_list]
        disk_values = [m.disk_utilization for m in metrics_list]

        avg_cpu = sum(cpu_values) / len(cpu_values)
        peak_cpu = max(cpu_values)
        avg_mem = sum(mem_values) / len(mem_values)
        peak_mem = max(mem_values)
        avg_disk = sum(disk_values) / len(disk_values)

        timestamps = [m.timestamp for m in metrics_list]
        period_start = min(timestamps)
        period_end = max(timestamps)

        idle_threshold = self._config.idle_threshold_hours
        idle_hours = 0
        recent = [
            m for m in metrics_list if m.cpu_utilization < 5.0 and m.memory_utilization < 10.0
        ]
        if recent and timestamps:
            idle_span = (timestamps[-1] - recent[0].timestamp).total_seconds() / 3600
            idle_hours = max(0, int(idle_span))
        is_idle = idle_hours >= idle_threshold

        utilization = ResourceUtilization(
            resource_id=resource_id,
            resource_type=resource_type,
            avg_cpu_utilization=round(avg_cpu, 2),
            peak_cpu_utilization=round(peak_cpu, 2),
            avg_memory_utilization=round(avg_mem, 2),
            peak_memory_utilization=round(peak_mem, 2),
            avg_disk_utilization=round(avg_disk, 2),
            is_idle=is_idle,
            idle_hours=idle_hours,
            period_start=period_start,
            period_end=period_end,
            data_points=len(metrics_list),
        )
        self._utilizations[resource_id] = utilization
        self._log.info(
            "resource_optimization.utilization.analyzed",
            resource_id=resource_id,
            avg_cpu=avg_cpu,
            is_idle=is_idle,
        )
        return utilization

    async def get_utilization(self, resource_id: str) -> ResourceUtilization:
        utilization = self._utilizations.get(resource_id)
        if utilization is None:
            raise ResourceMetricsError(f"utilization not found: {resource_id!r}")
        return utilization

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------

    async def create_rule(
        self,
        rule_id: str,
        name: str,
        strategy: OptimizationStrategy,
        description: str = "",
        resource_type: ResourceType | None = None,
        condition_expression: str = "",
        priority: RecommendationPriority = RecommendationPriority.MEDIUM,
        enabled: bool = True,
        metadata: dict[str, str] | None = None,
    ) -> ResourceOptimizationRule:
        if rule_id in self._rules:
            raise ResourceOptimizationConfigError(f"rule already exists: {rule_id!r}")
        rule = ResourceOptimizationRule(
            id=rule_id,
            name=name,
            description=description,
            resource_type=resource_type,
            condition_expression=condition_expression,
            strategy=strategy,
            priority=priority,
            enabled=enabled,
            metadata=metadata or {},
        )
        self._rules[rule_id] = rule
        self._log.info("resource_optimization.rule.created", rule_id=rule_id, name=name)
        return rule

    async def get_rule(self, rule_id: str) -> ResourceOptimizationRule:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise ResourceOptimizationConfigError(f"rule not found: {rule_id!r}")
        return rule

    async def update_rule(self, rule_id: str, **changes: Any) -> ResourceOptimizationRule:
        rule = await self.get_rule(rule_id)
        merged = {**rule.model_dump(), **changes}
        updated = ResourceOptimizationRule(**merged)
        self._rules[rule_id] = updated
        self._log.info("resource_optimization.rule.updated", rule_id=rule_id)
        return updated

    async def list_rules(
        self,
        resource_type: ResourceType | None = None,
        strategy: OptimizationStrategy | None = None,
        enabled: bool | None = None,
    ) -> list[ResourceOptimizationRule]:
        result = list(self._rules.values())
        if resource_type:
            result = [r for r in result if r.resource_type == resource_type]
        if strategy:
            result = [r for r in result if r.strategy == strategy]
        if enabled is not None:
            result = [r for r in result if r.enabled == enabled]
        return result

    async def delete_rule(self, rule_id: str) -> None:
        if rule_id not in self._rules:
            raise ResourceOptimizationConfigError(f"rule not found: {rule_id!r}")
        del self._rules[rule_id]
        self._log.info("resource_optimization.rule.deleted", rule_id=rule_id)

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    async def generate_recommendation(
        self,
        recommendation_id: str,
        resource_id: str,
        resource_type: ResourceType,
        strategy: OptimizationStrategy,
        priority: RecommendationPriority,
        title: str,
        description: str = "",
        current_value: str = "",
        recommended_value: str = "",
        estimated_savings_per_hour: float = 0.0,
        estimated_savings_per_month: float = 0.0,
        risk_score: float = 0.0,
        confidence: float = 0.0,
        rule_id: str = "",
        metadata: dict[str, str] | None = None,
    ) -> ResourceRecommendation:
        recommendation = ResourceRecommendation(
            id=recommendation_id,
            resource_id=resource_id,
            resource_type=resource_type,
            rule_id=rule_id,
            strategy=strategy,
            priority=priority,
            title=title,
            description=description,
            current_value=current_value,
            recommended_value=recommended_value,
            estimated_savings_per_hour=estimated_savings_per_hour,
            estimated_savings_per_month=estimated_savings_per_month,
            risk_score=risk_score,
            confidence=confidence,
            metadata=metadata or {},
        )
        self._recommendations[recommendation_id] = recommendation
        self._log.info(
            "resource_optimization.recommendation.generated",
            recommendation_id=recommendation_id,
        )
        return recommendation

    async def get_recommendation(self, recommendation_id: str) -> ResourceRecommendation:
        recommendation = self._recommendations.get(recommendation_id)
        if recommendation is None:
            raise ResourceRecommendationError(f"recommendation not found: {recommendation_id!r}")
        return recommendation

    async def list_recommendations(
        self,
        resource_id: str | None = None,
        resource_type: ResourceType | None = None,
        strategy: OptimizationStrategy | None = None,
        priority: RecommendationPriority | None = None,
        include_applied: bool = False,
        include_dismissed: bool = False,
    ) -> list[ResourceRecommendation]:
        result = list(self._recommendations.values())
        if resource_id:
            result = [r for r in result if r.resource_id == resource_id]
        if resource_type:
            result = [r for r in result if r.resource_type == resource_type]
        if strategy:
            result = [r for r in result if r.strategy == strategy]
        if priority:
            result = [r for r in result if r.priority == priority]
        if not include_applied:
            result = [r for r in result if r.applied_at is None]
        if not include_dismissed:
            result = [r for r in result if r.dismissed_at is None]
        return result

    async def apply_recommendation(self, recommendation_id: str) -> ResourceRecommendation:
        recommendation = await self.get_recommendation(recommendation_id)
        if recommendation.applied_at is not None:
            raise ResourceRecommendationError(
                f"recommendation already applied: {recommendation_id!r}"
            )
        merged = {
            **recommendation.model_dump(),
            "applied_at": utc_now(),
        }
        updated = ResourceRecommendation(**merged)
        self._recommendations[recommendation_id] = updated
        self._log.info(
            "resource_optimization.recommendation.applied",
            recommendation_id=recommendation_id,
        )
        return updated

    async def dismiss_recommendation(
        self, recommendation_id: str, reason: str = ""
    ) -> ResourceRecommendation:
        recommendation = await self.get_recommendation(recommendation_id)
        if recommendation.dismissed_at is not None:
            raise ResourceRecommendationError(
                f"recommendation already dismissed: {recommendation_id!r}"
            )
        merged = {
            **recommendation.model_dump(),
            "dismissed_at": utc_now(),
        }
        updated = ResourceRecommendation(**merged)
        self._recommendations[recommendation_id] = updated
        self._log.info(
            "resource_optimization.recommendation.dismissed",
            recommendation_id=recommendation_id,
            reason=reason,
        )
        return updated

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    async def start_action(
        self,
        action_id: str,
        recommendation_id: str,
        resource_id: str,
        resource_type: ResourceType,
        action_type: str,
        metadata: dict[str, str] | None = None,
    ) -> ResourceAction:
        action = ResourceAction(
            id=action_id,
            recommendation_id=recommendation_id,
            resource_id=resource_id,
            resource_type=resource_type,
            action_type=action_type,
            status=ResourceActionStatus.RUNNING,
            started_at=utc_now(),
            metadata=metadata or {},
        )
        self._actions[action_id] = action
        self._log.info("resource_optimization.action.started", action_id=action_id)
        return action

    async def complete_action(
        self,
        action_id: str,
        result: dict[str, str] | None = None,
    ) -> ResourceAction:
        action = self._actions.get(action_id)
        if action is None:
            raise ResourceActionError(f"action not found: {action_id!r}")
        merged = {
            **action.model_dump(),
            "status": ResourceActionStatus.COMPLETED,
            "completed_at": utc_now(),
            "result": result or {},
        }
        updated = ResourceAction(**merged)
        self._actions[action_id] = updated
        self._log.info("resource_optimization.action.completed", action_id=action_id)
        return updated

    async def fail_action(
        self,
        action_id: str,
        error_message: str = "",
    ) -> ResourceAction:
        action = self._actions.get(action_id)
        if action is None:
            raise ResourceActionError(f"action not found: {action_id!r}")
        merged = {
            **action.model_dump(),
            "status": ResourceActionStatus.FAILED,
            "completed_at": utc_now(),
            "error_message": error_message,
        }
        updated = ResourceAction(**merged)
        self._actions[action_id] = updated
        self._log.info("resource_optimization.action.failed", action_id=action_id)
        return updated

    async def get_action(self, action_id: str) -> ResourceAction:
        action = self._actions.get(action_id)
        if action is None:
            raise ResourceActionError(f"action not found: {action_id!r}")
        return action

    async def list_actions(
        self,
        resource_id: str | None = None,
        status: ResourceActionStatus | None = None,
    ) -> list[ResourceAction]:
        result = list(self._actions.values())
        if resource_id:
            result = [a for a in result if a.resource_id == resource_id]
        if status:
            result = [a for a in result if a.status == status]
        return result

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    async def generate_report(
        self,
        report_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> ResourceOptimizationReport:
        recommendations = list(self._recommendations.values())
        actions = list(self._actions.values())

        critical = sum(1 for r in recommendations if r.priority == RecommendationPriority.CRITICAL)
        high = sum(1 for r in recommendations if r.priority == RecommendationPriority.HIGH)
        medium = sum(1 for r in recommendations if r.priority == RecommendationPriority.MEDIUM)
        low = sum(1 for r in recommendations if r.priority == RecommendationPriority.LOW)
        total_savings = sum(r.estimated_savings_per_month for r in recommendations)
        actions_taken = sum(1 for a in actions if a.status == ResourceActionStatus.COMPLETED)
        actions_failed = sum(1 for a in actions if a.status == ResourceActionStatus.FAILED)

        report = ResourceOptimizationReport(
            id=report_id,
            period_start=period_start,
            period_end=period_end,
            total_resources_analyzed=len(self._metrics),
            total_recommendations=len(recommendations),
            total_estimated_savings_per_month=round(total_savings, 2),
            critical_recommendations=critical,
            high_recommendations=high,
            medium_recommendations=medium,
            low_recommendations=low,
            actions_taken=actions_taken,
            actions_failed=actions_failed,
        )
        self._reports[report_id] = report
        self._log.info("resource_optimization.report.generated", report_id=report_id)
        return report

    async def get_report(self, report_id: str) -> ResourceOptimizationReport:
        report = self._reports.get(report_id)
        if report is None:
            raise ResourceRecommendationError(f"report not found: {report_id!r}")
        return report

    async def list_reports(self) -> list[ResourceOptimizationReport]:
        return list(self._reports.values())

    # ------------------------------------------------------------------
    # Schedules
    # ------------------------------------------------------------------

    async def create_schedule(
        self,
        schedule_id: str,
        name: str,
        interval_hours: int = 24,
        description: str = "",
        resource_types: tuple[ResourceType, ...] | None = None,
        auto_apply: bool = False,
        enabled: bool = True,
        metadata: dict[str, str] | None = None,
    ) -> ResourceOptimizationSchedule:
        if schedule_id in self._schedules:
            raise ResourceOptimizationConfigError(f"schedule already exists: {schedule_id!r}")
        schedule = ResourceOptimizationSchedule(
            id=schedule_id,
            name=name,
            description=description,
            interval_hours=interval_hours,
            resource_types=resource_types or (),
            auto_apply=auto_apply,
            enabled=enabled,
            metadata=metadata or {},
        )
        self._schedules[schedule_id] = schedule
        self._log.info("resource_optimization.schedule.created", schedule_id=schedule_id)
        return schedule

    async def get_schedule(self, schedule_id: str) -> ResourceOptimizationSchedule:
        schedule = self._schedules.get(schedule_id)
        if schedule is None:
            raise ResourceOptimizationConfigError(f"schedule not found: {schedule_id!r}")
        return schedule

    async def list_schedules(self) -> list[ResourceOptimizationSchedule]:
        return list(self._schedules.values())

    async def delete_schedule(self, schedule_id: str) -> None:
        if schedule_id not in self._schedules:
            raise ResourceOptimizationConfigError(f"schedule not found: {schedule_id!r}")
        del self._schedules[schedule_id]
        self._log.info("resource_optimization.schedule.deleted", schedule_id=schedule_id)

    # ------------------------------------------------------------------
    # Allocations
    # ------------------------------------------------------------------

    async def record_allocation(
        self,
        allocation_id: str,
        resource_id: str,
        resource_type: ResourceType,
        allocated_capacity: float = 0.0,
        used_capacity: float = 0.0,
        requested_capacity: float = 0.0,
        metadata: dict[str, str] | None = None,
    ) -> ResourceAllocation:
        efficiency = (used_capacity / allocated_capacity * 100) if allocated_capacity > 0 else 0.0
        allocation = ResourceAllocation(
            id=allocation_id,
            resource_id=resource_id,
            resource_type=resource_type,
            allocated_capacity=allocated_capacity,
            used_capacity=used_capacity,
            requested_capacity=requested_capacity,
            over_allocated=used_capacity < allocated_capacity * 0.5,
            under_allocated=used_capacity > allocated_capacity * 0.95,
            allocation_efficiency=round(efficiency, 2),
            metadata=metadata or {},
        )
        self._allocations[allocation_id] = allocation
        self._log.info("resource_optimization.allocation.recorded", allocation_id=allocation_id)
        return allocation

    async def get_allocation(self, allocation_id: str) -> ResourceAllocation:
        allocation = self._allocations.get(allocation_id)
        if allocation is None:
            raise ResourceAllocationError(f"allocation not found: {allocation_id!r}")
        return allocation

    async def list_allocations(self, resource_id: str | None = None) -> list[ResourceAllocation]:
        result = list(self._allocations.values())
        if resource_id:
            result = [a for a in result if a.resource_id == resource_id]
        return result

    async def adjust_allocation(
        self,
        allocation_id: str,
        new_allocated_capacity: float,
    ) -> ResourceAllocation:
        allocation = await self.get_allocation(allocation_id)
        if new_allocated_capacity < 0:
            raise ResourceAllocationError("allocated capacity must be non-negative")
        efficiency = (
            (allocation.used_capacity / new_allocated_capacity * 100)
            if new_allocated_capacity > 0
            else 0.0
        )
        merged = {
            **allocation.model_dump(),
            "allocated_capacity": new_allocated_capacity,
            "over_allocated": allocation.used_capacity < new_allocated_capacity * 0.5,
            "under_allocated": allocation.used_capacity > new_allocated_capacity * 0.95,
            "allocation_efficiency": round(efficiency, 2),
        }
        updated = ResourceAllocation(**merged)
        self._allocations[allocation_id] = updated
        self._log.info(
            "resource_optimization.allocation.adjusted",
            allocation_id=allocation_id,
        )
        return updated

    # ------------------------------------------------------------------
    # Forecasts
    # ------------------------------------------------------------------

    async def compute_forecast(
        self,
        forecast_id: str,
        resource_id: str,
        resource_type: ResourceType,
        metrics_list: list[ResourceMetrics],
        horizon_hours: int = 24,
    ) -> ResourceDemandForecast:
        if not metrics_list:
            raise ResourceDemandForecastError("at least one metrics data point is required")

        cpu_values = [m.cpu_utilization for m in metrics_list]
        mem_values = [m.memory_utilization for m in metrics_list]

        n = len(cpu_values)
        x_mean = (n - 1) / 2
        cpu_mean = sum(cpu_values) / n
        mem_mean = sum(mem_values) / n

        cpu_num = sum((i - x_mean) * (v - cpu_mean) for i, v in enumerate(cpu_values))
        den = sum((i - x_mean) ** 2 for i in range(n))
        cpu_slope = cpu_num / den if den != 0 else 0

        mem_num = sum((i - x_mean) * (v - mem_mean) for i, v in enumerate(mem_values))
        mem_slope = mem_num / den if den != 0 else 0

        predicted_cpu = cpu_slope * n + (cpu_mean - cpu_slope * x_mean)
        predicted_mem = mem_slope * n + (mem_mean - mem_slope * x_mean)

        predicted_cpu = max(0.0, min(100.0, predicted_cpu))
        predicted_mem = max(0.0, min(100.0, predicted_mem))

        if cpu_slope > 0.5:
            trend = "increasing"
        elif cpu_slope < -0.5:
            trend = "decreasing"
        else:
            trend = "stable"

        forecast = ResourceDemandForecast(
            id=forecast_id,
            resource_id=resource_id,
            resource_type=resource_type,
            forecast_horizon_hours=horizon_hours,
            predicted_cpu_utilization=round(predicted_cpu, 2),
            predicted_memory_utilization=round(predicted_mem, 2),
            predicted_demand_trend=trend,
            confidence_lower=round(max(0.0, predicted_cpu - 10.0), 2),
            confidence_upper=round(min(100.0, predicted_cpu + 10.0), 2),
            valid_until=utc_now() + timedelta(hours=horizon_hours),
        )
        self._forecasts[forecast_id] = forecast
        self._log.info(
            "resource_optimization.forecast.computed",
            forecast_id=forecast_id,
            trend=trend,
        )
        return forecast

    async def get_forecast(self, forecast_id: str) -> ResourceDemandForecast:
        forecast = self._forecasts.get(forecast_id)
        if forecast is None:
            raise ResourceDemandForecastError(f"forecast not found: {forecast_id!r}")
        return forecast

    async def list_forecasts(self, resource_id: str | None = None) -> list[ResourceDemandForecast]:
        result = list(self._forecasts.values())
        if resource_id:
            result = [f for f in result if f.resource_id == resource_id]
        return result

    # ------------------------------------------------------------------
    # Dashboards
    # ------------------------------------------------------------------

    async def create_dashboard(
        self,
        dashboard_id: str,
        name: str,
        description: str = "",
        widgets: tuple[str, ...] | None = None,
        resource_ids: tuple[str, ...] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> ResourceOptimizationDashboard:
        if dashboard_id in self._dashboards:
            raise ResourceOptimizationConfigError(f"dashboard already exists: {dashboard_id!r}")
        dashboard = ResourceOptimizationDashboard(
            id=dashboard_id,
            name=name,
            description=description,
            widgets=widgets or (),
            resource_ids=resource_ids or (),
            metadata=metadata or {},
        )
        self._dashboards[dashboard_id] = dashboard
        self._log.info(
            "resource_optimization.dashboard.created",
            dashboard_id=dashboard_id,
        )
        return dashboard

    async def get_dashboard(self, dashboard_id: str) -> ResourceOptimizationDashboard:
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard is None:
            raise ResourceOptimizationConfigError(f"dashboard not found: {dashboard_id!r}")
        return dashboard

    async def update_dashboard(
        self, dashboard_id: str, **changes: Any
    ) -> ResourceOptimizationDashboard:
        dashboard = await self.get_dashboard(dashboard_id)
        merged = {**dashboard.model_dump(), **changes}
        updated = ResourceOptimizationDashboard(**merged)
        self._dashboards[dashboard_id] = updated
        self._log.info(
            "resource_optimization.dashboard.updated",
            dashboard_id=dashboard_id,
        )
        return updated

    async def list_dashboards(self) -> list[ResourceOptimizationDashboard]:
        return list(self._dashboards.values())

    async def delete_dashboard(self, dashboard_id: str) -> None:
        if dashboard_id not in self._dashboards:
            raise ResourceOptimizationConfigError(f"dashboard not found: {dashboard_id!r}")
        del self._dashboards[dashboard_id]
        self._log.info(
            "resource_optimization.dashboard.deleted",
            dashboard_id=dashboard_id,
        )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    async def detect_constraint(
        self,
        constraint_id: str,
        resource_id: str,
        resource_type: ResourceType,
        constraint_type: str,
        constraint_value: str = "",
        description: str = "",
        metadata: dict[str, str] | None = None,
    ) -> ResourceConstraint:
        constraint = ResourceConstraint(
            id=constraint_id,
            resource_id=resource_id,
            resource_type=resource_type,
            constraint_type=constraint_type,
            constraint_value=constraint_value,
            description=description,
            metadata=metadata or {},
        )
        self._constraints.append(constraint)
        self._log.info(
            "resource_optimization.constraint.detected",
            constraint_id=constraint_id,
        )
        return constraint

    async def list_constraints(
        self,
        resource_id: str | None = None,
        constraint_type: str | None = None,
    ) -> list[ResourceConstraint]:
        result = list(self._constraints)
        if resource_id:
            result = [c for c in result if c.resource_id == resource_id]
        if constraint_type:
            result = [c for c in result if c.constraint_type == constraint_type]
        return result

    async def resolve_constraint(self, constraint_id: str) -> ResourceConstraint:
        for i, c in enumerate(self._constraints):
            if c.id == constraint_id:
                merged = {**c.model_dump(), "is_active": False, "resolved_at": utc_now()}
                resolved = ResourceConstraint(**merged)
                self._constraints[i] = resolved
                self._log.info(
                    "resource_optimization.constraint.resolved",
                    constraint_id=constraint_id,
                )
                return resolved
        raise ResourceConstraintError(f"constraint not found: {constraint_id!r}")

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    async def record_history(
        self,
        history_id: str,
        resource_id: str,
        resource_type: ResourceType,
        action_type: str,
        strategy: OptimizationStrategy,
        status: ResourceActionStatus,
        previous_state: str = "",
        new_state: str = "",
        savings_per_hour: float = 0.0,
        performed_by: str = "",
        metadata: dict[str, str] | None = None,
    ) -> ResourceOptimizationHistory:
        entry = ResourceOptimizationHistory(
            id=history_id,
            resource_id=resource_id,
            resource_type=resource_type,
            action_type=action_type,
            strategy=strategy,
            status=status,
            previous_state=previous_state,
            new_state=new_state,
            savings_per_hour=savings_per_hour,
            performed_by=performed_by,
            metadata=metadata or {},
        )
        self._history.append(entry)
        self._log.info("resource_optimization.history.recorded", history_id=history_id)
        return entry

    async def list_history(
        self,
        resource_id: str | None = None,
        strategy: OptimizationStrategy | None = None,
    ) -> list[ResourceOptimizationHistory]:
        result = list(self._history)
        if resource_id:
            result = [h for h in result if h.resource_id == resource_id]
        if strategy:
            result = [h for h in result if h.strategy == strategy]
        return result


__all__ = ["ResourceOptimizationService"]
