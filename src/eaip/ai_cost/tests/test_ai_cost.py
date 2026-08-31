"""Tests for AI Cost models, events, exceptions, service, integration, and health."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from eaip.ai_cost.events import (
    AiCostAllocationUpdated,
    AiCostAnomalyDetected,
    AiCostBudgetAlertTriggered,
    AiCostBudgetCreated,
    AiCostBudgetExceeded,
    AiCostBudgetUpdated,
    AiCostDashboardUpdated,
    AiCostOptimizationApplied,
    AiCostOptimizationRuleCreated,
    AiCostProjectionComputed,
    AiCostRecorded,
    AiCostReportGenerated,
    ModelCostRateUpdated,
)
from eaip.ai_cost.exceptions import (
    AiCostAllocationError,
    AiCostAnomalyError,
    AiCostBudgetError,
    AiCostError,
    AiCostOptimizationError,
    AiCostRecordError,
    AiCostReportError,
)
from eaip.ai_cost.health import AiCostHealthCheck
from eaip.ai_cost.integration import AiCostRuntimeModule
from eaip.ai_cost.models import (
    AiCostAlert,
    AiCostAllocation,
    AiCostBudget,
    AiCostConfig,
    AiCostDashboard,
    AiCostOptimizationRule,
    AiCostProjection,
    AiCostRecord,
    AiCostReport,
    AiCostReportPeriod,
    BudgetPeriod,
    CostType,
    ModelCostRate,
    OptimizationStrategy,
    TokenCostBreakdown,
)
from eaip.ai_cost.service import AiCostService
from eaip.shared.time import utc_now

# ── Models ───────────────────────────────────────────────────────────────────


class TestCostType:
    def test_values(self) -> None:
        assert CostType.PROMPT.value == "prompt"
        assert CostType.COMPLETION.value == "completion"
        assert CostType.EMBEDDING.value == "embedding"
        assert CostType.FINE_TUNE.value == "fine_tune"
        assert CostType.CACHE_HIT.value == "cache_hit"
        assert CostType.INFERENCE.value == "inference"
        assert CostType.TRAINING.value == "training"
        assert CostType.TOTAL.value == "total"


class TestBudgetPeriod:
    def test_values(self) -> None:
        assert BudgetPeriod.DAILY.value == "daily"
        assert BudgetPeriod.MONTHLY.value == "monthly"


class TestOptimizationStrategy:
    def test_values(self) -> None:
        assert OptimizationStrategy.MODEL_SWITCH.value == "model_switch"
        assert OptimizationStrategy.CACHE_OPTIMIZE.value == "cache_optimize"


class TestAiCostConfig:
    def test_defaults(self) -> None:
        c = AiCostConfig()
        assert c.default_currency == "USD"
        assert c.enable_budget_alerts is True
        assert c.data_retention_days == 365
        assert c.projection_horizon_days == 90

    def test_frozen(self) -> None:
        c = AiCostConfig()
        with pytest.raises(ValidationError):
            c.default_currency = "EUR"


class TestModelCostRate:
    def test_minimal(self) -> None:
        r = ModelCostRate(
            model_id="gpt-4",
            provider="openai",
            input_cost_per_1k_tokens=0.03,
            output_cost_per_1k_tokens=0.06,
        )
        assert r.currency == "USD"
        assert r.effective_to is None

    def test_frozen(self) -> None:
        r = ModelCostRate(
            model_id="gpt-4",
            provider="openai",
            input_cost_per_1k_tokens=0.03,
            output_cost_per_1k_tokens=0.06,
        )
        with pytest.raises(ValidationError):
            r.provider = "azure"


class TestTokenCostBreakdown:
    def test_defaults(self) -> None:
        b = TokenCostBreakdown()
        assert b.input_tokens == 0
        assert b.output_cost == 0.0


class TestAiCostRecord:
    def test_minimal(self) -> None:
        r = AiCostRecord(id="cr1", model_id="gpt-4", cost_type=CostType.INFERENCE, amount=0.05)
        assert r.currency == "USD"
        assert r.tags == ()
        assert r.token_breakdown is None

    def test_frozen(self) -> None:
        r = AiCostRecord(id="cr1", model_id="gpt-4", cost_type=CostType.INFERENCE, amount=0.05)
        with pytest.raises(ValidationError):
            r.amount = 0.10

    def test_with_tokens(self) -> None:
        tb = TokenCostBreakdown(
            input_tokens=100,
            output_tokens=50,
            input_cost=0.003,
            output_cost=0.003,
        )
        r = AiCostRecord(
            id="cr2",
            model_id="gpt-4",
            cost_type=CostType.INFERENCE,
            amount=0.006,
            input_tokens=100,
            output_tokens=50,
            token_breakdown=tb,
        )
        assert r.input_tokens == 100
        assert r.token_breakdown is not None
        assert r.token_breakdown.input_tokens == 100


class TestAiCostBudget:
    def test_minimal(self) -> None:
        now = utc_now()
        b = AiCostBudget(
            id="b1",
            name="Monthly GPT-4 Budget",
            amount=1000.0,
            period=BudgetPeriod.MONTHLY,
            start_date=now,
            end_date=now + timedelta(days=30),
        )
        assert b.alert_thresholds == (0.8, 0.9, 1.0)
        assert b.enabled is True

    def test_frozen(self) -> None:
        now = utc_now()
        b = AiCostBudget(
            id="b1",
            name="Test",
            amount=500.0,
            period=BudgetPeriod.MONTHLY,
            start_date=now,
            end_date=now + timedelta(days=30),
        )
        with pytest.raises(ValidationError):
            b.amount = 600.0


class TestAiCostAlert:
    def test_minimal(self) -> None:
        a = AiCostAlert(
            id="a1",
            budget_id="b1",
            threshold=0.9,
            actual_spend=900.0,
            budgeted_amount=1000.0,
            percentage=0.9,
        )
        assert a.acknowledged_at is None

    def test_frozen(self) -> None:
        a = AiCostAlert(
            id="a1",
            budget_id="b1",
            threshold=0.9,
            actual_spend=900.0,
            budgeted_amount=1000.0,
            percentage=0.9,
        )
        with pytest.raises(ValidationError):
            a.threshold = 1.0


class TestAiCostOptimizationRule:
    def test_minimal(self) -> None:
        r = AiCostOptimizationRule(
            id="r1",
            name="Switch to GPT-4o-mini",
            strategy=OptimizationStrategy.MODEL_SWITCH,
        )
        assert r.enabled is True

    def test_frozen(self) -> None:
        r = AiCostOptimizationRule(
            id="r1",
            name="Test",
            strategy=OptimizationStrategy.CACHE_OPTIMIZE,
        )
        with pytest.raises(ValidationError):
            r.strategy = OptimizationStrategy.MODEL_SWITCH


class TestAiCostReport:
    def test_minimal(self) -> None:
        now = utc_now()
        r = AiCostReport(
            id="rpt1",
            period=AiCostReportPeriod.MONTHLY,
            period_start=now,
            period_end=now + timedelta(days=30),
            total_cost=500.0,
        )
        assert r.cost_by_model == {}

    def test_frozen(self) -> None:
        now = utc_now()
        r = AiCostReport(
            id="rpt1",
            period=AiCostReportPeriod.MONTHLY,
            period_start=now,
            period_end=now + timedelta(days=30),
            total_cost=500.0,
        )
        with pytest.raises(ValidationError):
            r.total_cost = 600.0


class TestAiCostAllocation:
    def test_minimal(self) -> None:
        now = utc_now()
        a = AiCostAllocation(
            id="al1",
            tenant_id="tenant1",
            amount=250.0,
            period_start=now,
            period_end=now + timedelta(days=30),
        )
        assert a.currency == "USD"

    def test_frozen(self) -> None:
        now = utc_now()
        a = AiCostAllocation(
            id="al1",
            tenant_id="tenant1",
            amount=250.0,
            period_start=now,
            period_end=now + timedelta(days=30),
        )
        with pytest.raises(ValidationError):
            a.amount = 300.0


class TestAiCostProjection:
    def test_minimal(self) -> None:
        now = utc_now()
        p = AiCostProjection(
            id="proj1",
            projected_amount=1500.0,
            confidence_interval_low=1200.0,
            confidence_interval_high=1800.0,
            projection_start=now,
            projection_end=now + timedelta(days=90),
        )
        assert p.historical_data_points == 0

    def test_frozen(self) -> None:
        now = utc_now()
        p = AiCostProjection(
            id="proj1",
            projected_amount=1500.0,
            confidence_interval_low=1200.0,
            confidence_interval_high=1800.0,
            projection_start=now,
            projection_end=now + timedelta(days=90),
        )
        with pytest.raises(ValidationError):
            p.projected_amount = 2000.0


class TestAiCostDashboard:
    def test_defaults(self) -> None:
        d = AiCostDashboard(id="main", name="AI Cost Dashboard")
        assert d.current_spend == 0.0
        assert d.active_alerts == 0

    def test_frozen(self) -> None:
        d = AiCostDashboard(id="main", name="AI Cost Dashboard")
        with pytest.raises(ValidationError):
            d.name = "other"


# ── Events ───────────────────────────────────────────────────────────────────


class TestAiCostRecorded:
    def test_minimal(self) -> None:
        e = AiCostRecorded(
            record_id="cr1",
            model_id="gpt-4",
            cost_type="inference",
            amount=0.05,
            currency="USD",
        )
        assert e.event_type == "eaip.ai_cost.recorded"
        assert e.input_tokens == 0

    def test_frozen(self) -> None:
        e = AiCostRecorded(
            record_id="cr1",
            model_id="gpt-4",
            cost_type="inference",
            amount=0.05,
            currency="USD",
        )
        with pytest.raises(ValidationError):
            e.amount = 0.10


class TestAiCostBudgetCreated:
    def test_minimal(self) -> None:
        e = AiCostBudgetCreated(
            budget_id="b1",
            name="test",
            amount=1000.0,
            currency="USD",
            period="monthly",
        )
        assert e.event_type == "eaip.ai_cost.budget.created"


class TestAiCostBudgetUpdated:
    def test_minimal(self) -> None:
        e = AiCostBudgetUpdated(budget_id="b1", updates={"amount": 1200.0})
        assert e.event_type == "eaip.ai_cost.budget.updated"
        assert e.updates["amount"] == 1200.0


class TestAiCostBudgetExceeded:
    def test_minimal(self) -> None:
        e = AiCostBudgetExceeded(
            budget_id="b1",
            actual_spend=1100.0,
            budgeted_amount=1000.0,
            overshoot=100.0,
        )
        assert e.event_type == "eaip.ai_cost.budget.exceeded"


class TestAiCostBudgetAlertTriggered:
    def test_minimal(self) -> None:
        e = AiCostBudgetAlertTriggered(
            alert_id="a1",
            budget_id="b1",
            threshold=0.9,
            actual_spend=900.0,
            percentage=0.9,
        )
        assert e.event_type == "eaip.ai_cost.budget.alert_triggered"


class TestAiCostOptimizationRuleCreated:
    def test_minimal(self) -> None:
        e = AiCostOptimizationRuleCreated(rule_id="r1", name="switch", strategy="model_switch")
        assert e.event_type == "eaip.ai_cost.optimization_rule.created"


class TestAiCostOptimizationApplied:
    def test_minimal(self) -> None:
        e = AiCostOptimizationApplied(
            rule_id="r1",
            model_id="gpt-4",
            estimated_savings=150.0,
            currency="USD",
        )
        assert e.event_type == "eaip.ai_cost.optimization_applied"


class TestAiCostReportGenerated:
    def test_minimal(self) -> None:
        now = utc_now()
        e = AiCostReportGenerated(
            report_id="rpt1",
            period="monthly",
            period_start=now,
            period_end=now,
            total_cost=500.0,
        )
        assert e.event_type == "eaip.ai_cost.report.generated"


class TestAiCostProjectionComputed:
    def test_minimal(self) -> None:
        now = utc_now()
        e = AiCostProjectionComputed(
            projection_id="proj1",
            projected_amount=1500.0,
            projection_start=now,
            projection_end=now,
        )
        assert e.event_type == "eaip.ai_cost.projection.computed"


class TestAiCostAllocationUpdated:
    def test_minimal(self) -> None:
        now = utc_now()
        e = AiCostAllocationUpdated(
            allocation_id="al1",
            tenant_id="t1",
            amount=250.0,
            currency="USD",
            period_start=now,
            period_end=now,
        )
        assert e.event_type == "eaip.ai_cost.allocation.updated"


class TestAiCostDashboardUpdated:
    def test_minimal(self) -> None:
        e = AiCostDashboardUpdated(
            dashboard_id="main",
            current_spend=500.0,
            projected_cost=1500.0,
            active_alerts=2,
        )
        assert e.event_type == "eaip.ai_cost.dashboard.updated"


class TestModelCostRateUpdated:
    def test_minimal(self) -> None:
        e = ModelCostRateUpdated(
            model_id="gpt-4",
            provider="openai",
            input_cost_per_1k_tokens=0.03,
            output_cost_per_1k_tokens=0.06,
            currency="USD",
        )
        assert e.event_type == "eaip.ai_cost.model_cost_rate.updated"


class TestAiCostAnomalyDetected:
    def test_minimal(self) -> None:
        e = AiCostAnomalyDetected(
            model_id="gpt-4",
            actual_cost=500.0,
            expected_cost=100.0,
            deviation=400.0,
            severity="high",
        )
        assert e.event_type == "eaip.ai_cost.anomaly.detected"


# ── Exceptions ───────────────────────────────────────────────────────────────


class TestAiCostError:
    def test_is_eaip_error(self) -> None:
        err = AiCostError("something went wrong")
        assert str(err) == "something went wrong"


class TestAiCostBudgetError:
    def test_default_code(self) -> None:
        err = AiCostBudgetError("budget failed")
        assert str(err.code) == "EAIP-0012"


class TestAiCostRecordError:
    def test_with_context(self) -> None:
        err = AiCostRecordError("record not found")
        assert "record" in str(err)


class TestAiCostOptimizationError:
    def test_basic(self) -> None:
        err = AiCostOptimizationError("optimization failed")
        assert "optimization" in str(err)


class TestAiCostReportError:
    def test_basic(self) -> None:
        err = AiCostReportError("report failed")
        assert "report" in str(err)


class TestAiCostAllocationError:
    def test_basic(self) -> None:
        err = AiCostAllocationError("allocation failed")
        assert "allocation" in str(err)


class TestAiCostAnomalyError:
    def test_basic(self) -> None:
        err = AiCostAnomalyError("anomaly detection failed")
        assert "anomaly" in str(err)


# ── Service ──────────────────────────────────────────────────────────────────


class TestAiCostService:
    async def test_record_cost_minimal(self) -> None:
        svc = AiCostService()
        record = await svc.record_cost(
            model_id="gpt-4",
            cost_type=CostType.INFERENCE,
            amount=0.05,
        )
        assert record.model_id == "gpt-4"
        assert record.amount == 0.05
        assert record.currency == "USD"

    async def test_record_cost_with_tokens(self) -> None:
        svc = AiCostService()
        rate = ModelCostRate(
            model_id="gpt-4",
            provider="openai",
            input_cost_per_1k_tokens=0.03,
            output_cost_per_1k_tokens=0.06,
        )
        await svc.upsert_cost_rate(rate)
        record = await svc.record_cost(
            model_id="gpt-4",
            cost_type=CostType.INFERENCE,
            amount=0.006,
            input_tokens=100,
            output_tokens=50,
        )
        assert record.input_tokens == 100
        assert record.token_breakdown is not None
        assert record.token_breakdown.input_tokens == 100

    async def test_get_record(self) -> None:
        svc = AiCostService()
        created = await svc.record_cost(model_id="gpt-4", cost_type=CostType.INFERENCE, amount=0.05)
        fetched = await svc.get_record(created.id)
        assert fetched.id == created.id

    async def test_get_record_not_found(self) -> None:
        svc = AiCostService()
        with pytest.raises(AiCostRecordError):
            await svc.get_record("nonexistent")

    async def test_query_costs(self) -> None:
        svc = AiCostService()
        await svc.record_cost(model_id="gpt-4", cost_type=CostType.INFERENCE, amount=0.05)
        await svc.record_cost(model_id="gpt-3.5", cost_type=CostType.INFERENCE, amount=0.02)
        results = await svc.query_costs(model_id="gpt-4")
        assert len(results) == 1
        assert results[0].model_id == "gpt-4"

    async def test_upsert_cost_rate(self) -> None:
        svc = AiCostService()
        rate = ModelCostRate(
            model_id="gpt-4",
            provider="openai",
            input_cost_per_1k_tokens=0.03,
            output_cost_per_1k_tokens=0.06,
        )
        result = await svc.upsert_cost_rate(rate)
        assert result.model_id == "gpt-4"
        fetched = await svc.get_cost_rate("gpt-4")
        assert fetched is not None
        assert fetched.input_cost_per_1k_tokens == 0.03

    async def test_create_budget(self) -> None:
        svc = AiCostService()
        now = utc_now()
        budget = AiCostBudget(
            id="b1",
            name="Monthly GPT-4",
            amount=1000.0,
            period=BudgetPeriod.MONTHLY,
            start_date=now,
            end_date=now + timedelta(days=30),
        )
        result = await svc.create_budget(budget)
        assert result.id == "b1"

    async def test_update_budget(self) -> None:
        svc = AiCostService()
        now = utc_now()
        budget = AiCostBudget(
            id="b1",
            name="Monthly GPT-4",
            amount=1000.0,
            period=BudgetPeriod.MONTHLY,
            start_date=now,
            end_date=now + timedelta(days=30),
        )
        await svc.create_budget(budget)
        updated = await svc.update_budget(budget_id="b1", amount=1200.0)
        assert updated.amount == 1200.0

    async def test_update_budget_not_found(self) -> None:
        svc = AiCostService()
        with pytest.raises(AiCostBudgetError):
            await svc.update_budget("nonexistent", amount=100.0)

    async def test_get_budget(self) -> None:
        svc = AiCostService()
        now = utc_now()
        budget = AiCostBudget(
            id="b1",
            name="Test",
            amount=500.0,
            period=BudgetPeriod.MONTHLY,
            start_date=now,
            end_date=now + timedelta(days=30),
        )
        await svc.create_budget(budget)
        fetched = await svc.get_budget("b1")
        assert fetched.name == "Test"

    async def test_get_budget_not_found(self) -> None:
        svc = AiCostService()
        with pytest.raises(AiCostBudgetError):
            await svc.get_budget("nonexistent")

    async def test_list_budgets(self) -> None:
        svc = AiCostService()
        now = utc_now()
        b1 = AiCostBudget(
            id="b1",
            name="B1",
            amount=100.0,
            period=BudgetPeriod.MONTHLY,
            start_date=now,
            end_date=now + timedelta(days=30),
        )
        b2 = AiCostBudget(
            id="b2",
            name="B2",
            amount=200.0,
            period=BudgetPeriod.MONTHLY,
            start_date=now,
            end_date=now + timedelta(days=30),
        )
        await svc.create_budget(b1)
        await svc.create_budget(b2)
        budgets = await svc.list_budgets()
        assert len(budgets) == 2

    async def test_budget_alert_triggered(self) -> None:
        svc = AiCostService()
        now = utc_now()
        budget = AiCostBudget(
            id="b1",
            name="Test",
            amount=10.0,
            period=BudgetPeriod.MONTHLY,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
            alert_thresholds=(0.5,),
        )
        await svc.create_budget(budget)

        events: list[Any] = []
        svc.set_event_callback(events.append)

        await svc.record_cost(model_id="gpt-4", cost_type=CostType.INFERENCE, amount=6.0)
        alert_events = [e for e in events if isinstance(e, AiCostBudgetAlertTriggered)]
        assert len(alert_events) >= 1

    async def test_budget_exceeded(self) -> None:
        svc = AiCostService()
        now = utc_now()
        budget = AiCostBudget(
            id="b1",
            name="Test",
            amount=5.0,
            period=BudgetPeriod.MONTHLY,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
        )
        await svc.create_budget(budget)

        events: list[Any] = []
        svc.set_event_callback(events.append)

        await svc.record_cost(model_id="gpt-4", cost_type=CostType.INFERENCE, amount=7.0)
        exceeded_events = [e for e in events if isinstance(e, AiCostBudgetExceeded)]
        assert len(exceeded_events) >= 1

    async def test_create_optimization_rule(self) -> None:
        svc = AiCostService()
        rule = AiCostOptimizationRule(
            id="r1",
            name="Switch Model",
            strategy=OptimizationStrategy.MODEL_SWITCH,
            model_id="gpt-4",
        )
        result = await svc.create_optimization_rule(rule)
        assert result.id == "r1"

    async def test_list_optimization_rules(self) -> None:
        svc = AiCostService()
        r1 = AiCostOptimizationRule(id="r1", name="R1", strategy=OptimizationStrategy.MODEL_SWITCH)
        r2 = AiCostOptimizationRule(
            id="r2",
            name="R2",
            strategy=OptimizationStrategy.CACHE_OPTIMIZE,
        )
        await svc.create_optimization_rule(r1)
        await svc.create_optimization_rule(r2)
        rules = await svc.list_optimization_rules()
        assert len(rules) == 2

    async def test_apply_optimization(self) -> None:
        svc = AiCostService()
        rule = AiCostOptimizationRule(
            id="r1",
            name="Switch Model",
            strategy=OptimizationStrategy.MODEL_SWITCH,
        )
        await svc.create_optimization_rule(rule)
        await svc.record_cost(model_id="gpt-4", cost_type=CostType.INFERENCE, amount=100.0)
        result = await svc.apply_optimization(rule_id="r1", model_id="gpt-4")
        assert result["estimated_savings"] > 0

    async def test_apply_optimization_rule_not_found(self) -> None:
        svc = AiCostService()
        with pytest.raises(AiCostOptimizationError):
            await svc.apply_optimization(rule_id="nonexistent", model_id="gpt-4")

    async def test_generate_report(self) -> None:
        svc = AiCostService()
        now = utc_now()
        await svc.record_cost(model_id="gpt-4", cost_type=CostType.INFERENCE, amount=50.0)
        await svc.record_cost(model_id="gpt-3.5", cost_type=CostType.INFERENCE, amount=30.0)
        report = await svc.generate_report(
            period=AiCostReportPeriod.DAILY,
            period_start=now - timedelta(days=1),
            period_end=now + timedelta(days=1),
        )
        assert report.total_cost == 80.0
        assert "gpt-4" in report.cost_by_model

    async def test_get_report(self) -> None:
        svc = AiCostService()
        now = utc_now()
        report = await svc.generate_report(
            period=AiCostReportPeriod.DAILY,
            period_start=now - timedelta(days=1),
            period_end=now + timedelta(days=1),
        )
        fetched = await svc.get_report(report.id)
        assert fetched.id == report.id

    async def test_get_report_not_found(self) -> None:
        svc = AiCostService()
        with pytest.raises(AiCostReportError):
            await svc.get_report("nonexistent")

    async def test_compute_projection(self) -> None:
        svc = AiCostService()
        await svc.record_cost(model_id="gpt-4", cost_type=CostType.INFERENCE, amount=100.0)
        projection = await svc.compute_projection(model_id="gpt-4", horizon_days=30)
        assert projection.projected_amount > 0
        assert projection.confidence_interval_low < projection.projected_amount

    async def test_compute_projection_no_data(self) -> None:
        svc = AiCostService()
        projection = await svc.compute_projection(model_id="gpt-4")
        assert projection.projected_amount == 0.0
        assert projection.historical_data_points == 0

    async def test_get_projection(self) -> None:
        svc = AiCostService()
        await svc.record_cost(model_id="gpt-4", cost_type=CostType.INFERENCE, amount=100.0)
        projection = await svc.compute_projection(model_id="gpt-4")
        fetched = await svc.get_projection(projection.id)
        assert fetched.id == projection.id

    async def test_get_projection_not_found(self) -> None:
        svc = AiCostService()
        with pytest.raises(AiCostReportError):
            await svc.get_projection("nonexistent")

    async def test_create_allocation(self) -> None:
        svc = AiCostService()
        now = utc_now()
        allocation = AiCostAllocation(
            id="al1",
            tenant_id="tenant1",
            amount=250.0,
            period_start=now,
            period_end=now + timedelta(days=30),
        )
        result = await svc.create_allocation(allocation)
        assert result.id == "al1"

    async def test_list_allocations(self) -> None:
        svc = AiCostService()
        now = utc_now()
        a1 = AiCostAllocation(
            id="al1",
            tenant_id="t1",
            amount=100.0,
            period_start=now,
            period_end=now + timedelta(days=30),
        )
        a2 = AiCostAllocation(
            id="al2",
            tenant_id="t2",
            amount=200.0,
            period_start=now,
            period_end=now + timedelta(days=30),
        )
        await svc.create_allocation(a1)
        await svc.create_allocation(a2)
        all_allocs = await svc.list_allocations()
        assert len(all_allocs) == 2
        t1_allocs = await svc.list_allocations(tenant_id="t1")
        assert len(t1_allocs) == 1

    async def test_detect_anomaly(self) -> None:
        svc = AiCostService()
        result = await svc.detect_anomalies(
            model_id="gpt-4",
            current_cost=500.0,
            expected_cost=100.0,
        )
        assert result["severity"] == "critical"
        assert result["deviation"] == 400.0

    async def test_detect_anomaly_no_deviation(self) -> None:
        svc = AiCostService()
        result = await svc.detect_anomalies(
            model_id="gpt-4",
            current_cost=100.0,
            expected_cost=100.0,
        )
        assert result["severity"] == "low"
        assert result["deviation"] == 0.0

    async def test_dashboard(self) -> None:
        svc = AiCostService()
        now = utc_now()
        budget = AiCostBudget(
            id="b1",
            name="Test",
            amount=1000.0,
            period=BudgetPeriod.MONTHLY,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
        )
        await svc.create_budget(budget)
        await svc.record_cost(model_id="gpt-4", cost_type=CostType.INFERENCE, amount=100.0)
        await svc.record_cost(model_id="gpt-3.5", cost_type=CostType.INFERENCE, amount=50.0)
        await svc.compute_projection(horizon_days=30)

        dashboard = await svc.get_dashboard()
        assert dashboard.current_spend == 150.0
        assert dashboard.budget_remaining == 850.0
        assert len(dashboard.top_models) > 0

    async def test_event_emission(self) -> None:
        svc = AiCostService()
        events: list[Any] = []
        svc.set_event_callback(events.append)

        await svc.record_cost(model_id="gpt-4", cost_type=CostType.INFERENCE, amount=1.0)
        assert any(isinstance(e, AiCostRecorded) for e in events)


# ── Integration ──────────────────────────────────────────────────────────────


class TestAiCostRuntimeModule:
    def test_module_name(self) -> None:
        module = AiCostRuntimeModule()
        assert module.name == "ai_cost"

    def test_service_property(self) -> None:
        module = AiCostRuntimeModule()
        assert module.service is not None
        assert isinstance(module.service, AiCostService)

    def test_custom_service(self) -> None:
        service = AiCostService()
        module = AiCostRuntimeModule(service=service)
        assert module.service is service

    @pytest.mark.asyncio
    async def test_start_stop(self) -> None:
        module = AiCostRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.health = MagicMock()
        kernel.platform.events = MagicMock()

        await module.start(kernel)
        kernel.platform.health.register.assert_called_once()

        await module.stop(kernel)


# ── Health ───────────────────────────────────────────────────────────────────


class TestAiCostHealthCheck:
    @pytest.mark.asyncio
    async def test_check_healthy(self) -> None:
        service = AiCostService()
        await service.record_cost(model_id="gpt-4", cost_type=CostType.INFERENCE, amount=1.0)
        check = AiCostHealthCheck(service=service)
        report = await check.check()
        assert report.component == "AiCostService"
        assert report.status.value == "healthy"
        assert report.details["record_count"] == 1

    @pytest.mark.asyncio
    async def test_check_degraded(self) -> None:
        service = AiCostService()
        check = AiCostHealthCheck(service=service)
        report = await check.check()
        assert report.status.value == "degraded"
