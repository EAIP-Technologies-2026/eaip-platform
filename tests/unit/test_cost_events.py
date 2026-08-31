"""Tests for :mod:`eaip.cost.events`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.cost.events import (
    AlertAcknowledged,
    AlertCreated,
    AlertResolved,
    BudgetCreated,
    BudgetExceeded,
    BudgetThresholdReached,
    BudgetUpdated,
    ChargebackGenerated,
    CostRecorded,
    RecommendationApplied,
    RecommendationGenerated,
)


class TestCostRecorded:
    def test_minimal(self) -> None:
        e = CostRecorded(record_id="r1", category="compute", amount=10.0, currency="USD")
        assert e.event_type == "eaip.cost.recorded"
        assert e.record_id == "r1"

    def test_full(self) -> None:
        e = CostRecorded(
            record_id="r1",
            category="ai",
            amount=99.99,
            currency="USD",
            tenant_id="t1",
            workflow_id="w1",
            agent_id="a1",
            resource_type="gpu",
            resource_id="gpu-001",
        )
        assert e.tenant_id == "t1"

    def test_frozen(self) -> None:
        e = CostRecorded(record_id="r1", category="compute", amount=10.0, currency="USD")
        with pytest.raises(ValueError):
            e.amount = 20.0


class TestBudgetCreated:
    def test_create(self) -> None:
        e = BudgetCreated(
            budget_id="b1",
            name="Test",
            amount=1000.0,
            currency="USD",
            period="monthly",
            scope="tenant",
        )
        assert e.event_type == "eaip.cost.budget.created"

    def test_with_scope_id(self) -> None:
        e = BudgetCreated(
            budget_id="b1",
            name="Test",
            amount=500.0,
            currency="USD",
            period="weekly",
            scope="workflow",
            scope_id="w1",
        )
        assert e.scope_id == "w1"


class TestBudgetUpdated:
    def test_create(self) -> None:
        e = BudgetUpdated(budget_id="b1", updates={"amount": 2000.0})
        assert e.event_type == "eaip.cost.budget.updated"


class TestBudgetThresholdReached:
    def test_create(self) -> None:
        e = BudgetThresholdReached(
            budget_id="b1",
            threshold=0.8,
            actual_spend=800.0,
            budgeted_amount=1000.0,
            percentage=0.8,
        )
        assert e.event_type == "eaip.cost.budget.threshold_reached"


class TestBudgetExceeded:
    def test_create(self) -> None:
        e = BudgetExceeded(
            budget_id="b1",
            actual_spend=1200.0,
            budgeted_amount=1000.0,
            overshoot=200.0,
        )
        assert e.event_type == "eaip.cost.budget.exceeded"


class TestAlertCreated:
    def test_create(self) -> None:
        e = AlertCreated(
            alert_id="a1",
            budget_id="b1",
            threshold=0.9,
            actual_spend=900.0,
            percentage=0.9,
        )
        assert e.event_type == "eaip.cost.alert.created"


class TestAlertAcknowledged:
    def test_create(self) -> None:
        now = datetime.now(UTC)
        e = AlertAcknowledged(alert_id="a1", acknowledged_at=now)
        assert e.event_type == "eaip.cost.alert.acknowledged"


class TestAlertResolved:
    def test_create(self) -> None:
        now = datetime.now(UTC)
        e = AlertResolved(alert_id="a1", resolved_at=now)
        assert e.event_type == "eaip.cost.alert.resolved"


class TestRecommendationGenerated:
    def test_create(self) -> None:
        e = RecommendationGenerated(
            recommendation_id="r1",
            type="rightsize",
            resource_type="vm",
            resource_id="vm-001",
            estimated_savings=150.0,
        )
        assert e.event_type == "eaip.cost.recommendation.generated"


class TestRecommendationApplied:
    def test_create(self) -> None:
        e = RecommendationApplied(
            recommendation_id="r1",
            type="rightsize",
            resource_id="vm-001",
        )
        assert e.event_type == "eaip.cost.recommendation.applied"


class TestChargebackGenerated:
    def test_create(self) -> None:
        now = datetime.now(UTC)
        e = ChargebackGenerated(
            report_id="cb1",
            period_start=now,
            period_end=now,
            total_cost=1000.0,
            item_count=3,
        )
        assert e.event_type == "eaip.cost.chargeback.generated"
