"""Tests for the Resource Optimization package."""

from __future__ import annotations

from datetime import timedelta

import pytest

from eaip.resource_optimization.events import (
    ResourceActionCompleted,
    ResourceActionFailed,
    ResourceActionStarted,
    ResourceAllocationAdjusted,
    ResourceConstraintDetected,
    ResourceDemandForecastComputed,
    ResourceMetricsCollected,
    ResourceOptimizationConfigUpdated,
    ResourceOptimizationDashboardUpdated,
    ResourceOptimizationReportGenerated,
    ResourceOptimizationRuleCreated,
    ResourceOptimizationRuleDeleted,
    ResourceOptimizationRuleUpdated,
    ResourceRecommendationApplied,
    ResourceRecommendationDismissed,
    ResourceRecommendationGenerated,
    ResourceUtilizationAnalyzed,
)
from eaip.resource_optimization.exceptions import (
    ResourceActionError,
    ResourceAllocationError,
    ResourceConstraintError,
    ResourceDemandForecastError,
    ResourceMetricsError,
    ResourceOptimizationConfigError,
    ResourceOptimizationError,
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
    ResourceTag,
    ResourceType,
    ResourceUtilization,
)
from eaip.resource_optimization.service import ResourceOptimizationService
from eaip.shared.time import utc_now

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestResourceOptimizationConfig:
    def test_defaults(self) -> None:
        c = ResourceOptimizationConfig()
        assert c.auto_apply_recommendations is False
        assert c.max_recommendations_per_resource == 10

    def test_frozen(self) -> None:
        c = ResourceOptimizationConfig()
        with pytest.raises(ValueError):
            c.auto_apply_recommendations = True


class TestResourceMetrics:
    def test_defaults(self) -> None:
        m = ResourceMetrics(id="m1", resource_id="r1", resource_type=ResourceType.COMPUTE)
        assert m.cpu_utilization == 0.0
        assert m.memory_utilization == 0.0
        assert m.request_count == 0

    def test_frozen(self) -> None:
        m = ResourceMetrics(id="m1", resource_id="r1", resource_type=ResourceType.COMPUTE)
        with pytest.raises(ValueError):
            m.cpu_utilization = 50.0


class TestResourceUtilization:
    def test_defaults(self) -> None:
        now = utc_now()
        u = ResourceUtilization(
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            avg_cpu_utilization=45.0,
            peak_cpu_utilization=80.0,
            avg_memory_utilization=60.0,
            peak_memory_utilization=90.0,
            avg_disk_utilization=30.0,
            period_start=now - timedelta(hours=1),
            period_end=now,
        )
        assert u.is_idle is False
        assert u.idle_hours == 0


class TestResourceOptimizationRule:
    def test_defaults(self) -> None:
        r = ResourceOptimizationRule(
            id="rule1",
            name="test rule",
            strategy=OptimizationStrategy.RIGHT_SIZING,
        )
        assert r.enabled is True
        assert r.priority == RecommendationPriority.MEDIUM


class TestResourceRecommendation:
    def test_defaults(self) -> None:
        r = ResourceRecommendation(
            id="rec1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            strategy=OptimizationStrategy.SCALE_DOWN,
            priority=RecommendationPriority.HIGH,
            title="Scale down",
        )
        assert r.estimated_savings_per_month == 0.0
        assert r.risk_score == 0.0


class TestResourceAction:
    def test_defaults(self) -> None:
        a = ResourceAction(
            id="a1",
            recommendation_id="rec1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            action_type="resize",
        )
        assert a.status == ResourceActionStatus.PENDING


class TestResourceOptimizationReport:
    def test_defaults(self) -> None:
        now = utc_now()
        r = ResourceOptimizationReport(
            id="rp1",
            period_start=now - timedelta(days=1),
            period_end=now,
        )
        assert r.total_resources_analyzed == 0
        assert r.total_estimated_savings_per_month == 0.0


class TestResourceAllocation:
    def test_defaults(self) -> None:
        a = ResourceAllocation(
            id="al1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            allocated_capacity=100.0,
            used_capacity=60.0,
            requested_capacity=80.0,
        )
        assert a.allocation_efficiency == 0.0


class TestResourceDemandForecast:
    def test_defaults(self) -> None:
        f = ResourceDemandForecast(
            id="f1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
        )
        assert f.forecast_horizon_hours == 24


class TestResourceConstraint:
    def test_defaults(self) -> None:
        c = ResourceConstraint(
            id="c1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            constraint_type="budget",
        )
        assert c.is_active is True


class TestResourceTag:
    def test_create(self) -> None:
        t = ResourceTag(key="env", value="prod")
        assert t.key == "env"
        assert t.value == "prod"

    def test_frozen(self) -> None:
        t = ResourceTag(key="env", value="prod")
        with pytest.raises(ValueError):
            t.value = "staging"


class TestResourceOptimizationSchedule:
    def test_defaults(self) -> None:
        s = ResourceOptimizationSchedule(id="s1", name="daily")
        assert s.interval_hours == 24
        assert s.enabled is True


class TestResourceOptimizationDashboard:
    def test_defaults(self) -> None:
        d = ResourceOptimizationDashboard(id="d1", name="main")
        assert d.widgets == ()


class TestResourceOptimizationHistory:
    def test_defaults(self) -> None:
        h = ResourceOptimizationHistory(
            id="h1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            action_type="resize",
            strategy=OptimizationStrategy.RIGHT_SIZING,
            status=ResourceActionStatus.COMPLETED,
        )
        assert h.savings_per_hour == 0.0


# ---------------------------------------------------------------------------
# StrEnum values
# ---------------------------------------------------------------------------


class TestResourceTypeValues:
    def test_values(self) -> None:
        assert ResourceType.COMPUTE.value == "compute"
        assert ResourceType.MEMORY.value == "memory"
        assert ResourceType.STORAGE.value == "storage"
        assert ResourceType.GPU.value == "gpu"


class TestOptimizationStrategyValues:
    def test_values(self) -> None:
        assert OptimizationStrategy.RIGHT_SIZING.value == "right_sizing"
        assert OptimizationStrategy.SCALE_DOWN.value == "scale_down"
        assert OptimizationStrategy.SPOT_INSTANCE.value == "spot_instance"


class TestRecommendationPriorityValues:
    def test_values(self) -> None:
        assert RecommendationPriority.CRITICAL.value == "critical"
        assert RecommendationPriority.LOW.value == "low"


class TestResourceActionStatusValues:
    def test_values(self) -> None:
        assert ResourceActionStatus.PENDING.value == "pending"
        assert ResourceActionStatus.ROLLED_BACK.value == "rolled_back"


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class TestResourceOptimizationConfigUpdated:
    def test_create(self) -> None:
        e = ResourceOptimizationConfigUpdated(changes={"auto_apply": True})
        assert e.event_type == "eaip.resource_optimization.config.updated"
        assert e.changes["auto_apply"] is True


class TestResourceMetricsCollected:
    def test_create(self) -> None:
        e = ResourceMetricsCollected(
            metrics_id="m1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            cpu_utilization=45.0,
            memory_utilization=60.0,
        )
        assert e.event_type == "eaip.resource_optimization.metrics.collected"


class TestResourceUtilizationAnalyzed:
    def test_create(self) -> None:
        e = ResourceUtilizationAnalyzed(
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            avg_cpu_utilization=50.0,
            avg_memory_utilization=70.0,
            is_idle=False,
        )
        assert e.event_type == "eaip.resource_optimization.utilization.analyzed"


class TestResourceOptimizationRuleCreated:
    def test_create(self) -> None:
        e = ResourceOptimizationRuleCreated(
            rule_id="r1",
            name="test",
            strategy=OptimizationStrategy.RIGHT_SIZING,
        )
        assert e.event_type == "eaip.resource_optimization.rule.created"


class TestResourceOptimizationRuleUpdated:
    def test_create(self) -> None:
        e = ResourceOptimizationRuleUpdated(rule_id="r1", name="test", changes={"enabled": False})
        assert e.event_type == "eaip.resource_optimization.rule.updated"


class TestResourceOptimizationRuleDeleted:
    def test_create(self) -> None:
        e = ResourceOptimizationRuleDeleted(rule_id="r1", name="test")
        assert e.event_type == "eaip.resource_optimization.rule.deleted"


class TestResourceRecommendationGenerated:
    def test_create(self) -> None:
        e = ResourceRecommendationGenerated(
            recommendation_id="rec1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            strategy=OptimizationStrategy.SCALE_DOWN,
            priority=RecommendationPriority.HIGH,
            estimated_savings_per_month=100.0,
        )
        assert e.event_type == "eaip.resource_optimization.recommendation.generated"


class TestResourceRecommendationApplied:
    def test_create(self) -> None:
        e = ResourceRecommendationApplied(
            recommendation_id="rec1",
            resource_id="r1",
            action_id="a1",
        )
        assert e.event_type == "eaip.resource_optimization.recommendation.applied"


class TestResourceRecommendationDismissed:
    def test_create(self) -> None:
        e = ResourceRecommendationDismissed(
            recommendation_id="rec1", resource_id="r1", reason="not needed"
        )
        assert e.event_type == "eaip.resource_optimization.recommendation.dismissed"


class TestResourceActionStarted:
    def test_create(self) -> None:
        e = ResourceActionStarted(
            action_id="a1",
            recommendation_id="rec1",
            resource_id="r1",
            action_type="resize",
        )
        assert e.event_type == "eaip.resource_optimization.action.started"


class TestResourceActionCompleted:
    def test_create(self) -> None:
        e = ResourceActionCompleted(
            action_id="a1",
            recommendation_id="rec1",
            resource_id="r1",
            result={"new_size": "medium"},
        )
        assert e.event_type == "eaip.resource_optimization.action.completed"


class TestResourceActionFailed:
    def test_create(self) -> None:
        e = ResourceActionFailed(
            action_id="a1",
            recommendation_id="rec1",
            resource_id="r1",
            error_message="timeout",
        )
        assert e.event_type == "eaip.resource_optimization.action.failed"


class TestResourceOptimizationReportGenerated:
    def test_create(self) -> None:
        e = ResourceOptimizationReportGenerated(
            report_id="rp1",
            total_recommendations=5,
            total_estimated_savings_per_month=200.0,
        )
        assert e.event_type == "eaip.resource_optimization.report.generated"


class TestResourceDemandForecastComputed:
    def test_create(self) -> None:
        e = ResourceDemandForecastComputed(
            forecast_id="f1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            predicted_cpu_utilization=60.0,
            predicted_memory_utilization=70.0,
        )
        assert e.event_type == "eaip.resource_optimization.forecast.computed"


class TestResourceConstraintDetected:
    def test_create(self) -> None:
        e = ResourceConstraintDetected(
            constraint_id="c1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            constraint_type="budget",
        )
        assert e.event_type == "eaip.resource_optimization.constraint.detected"


class TestResourceOptimizationDashboardUpdated:
    def test_create(self) -> None:
        e = ResourceOptimizationDashboardUpdated(dashboard_id="d1", name="main")
        assert e.event_type == "eaip.resource_optimization.dashboard.updated"


class TestResourceAllocationAdjusted:
    def test_create(self) -> None:
        e = ResourceAllocationAdjusted(
            allocation_id="al1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            previous_capacity=100.0,
            new_capacity=80.0,
        )
        assert e.event_type == "eaip.resource_optimization.allocation.adjusted"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TestExceptionsHierarchy:
    def test_base_exception(self) -> None:
        e = ResourceOptimizationError("test error")
        assert isinstance(e, Exception)

    def test_config_error(self) -> None:
        e = ResourceOptimizationConfigError("invalid config")
        assert isinstance(e, ResourceOptimizationError)

    def test_metrics_error(self) -> None:
        e = ResourceMetricsError("metrics error")
        assert isinstance(e, ResourceOptimizationError)

    def test_recommendation_error(self) -> None:
        e = ResourceRecommendationError("rec error")
        assert isinstance(e, ResourceOptimizationError)

    def test_action_error(self) -> None:
        e = ResourceActionError("action error")
        assert isinstance(e, ResourceOptimizationError)

    def test_allocation_error(self) -> None:
        e = ResourceAllocationError("allocation error")
        assert isinstance(e, ResourceOptimizationError)

    def test_forecast_error(self) -> None:
        e = ResourceDemandForecastError("forecast error")
        assert isinstance(e, ResourceOptimizationError)

    def test_constraint_error(self) -> None:
        e = ResourceConstraintError("constraint error")
        assert isinstance(e, ResourceOptimizationError)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TestResourceOptimizationService:
    async def test_config_defaults(self) -> None:
        svc = ResourceOptimizationService()
        assert svc.config.auto_apply_recommendations is False

    async def test_update_config(self) -> None:
        svc = ResourceOptimizationService()
        updated = await svc.update_config(auto_apply_recommendations=True)
        assert updated.auto_apply_recommendations is True

    async def test_record_and_get_metrics(self) -> None:
        svc = ResourceOptimizationService()
        m = await svc.record_metrics(
            metrics_id="m1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            cpu_utilization=50.0,
            memory_utilization=60.0,
        )
        assert m.id == "m1"
        got = await svc.get_metrics("m1")
        assert got.cpu_utilization == 50.0

    async def test_get_metrics_not_found(self) -> None:
        svc = ResourceOptimizationService()
        with pytest.raises(ResourceMetricsError):
            await svc.get_metrics("nonexistent")

    async def test_list_metrics_filter(self) -> None:
        svc = ResourceOptimizationService()
        await svc.record_metrics(
            metrics_id="m1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
        )
        await svc.record_metrics(
            metrics_id="m2",
            resource_id="r2",
            resource_type=ResourceType.MEMORY,
        )
        result = await svc.list_metrics(resource_type=ResourceType.COMPUTE)
        assert len(result) == 1
        assert result[0].id == "m1"

    async def test_analyze_utilization(self) -> None:
        svc = ResourceOptimizationService()
        m1 = await svc.record_metrics(
            metrics_id="m1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            cpu_utilization=30.0,
            memory_utilization=40.0,
        )
        m2 = await svc.record_metrics(
            metrics_id="m2",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            cpu_utilization=50.0,
            memory_utilization=60.0,
        )
        u = await svc.analyze_utilization("r1", ResourceType.COMPUTE, [m1, m2])
        assert u.avg_cpu_utilization == 40.0
        assert u.peak_cpu_utilization == 50.0

    async def test_analyze_utilization_no_data(self) -> None:
        svc = ResourceOptimizationService()
        with pytest.raises(ResourceMetricsError):
            await svc.analyze_utilization("r1", ResourceType.COMPUTE, [])

    async def test_create_and_get_rule(self) -> None:
        svc = ResourceOptimizationService()
        r = await svc.create_rule(
            rule_id="rule1",
            name="high cpu",
            strategy=OptimizationStrategy.RIGHT_SIZING,
        )
        assert r.id == "rule1"
        got = await svc.get_rule("rule1")
        assert got.name == "high cpu"

    async def test_create_rule_duplicate(self) -> None:
        svc = ResourceOptimizationService()
        await svc.create_rule(
            rule_id="rule1",
            name="r1",
            strategy=OptimizationStrategy.RIGHT_SIZING,
        )
        with pytest.raises(ResourceOptimizationConfigError):
            await svc.create_rule(
                rule_id="rule1",
                name="r2",
                strategy=OptimizationStrategy.SCALE_DOWN,
            )

    async def test_delete_rule(self) -> None:
        svc = ResourceOptimizationService()
        await svc.create_rule(
            rule_id="rule1",
            name="r1",
            strategy=OptimizationStrategy.RIGHT_SIZING,
        )
        await svc.delete_rule("rule1")
        with pytest.raises(ResourceOptimizationConfigError):
            await svc.get_rule("rule1")

    async def test_list_rules_filter(self) -> None:
        svc = ResourceOptimizationService()
        await svc.create_rule(
            rule_id="r1",
            name="r1",
            strategy=OptimizationStrategy.RIGHT_SIZING,
            enabled=True,
        )
        await svc.create_rule(
            rule_id="r2",
            name="r2",
            strategy=OptimizationStrategy.SCALE_DOWN,
            enabled=False,
        )
        result = await svc.list_rules(enabled=True)
        assert len(result) == 1

    async def test_generate_recommendation(self) -> None:
        svc = ResourceOptimizationService()
        rec = await svc.generate_recommendation(
            recommendation_id="rec1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            strategy=OptimizationStrategy.SCALE_DOWN,
            priority=RecommendationPriority.HIGH,
            title="Scale down r1",
            estimated_savings_per_month=50.0,
        )
        assert rec.id == "rec1"
        assert rec.estimated_savings_per_month == 50.0

    async def test_apply_recommendation(self) -> None:
        svc = ResourceOptimizationService()
        await svc.generate_recommendation(
            recommendation_id="rec1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            strategy=OptimizationStrategy.SCALE_DOWN,
            priority=RecommendationPriority.HIGH,
            title="Scale down",
        )
        applied = await svc.apply_recommendation("rec1")
        assert applied.applied_at is not None

    async def test_apply_recommendation_already_applied(self) -> None:
        svc = ResourceOptimizationService()
        await svc.generate_recommendation(
            recommendation_id="rec1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            strategy=OptimizationStrategy.SCALE_DOWN,
            priority=RecommendationPriority.HIGH,
            title="Scale down",
        )
        await svc.apply_recommendation("rec1")
        with pytest.raises(ResourceRecommendationError):
            await svc.apply_recommendation("rec1")

    async def test_dismiss_recommendation(self) -> None:
        svc = ResourceOptimizationService()
        await svc.generate_recommendation(
            recommendation_id="rec1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            strategy=OptimizationStrategy.SCALE_DOWN,
            priority=RecommendationPriority.HIGH,
            title="Scale down",
        )
        dismissed = await svc.dismiss_recommendation("rec1")
        assert dismissed.dismissed_at is not None

    async def test_start_and_complete_action(self) -> None:
        svc = ResourceOptimizationService()
        a = await svc.start_action(
            action_id="a1",
            recommendation_id="rec1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            action_type="resize",
        )
        assert a.status == ResourceActionStatus.RUNNING
        completed = await svc.complete_action("a1", {"result": "ok"})
        assert completed.status == ResourceActionStatus.COMPLETED

    async def test_fail_action(self) -> None:
        svc = ResourceOptimizationService()
        await svc.start_action(
            action_id="a1",
            recommendation_id="rec1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            action_type="resize",
        )
        failed = await svc.fail_action("a1", "error occurred")
        assert failed.status == ResourceActionStatus.FAILED
        assert failed.error_message == "error occurred"

    async def test_get_action_not_found(self) -> None:
        svc = ResourceOptimizationService()
        with pytest.raises(ResourceActionError):
            await svc.get_action("nonexistent")

    async def test_generate_report(self) -> None:
        svc = ResourceOptimizationService()
        now = utc_now()
        await svc.generate_recommendation(
            recommendation_id="rec1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            strategy=OptimizationStrategy.SCALE_DOWN,
            priority=RecommendationPriority.CRITICAL,
            title="Critical",
            estimated_savings_per_month=100.0,
        )
        report = await svc.generate_report(
            report_id="rp1",
            period_start=now - timedelta(days=1),
            period_end=now,
        )
        assert report.total_recommendations == 1
        assert report.critical_recommendations == 1

    async def test_record_allocation(self) -> None:
        svc = ResourceOptimizationService()
        a = await svc.record_allocation(
            allocation_id="al1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            allocated_capacity=100.0,
            used_capacity=60.0,
        )
        assert a.allocation_efficiency == 60.0
        assert a.over_allocated is True

    async def test_adjust_allocation(self) -> None:
        svc = ResourceOptimizationService()
        await svc.record_allocation(
            allocation_id="al1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            allocated_capacity=100.0,
            used_capacity=60.0,
        )
        adjusted = await svc.adjust_allocation("al1", 80.0)
        assert adjusted.allocated_capacity == 80.0

    async def test_adjust_allocation_negative(self) -> None:
        svc = ResourceOptimizationService()
        await svc.record_allocation(
            allocation_id="al1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
        )
        with pytest.raises(ResourceAllocationError):
            await svc.adjust_allocation("al1", -10.0)

    async def test_compute_forecast(self) -> None:
        svc = ResourceOptimizationService()
        m1 = await svc.record_metrics(
            metrics_id="m1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            cpu_utilization=30.0,
            memory_utilization=40.0,
        )
        m2 = await svc.record_metrics(
            metrics_id="m2",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            cpu_utilization=50.0,
            memory_utilization=60.0,
        )
        f = await svc.compute_forecast(
            forecast_id="f1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            metrics_list=[m1, m2],
        )
        assert f.predicted_demand_trend in ("increasing", "decreasing", "stable")

    async def test_compute_forecast_no_data(self) -> None:
        svc = ResourceOptimizationService()
        with pytest.raises(ResourceDemandForecastError):
            await svc.compute_forecast(
                forecast_id="f1",
                resource_id="r1",
                resource_type=ResourceType.COMPUTE,
                metrics_list=[],
            )

    async def test_create_and_get_dashboard(self) -> None:
        svc = ResourceOptimizationService()
        d = await svc.create_dashboard(dashboard_id="d1", name="main", description="test")
        assert d.name == "main"
        got = await svc.get_dashboard("d1")
        assert got.description == "test"

    async def test_update_dashboard(self) -> None:
        svc = ResourceOptimizationService()
        await svc.create_dashboard(dashboard_id="d1", name="main")
        updated = await svc.update_dashboard(dashboard_id="d1", name="updated")
        assert updated.name == "updated"

    async def test_delete_dashboard(self) -> None:
        svc = ResourceOptimizationService()
        await svc.create_dashboard(dashboard_id="d1", name="main")
        await svc.delete_dashboard("d1")
        with pytest.raises(ResourceOptimizationConfigError):
            await svc.get_dashboard("d1")

    async def test_detect_constraint(self) -> None:
        svc = ResourceOptimizationService()
        c = await svc.detect_constraint(
            constraint_id="c1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            constraint_type="budget",
        )
        assert c.is_active is True

    async def test_resolve_constraint(self) -> None:
        svc = ResourceOptimizationService()
        await svc.detect_constraint(
            constraint_id="c1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            constraint_type="budget",
        )
        resolved = await svc.resolve_constraint("c1")
        assert resolved.is_active is False
        assert resolved.resolved_at is not None

    async def test_resolve_constraint_not_found(self) -> None:
        svc = ResourceOptimizationService()
        with pytest.raises(ResourceConstraintError):
            await svc.resolve_constraint("nonexistent")

    async def test_list_constraints_filter(self) -> None:
        svc = ResourceOptimizationService()
        await svc.detect_constraint(
            constraint_id="c1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            constraint_type="budget",
        )
        await svc.detect_constraint(
            constraint_id="c2",
            resource_id="r2",
            resource_type=ResourceType.MEMORY,
            constraint_type="quota",
        )
        result = await svc.list_constraints(constraint_type="budget")
        assert len(result) == 1

    async def test_record_history(self) -> None:
        svc = ResourceOptimizationService()
        h = await svc.record_history(
            history_id="h1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            action_type="resize",
            strategy=OptimizationStrategy.RIGHT_SIZING,
            status=ResourceActionStatus.COMPLETED,
        )
        assert h.id == "h1"

    async def test_list_history_filter(self) -> None:
        svc = ResourceOptimizationService()
        await svc.record_history(
            history_id="h1",
            resource_id="r1",
            resource_type=ResourceType.COMPUTE,
            action_type="resize",
            strategy=OptimizationStrategy.RIGHT_SIZING,
            status=ResourceActionStatus.COMPLETED,
        )
        await svc.record_history(
            history_id="h2",
            resource_id="r2",
            resource_type=ResourceType.MEMORY,
            action_type="scale",
            strategy=OptimizationStrategy.SCALE_DOWN,
            status=ResourceActionStatus.PENDING,
        )
        result = await svc.list_history(strategy=OptimizationStrategy.RIGHT_SIZING)
        assert len(result) == 1

    async def test_create_schedule(self) -> None:
        svc = ResourceOptimizationService()
        s = await svc.create_schedule(schedule_id="s1", name="weekly", interval_hours=168)
        assert s.interval_hours == 168

    async def test_create_schedule_duplicate(self) -> None:
        svc = ResourceOptimizationService()
        await svc.create_schedule(schedule_id="s1", name="s1")
        with pytest.raises(ResourceOptimizationConfigError):
            await svc.create_schedule(schedule_id="s1", name="s2")

    async def test_delete_schedule(self) -> None:
        svc = ResourceOptimizationService()
        await svc.create_schedule(schedule_id="s1", name="s1")
        await svc.delete_schedule("s1")
        with pytest.raises(ResourceOptimizationConfigError):
            await svc.get_schedule("s1")
