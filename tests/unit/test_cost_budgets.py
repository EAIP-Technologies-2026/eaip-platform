"""Tests for :mod:`eaip.cost.budgets`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.cost.alerts import AlertService
from eaip.cost.budgets import BudgetManager
from eaip.cost.exceptions import BudgetNotFoundError
from eaip.cost.models import BudgetPeriod, BudgetScope, Category, CostBudget, CostRecord
from eaip.cost.tracker import CostTracker


@pytest.fixture
def tracker() -> CostTracker:
    return CostTracker()


@pytest.fixture
def alert_service() -> AlertService:
    return AlertService()


@pytest.fixture
def manager(tracker: CostTracker, alert_service: AlertService) -> BudgetManager:
    return BudgetManager(tracker, alert_service)


@pytest.fixture
def sample_budget() -> CostBudget:
    now = datetime.now(UTC)
    return CostBudget(
        id="b1",
        name="Monthly Compute Budget",
        amount=1000.0,
        currency="USD",
        period=BudgetPeriod.MONTHLY,
        scope=BudgetScope.TENANT,
        scope_id="t1",
        start_date=now,
        end_date=now,
        category=Category.COMPUTE,
    )


class TestCreateBudget:
    @pytest.mark.asyncio
    async def test_create(self, manager: BudgetManager, sample_budget: CostBudget) -> None:
        created = await manager.create_budget(sample_budget)
        assert created.id == "b1"
        assert created.name == "Monthly Compute Budget"

    @pytest.mark.asyncio
    async def test_duplicate_overwrites(
        self, manager: BudgetManager, sample_budget: CostBudget
    ) -> None:
        await manager.create_budget(sample_budget)
        b2 = CostBudget(
            id="b1",
            name="Updated",
            amount=2000.0,
            currency="USD",
            period=BudgetPeriod.MONTHLY,
            scope=BudgetScope.GLOBAL,
            start_date=sample_budget.start_date,
            end_date=sample_budget.end_date,
        )
        created = await manager.create_budget(b2)
        assert created.name == "Updated"


class TestGetBudget:
    @pytest.mark.asyncio
    async def test_get(self, manager: BudgetManager, sample_budget: CostBudget) -> None:
        await manager.create_budget(sample_budget)
        b = await manager.get_budget("b1")
        assert b.id == "b1"

    @pytest.mark.asyncio
    async def test_get_not_found(self, manager: BudgetManager) -> None:
        with pytest.raises(BudgetNotFoundError):
            await manager.get_budget("nonexistent")


class TestUpdateBudget:
    @pytest.mark.asyncio
    async def test_update(self, manager: BudgetManager, sample_budget: CostBudget) -> None:
        await manager.create_budget(sample_budget)
        updated = await manager.update_budget("b1", {"amount": 2000.0})
        assert updated.amount == 2000.0

    @pytest.mark.asyncio
    async def test_update_not_found(self, manager: BudgetManager) -> None:
        with pytest.raises(BudgetNotFoundError):
            await manager.update_budget("nonexistent", {"amount": 100.0})


class TestDeleteBudget:
    @pytest.mark.asyncio
    async def test_delete(self, manager: BudgetManager, sample_budget: CostBudget) -> None:
        await manager.create_budget(sample_budget)
        await manager.delete_budget("b1")
        with pytest.raises(BudgetNotFoundError):
            await manager.get_budget("b1")

    @pytest.mark.asyncio
    async def test_delete_not_found(self, manager: BudgetManager) -> None:
        with pytest.raises(BudgetNotFoundError):
            await manager.delete_budget("nonexistent")


class TestListBudgets:
    @pytest.mark.asyncio
    async def test_list_all(self, manager: BudgetManager, sample_budget: CostBudget) -> None:
        await manager.create_budget(sample_budget)
        budgets = await manager.list_budgets()
        assert len(budgets) == 1

    @pytest.mark.asyncio
    async def test_list_empty(self, manager: BudgetManager) -> None:
        budgets = await manager.list_budgets()
        assert budgets == []

    @pytest.mark.asyncio
    async def test_list_by_scope(self, manager: BudgetManager, sample_budget: CostBudget) -> None:
        await manager.create_budget(sample_budget)
        budgets = await manager.list_budgets(scope="tenant")
        assert len(budgets) == 1
        budgets = await manager.list_budgets(scope="workflow")
        assert budgets == []

    @pytest.mark.asyncio
    async def test_list_by_category(
        self, manager: BudgetManager, sample_budget: CostBudget
    ) -> None:
        await manager.create_budget(sample_budget)
        budgets = await manager.list_budgets(category="compute")
        assert len(budgets) == 1
        budgets = await manager.list_budgets(category="storage")
        assert budgets == []


class TestCheckBudgets:
    @pytest.mark.asyncio
    async def test_check_no_budgets(self, manager: BudgetManager) -> None:
        triggered = await manager.check_budgets()
        assert triggered == []

    @pytest.mark.asyncio
    async def test_check_budget_not_exceeded(
        self, manager: BudgetManager, sample_budget: CostBudget
    ) -> None:
        await manager.create_budget(sample_budget)
        triggered = await manager.check_budgets()
        assert triggered == []

    @pytest.mark.asyncio
    async def test_check_budget_exceeded(
        self, manager: BudgetManager, sample_budget: CostBudget, tracker: CostTracker
    ) -> None:
        await manager.create_budget(sample_budget)
        tracker._records.append(
            CostRecord(
                id="r1",
                category=Category.COMPUTE,
                amount=2000.0,
                currency="USD",
                tenant_id="t1",
            )
        )
        triggered = await manager.check_budgets()
        assert len(triggered) > 0

    @pytest.mark.asyncio
    async def test_disabled_budget_not_checked(
        self, manager: BudgetManager, sample_budget: CostBudget, tracker: CostTracker
    ) -> None:
        now = datetime.now(UTC)
        disabled = CostBudget(
            id="b2",
            name="Disabled",
            amount=100.0,
            currency="USD",
            period=BudgetPeriod.DAILY,
            scope=BudgetScope.GLOBAL,
            start_date=now,
            end_date=now,
            enabled=False,
        )
        await manager.create_budget(disabled)
        tracker._records.append(
            CostRecord(id="r1", category=Category.OTHER, amount=9999.0, currency="USD")
        )
        triggered = await manager.check_budgets()
        assert triggered == []


class TestBudgetStatus:
    @pytest.mark.asyncio
    async def test_budget_status(
        self, manager: BudgetManager, sample_budget: CostBudget, tracker: CostTracker
    ) -> None:
        await manager.create_budget(sample_budget)
        tracker._records.append(
            CostRecord(
                id="r1",
                category=Category.COMPUTE,
                amount=300.0,
                currency="USD",
                tenant_id="t1",
            )
        )
        status = await manager.get_budget_status("b1")
        assert status["current_spend"] == 300.0
        assert status["budgeted_amount"] == 1000.0
        assert status["percentage"] == 0.3
        assert status["remaining"] == 700.0

    @pytest.mark.asyncio
    async def test_budget_status_not_found(self, manager: BudgetManager) -> None:
        with pytest.raises(BudgetNotFoundError):
            await manager.get_budget_status("nonexistent")
