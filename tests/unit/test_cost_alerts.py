"""Tests for :mod:`eaip.cost.alerts`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.cost.alerts import AlertService
from eaip.cost.exceptions import AlertNotFoundError
from eaip.cost.models import AlertStatus, BudgetPeriod, BudgetScope, CostBudget


@pytest.fixture
def alert_service() -> AlertService:
    return AlertService()


@pytest.fixture
def sample_budget() -> CostBudget:
    now = datetime.now(UTC)
    return CostBudget(
        id="b1",
        name="Monthly Budget",
        amount=1000.0,
        currency="USD",
        period=BudgetPeriod.MONTHLY,
        scope=BudgetScope.GLOBAL,
        start_date=now,
        end_date=now,
    )


class TestCheckAndAlert:
    @pytest.mark.asyncio
    async def test_alert_created(
        self, alert_service: AlertService, sample_budget: CostBudget
    ) -> None:
        result = await alert_service.check_and_alert(sample_budget, 900.0, 0.9, 0.9)
        assert result is not None
        assert result["percentage"] == 0.9

    @pytest.mark.asyncio
    async def test_no_duplicate_active_alerts(
        self, alert_service: AlertService, sample_budget: CostBudget
    ) -> None:
        r1 = await alert_service.check_and_alert(sample_budget, 900.0, 0.9, 0.9)
        assert r1 is not None
        r2 = await alert_service.check_and_alert(sample_budget, 950.0, 0.95, 0.9)
        assert r2 is None

    @pytest.mark.asyncio
    async def test_different_threshold_allows_new_alert(
        self, alert_service: AlertService, sample_budget: CostBudget
    ) -> None:
        await alert_service.check_and_alert(sample_budget, 800.0, 0.8, 0.8)
        r2 = await alert_service.check_and_alert(sample_budget, 950.0, 0.95, 0.95)
        assert r2 is not None

    @pytest.mark.asyncio
    async def test_multiple_thresholds(
        self, alert_service: AlertService, sample_budget: CostBudget
    ) -> None:
        r1 = await alert_service.check_and_alert(sample_budget, 800.0, 0.8, 0.8)
        r2 = await alert_service.check_and_alert(sample_budget, 900.0, 0.9, 0.9)
        r3 = await alert_service.check_and_alert(sample_budget, 1000.0, 1.0, 1.0)
        assert r1 is not None
        assert r2 is not None
        assert r3 is not None


class TestAcknowledgeAlert:
    @pytest.mark.asyncio
    async def test_acknowledge(
        self, alert_service: AlertService, sample_budget: CostBudget
    ) -> None:
        await alert_service.check_and_alert(sample_budget, 900.0, 0.9, 0.9)
        alerts = await alert_service.list_alerts()
        alert_id = alerts[0].id
        updated = await alert_service.acknowledge_alert(alert_id)
        assert updated.status is AlertStatus.ACKNOWLEDGED
        assert updated.acknowledged_at is not None

    @pytest.mark.asyncio
    async def test_acknowledge_not_found(self, alert_service: AlertService) -> None:
        with pytest.raises(AlertNotFoundError):
            await alert_service.acknowledge_alert("nonexistent")


class TestResolveAlert:
    @pytest.mark.asyncio
    async def test_resolve(self, alert_service: AlertService, sample_budget: CostBudget) -> None:
        await alert_service.check_and_alert(sample_budget, 1000.0, 1.0, 1.0)
        alerts = await alert_service.list_alerts()
        alert_id = alerts[0].id
        updated = await alert_service.resolve_alert(alert_id)
        assert updated.status is AlertStatus.RESOLVED
        assert updated.resolved_at is not None

    @pytest.mark.asyncio
    async def test_resolve_not_found(self, alert_service: AlertService) -> None:
        with pytest.raises(AlertNotFoundError):
            await alert_service.resolve_alert("nonexistent")


class TestListAlerts:
    @pytest.mark.asyncio
    async def test_list_all(self, alert_service: AlertService, sample_budget: CostBudget) -> None:
        await alert_service.check_and_alert(sample_budget, 900.0, 0.9, 0.9)
        alerts = await alert_service.list_alerts()
        assert len(alerts) == 1

    @pytest.mark.asyncio
    async def test_list_empty(self, alert_service: AlertService) -> None:
        alerts = await alert_service.list_alerts()
        assert alerts == []

    @pytest.mark.asyncio
    async def test_list_by_budget(
        self, alert_service: AlertService, sample_budget: CostBudget
    ) -> None:
        b2 = CostBudget(
            id="b2",
            name="B2",
            amount=500.0,
            currency="USD",
            period=BudgetPeriod.MONTHLY,
            scope=BudgetScope.GLOBAL,
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC),
        )
        await alert_service.check_and_alert(sample_budget, 900.0, 0.9, 0.9)
        await alert_service.check_and_alert(b2, 450.0, 0.9, 0.9)
        alerts_b1 = await alert_service.list_alerts(budget_id="b1")
        assert len(alerts_b1) == 1

    @pytest.mark.asyncio
    async def test_list_by_status(
        self, alert_service: AlertService, sample_budget: CostBudget
    ) -> None:
        await alert_service.check_and_alert(sample_budget, 900.0, 0.9, 0.9)
        active = await alert_service.list_alerts(status="active")
        assert len(active) == 1
        resolved = await alert_service.list_alerts(status="resolved")
        assert resolved == []
