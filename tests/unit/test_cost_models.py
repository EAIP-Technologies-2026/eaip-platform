"""Tests for :mod:`eaip.cost.models`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.cost.models import (
    AlertStatus,
    BudgetPeriod,
    BudgetScope,
    Category,
    ChargebackItem,
    ChargebackReport,
    CostAlert,
    CostBudget,
    CostConfig,
    CostRecord,
    OptimizationRecommendation,
    RecommendationEffort,
    RecommendationRisk,
    RecommendationStatus,
    RecommendationType,
)


class TestCostRecord:
    def test_create_minimal(self) -> None:
        r = CostRecord(id="r1", category=Category.COMPUTE, amount=10.5, currency="USD")
        assert r.id == "r1"
        assert r.category is Category.COMPUTE
        assert r.amount == 10.5
        assert r.currency == "USD"
        assert r.tenant_id is None

    def test_create_full(self) -> None:
        now = datetime.now(UTC)
        r = CostRecord(
            id="r2",
            category=Category.AI,
            amount=99.99,
            currency="USD",
            tenant_id="t1",
            workflow_id="w1",
            agent_id="a1",
            user_id="u1",
            resource_type="gpu",
            resource_id="gpu-001",
            timestamp=now,
            tags=("prod", "us-east"),
            metadata={"region": "eastus"},
            billed_period_start=now,
            billed_period_end=now,
        )
        assert r.tenant_id == "t1"
        assert r.tags == ("prod", "us-east")

    def test_frozen(self) -> None:
        r = CostRecord(id="r3", category=Category.STORAGE, amount=5.0, currency="USD")
        with pytest.raises(ValidationError):
            r.amount = 10.0

    def test_category_enum_values(self) -> None:
        assert Category.COMPUTE.value == "compute"
        assert Category.STORAGE.value == "storage"
        assert Category.NETWORK.value == "network"
        assert Category.API.value == "api"
        assert Category.AI.value == "ai"
        assert Category.OTHER.value == "other"


class TestCostBudget:
    def test_create_minimal(self) -> None:
        now = datetime.now(UTC)
        b = CostBudget(
            id="b1",
            name="Monthly Compute",
            amount=1000.0,
            currency="USD",
            period=BudgetPeriod.MONTHLY,
            scope=BudgetScope.TENANT,
            scope_id="t1",
            start_date=now,
            end_date=now,
        )
        assert b.id == "b1"
        assert b.alert_thresholds == (0.8, 0.9, 1.0)
        assert b.enabled is True

    def test_custom_alert_thresholds(self) -> None:
        now = datetime.now(UTC)
        b = CostBudget(
            id="b2",
            name="Test",
            amount=500.0,
            currency="USD",
            period=BudgetPeriod.WEEKLY,
            scope=BudgetScope.GLOBAL,
            start_date=now,
            end_date=now,
            alert_thresholds=(0.5, 0.75, 0.95),
        )
        assert b.alert_thresholds == (0.5, 0.75, 0.95)

    def test_frozen(self) -> None:
        now = datetime.now(UTC)
        b = CostBudget(
            id="b3",
            name="Test",
            amount=100.0,
            currency="USD",
            period=BudgetPeriod.DAILY,
            scope=BudgetScope.GLOBAL,
            start_date=now,
            end_date=now,
        )
        with pytest.raises(ValidationError):
            b.amount = 200.0

    def test_scope_enum_values(self) -> None:
        assert BudgetScope.TENANT.value == "tenant"
        assert BudgetScope.WORKFLOW.value == "workflow"
        assert BudgetScope.AGENT.value == "agent"
        assert BudgetScope.GLOBAL.value == "global"

    def test_period_enum_values(self) -> None:
        assert BudgetPeriod.DAILY.value == "daily"
        assert BudgetPeriod.WEEKLY.value == "weekly"
        assert BudgetPeriod.MONTHLY.value == "monthly"
        assert BudgetPeriod.QUARTERLY.value == "quarterly"
        assert BudgetPeriod.YEARLY.value == "yearly"

    def test_disabled_budget(self) -> None:
        now = datetime.now(UTC)
        b = CostBudget(
            id="b4",
            name="Test",
            amount=100.0,
            currency="USD",
            period=BudgetPeriod.DAILY,
            scope=BudgetScope.GLOBAL,
            start_date=now,
            end_date=now,
            enabled=False,
        )
        assert b.enabled is False


class TestCostAlert:
    def test_create_defaults(self) -> None:
        a = CostAlert(
            id="a1",
            budget_id="b1",
            threshold=0.8,
            actual_spend=800.0,
            budgeted_amount=1000.0,
            percentage=0.8,
        )
        assert a.status is AlertStatus.ACTIVE
        assert a.acknowledged_at is None

    def test_acknowledged(self) -> None:
        now = datetime.now(UTC)
        a = CostAlert(
            id="a2",
            budget_id="b1",
            threshold=0.9,
            actual_spend=900.0,
            budgeted_amount=1000.0,
            percentage=0.9,
            status=AlertStatus.ACKNOWLEDGED,
            acknowledged_at=now,
        )
        assert a.status is AlertStatus.ACKNOWLEDGED
        assert a.acknowledged_at == now

    def test_resolved(self) -> None:
        now = datetime.now(UTC)
        a = CostAlert(
            id="a3",
            budget_id="b1",
            threshold=1.0,
            actual_spend=1000.0,
            budgeted_amount=1000.0,
            percentage=1.0,
            status=AlertStatus.RESOLVED,
            resolved_at=now,
        )
        assert a.status is AlertStatus.RESOLVED

    def test_notified_users(self) -> None:
        a = CostAlert(
            id="a4",
            budget_id="b1",
            threshold=0.8,
            actual_spend=800.0,
            budgeted_amount=1000.0,
            percentage=0.8,
            notified_users=("alice@example.com", "bob@example.com"),
        )
        assert len(a.notified_users) == 2


class TestOptimizationRecommendation:
    def test_create_defaults(self) -> None:
        r = OptimizationRecommendation(
            id="r1",
            type=RecommendationType.RIGHTSIZE,
            resource_type="vm",
            resource_id="vm-001",
            current_cost=500.0,
            estimated_savings=150.0,
            effort=RecommendationEffort.MEDIUM,
            risk=RecommendationRisk.LOW,
            description="Rightsize vm-001",
            rationale="Underutilized",
        )
        assert r.status is RecommendationStatus.OPEN

    def test_lifecycle_statuses(self) -> None:
        r = OptimizationRecommendation(
            id="r2",
            type=RecommendationType.STOP,
            resource_type="disk",
            resource_id="disk-001",
            current_cost=5.0,
            estimated_savings=5.0,
            effort=RecommendationEffort.LOW,
            risk=RecommendationRisk.LOW,
            description="Stop disk",
            rationale="Unused",
            status=RecommendationStatus.APPLIED,
        )
        assert r.status is RecommendationStatus.APPLIED

    def test_type_enum_values(self) -> None:
        assert RecommendationType.RIGHTSIZE.value == "rightsize"
        assert RecommendationType.STOP.value == "stop"
        assert RecommendationType.DELETE.value == "delete"
        assert RecommendationType.MIGRATE.value == "migrate"
        assert RecommendationType.COMPRESS.value == "compress"

    def test_effort_risk_enums(self) -> None:
        assert RecommendationEffort.LOW.value == "low"
        assert RecommendationRisk.HIGH.value == "high"


class TestChargebackModels:
    def test_chargeback_item(self) -> None:
        item = ChargebackItem(
            tenant_id="t1",
            tenant_name="Acme Corp",
            category=Category.COMPUTE,
            amount=500.0,
            percentage=50.0,
            usage_metrics={"vm_count": 5.0},
        )
        assert item.tenant_id == "t1"
        assert item.usage_metrics["vm_count"] == 5.0

    def test_chargeback_report_empty(self) -> None:
        now = datetime.now(UTC)
        report = ChargebackReport(
            id="cb1",
            period_start=now,
            period_end=now,
            total_cost=0.0,
            currency="USD",
        )
        assert report.total_cost == 0.0
        assert report.items == ()

    def test_chargeback_report_with_items(self) -> None:
        now = datetime.now(UTC)
        items = (
            ChargebackItem(
                tenant_id="t1",
                tenant_name="Acme",
                category=Category.COMPUTE,
                amount=800.0,
                percentage=80.0,
            ),
            ChargebackItem(
                tenant_id="t2",
                tenant_name="Beta",
                category=Category.STORAGE,
                amount=200.0,
                percentage=20.0,
            ),
        )
        report = ChargebackReport(
            id="cb2",
            period_start=now,
            period_end=now,
            total_cost=1000.0,
            items=items,
            currency="USD",
        )
        assert len(report.items) == 2
        assert report.total_cost == 1000.0

    def test_chargeback_item_frozen(self) -> None:
        item = ChargebackItem(
            tenant_id="t1",
            tenant_name="T1",
            category=Category.OTHER,
            amount=0.0,
            percentage=0.0,
        )
        with pytest.raises(ValidationError):
            item.amount = 100.0


class TestCostConfig:
    def test_defaults(self) -> None:
        c = CostConfig()
        assert c.default_currency == "USD"
        assert c.enable_budget_alerts is True
        assert c.enable_optimization is True
        assert c.alert_check_interval_hours == 1
        assert c.data_retention_days == 365
        assert c.exchange_rates == {}

    def test_custom(self) -> None:
        c = CostConfig(
            default_currency="EUR",
            enable_budget_alerts=False,
            data_retention_days=90,
            exchange_rates={"USD": 1.0, "EUR": 0.85},
        )
        assert c.default_currency == "EUR"
        assert c.exchange_rates["EUR"] == 0.85

    def test_frozen(self) -> None:
        c = CostConfig()
        with pytest.raises(ValidationError):
            c.default_currency = "GBP"


def test_model_with_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        CostRecord(id="x", category=Category.OTHER, amount=1.0, currency="USD", unknown="field")
