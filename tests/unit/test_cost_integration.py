"""Tests for :mod:`eaip.cost.integration`."""

from __future__ import annotations

import pytest

from eaip.cost.alerts import AlertService
from eaip.cost.budgets import BudgetManager
from eaip.cost.health import CostHealthCheck
from eaip.cost.integration import CostRuntimeModule
from eaip.cost.optimizer import CostOptimizer
from eaip.cost.reporting import CostReportingService
from eaip.cost.tracker import CostTracker


class TestCostRuntimeModule:
    def test_instantiation(self) -> None:
        module = CostRuntimeModule()
        assert module.name == "cost"
        assert isinstance(module.tracker, CostTracker)
        assert isinstance(module.alert_service, AlertService)
        assert isinstance(module.budget_manager, BudgetManager)
        assert isinstance(module.optimizer, CostOptimizer)
        assert isinstance(module.reporting, CostReportingService)
        assert isinstance(module.health_check, CostHealthCheck)

    def test_all_services_share_tracker(self) -> None:
        module = CostRuntimeModule()
        assert module.budget_manager._tracker is module.tracker
        assert module.optimizer._tracker is module.tracker
        assert module.reporting._tracker is module.tracker

    def test_budget_manager_uses_alert_service(self) -> None:
        module = CostRuntimeModule()
        assert module.budget_manager._alert_service is module.alert_service

    def test_health_check_references_services(self) -> None:
        module = CostRuntimeModule()
        assert module.health_check._tracker is module.tracker
        assert module.health_check._budget_manager is module.budget_manager
        assert module.health_check._alert_service is module.alert_service


class TestCostHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        module = CostRuntimeModule()
        report = await module.health_check.check()
        assert report.component == "cost"
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_details(self) -> None:
        module = CostRuntimeModule()
        report = await module.health_check.check()
        assert "budget_count" in report.details
        assert "alert_count" in report.details
        assert "record_count" in report.details

    @pytest.mark.asyncio
    async def test_health_check_with_active_alerts_degraded(self) -> None:
        module = CostRuntimeModule()
        from datetime import UTC, datetime

        from eaip.cost.models import BudgetPeriod, BudgetScope, CostBudget

        now = datetime.now(UTC)
        budget = CostBudget(
            id="b1",
            name="Test",
            amount=100.0,
            currency="USD",
            period=BudgetPeriod.DAILY,
            scope=BudgetScope.GLOBAL,
            start_date=now,
            end_date=now,
        )
        await module.budget_manager.create_budget(budget)
        # add spend exceeding 100% threshold
        from eaip.cost.models import Category, CostRecord

        module.tracker._records.append(
            CostRecord(id="r1", category=Category.COMPUTE, amount=200.0, currency="USD")
        )
        await module.budget_manager.check_budgets()
        report = await module.health_check.check()
        assert report.status.value in ("degraded", "unhealthy")
