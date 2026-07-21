"""Tests for :mod:`eaip.cost.reporting`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from eaip.cost.models import Category, CostRecord
from eaip.cost.reporting import CostReportingService
from eaip.cost.tracker import CostTracker


@pytest.fixture
def tracker() -> CostTracker:
    return CostTracker()


@pytest.fixture
def reporting(tracker: CostTracker) -> CostReportingService:
    return CostReportingService(tracker)


@pytest.fixture
def populated_tracker(tracker: CostTracker) -> CostTracker:
    now = datetime.now(UTC)
    tracker._records = [
        CostRecord(
            id="r1",
            category=Category.COMPUTE,
            amount=500.0,
            currency="USD",
            tenant_id="t1",
            workflow_id="w1",
            resource_type="vm",
            resource_id="vm-001",
            timestamp=now - timedelta(days=1),
        ),
        CostRecord(
            id="r2",
            category=Category.STORAGE,
            amount=200.0,
            currency="USD",
            tenant_id="t1",
            workflow_id="w1",
            resource_type="disk",
            resource_id="disk-001",
            timestamp=now - timedelta(days=1),
        ),
        CostRecord(
            id="r3",
            category=Category.AI,
            amount=1000.0,
            currency="USD",
            tenant_id="t2",
            workflow_id="w2",
            agent_id="a1",
            resource_type="gpu",
            resource_id="gpu-001",
            timestamp=now,
        ),
        CostRecord(
            id="r4",
            category=Category.COMPUTE,
            amount=300.0,
            currency="USD",
            tenant_id="t2",
            workflow_id="w2",
            resource_type="vm",
            resource_id="vm-002",
            timestamp=now,
        ),
    ]
    return tracker


class TestGenerateChargeback:
    @pytest.mark.asyncio
    async def test_generate_no_data(self, reporting: CostReportingService) -> None:
        now = datetime.now(UTC)
        report = await reporting.generate_chargeback(now - timedelta(days=30), now)
        assert report.total_cost == 0.0
        assert report.items == ()

    @pytest.mark.asyncio
    async def test_generate_with_data(
        self, reporting: CostReportingService, populated_tracker: CostTracker
    ) -> None:
        now = datetime.now(UTC)
        report = await reporting.generate_chargeback(now - timedelta(days=2), now)
        assert report.total_cost == 2000.0
        assert len(report.items) == 2

    @pytest.mark.asyncio
    async def test_chargeback_percentage_sum(
        self, reporting: CostReportingService, populated_tracker: CostTracker
    ) -> None:
        now = datetime.now(UTC)
        report = await reporting.generate_chargeback(now - timedelta(days=2), now)
        total_pct = sum(item.percentage for item in report.items)
        assert abs(total_pct - 100.0) < 0.01

    @pytest.mark.asyncio
    async def test_chargeback_has_usage_metrics(
        self, reporting: CostReportingService, populated_tracker: CostTracker
    ) -> None:
        now = datetime.now(UTC)
        report = await reporting.generate_chargeback(now - timedelta(days=2), now)
        for item in report.items:
            if item.tenant_id == "t1":
                assert "vm_count" in item.usage_metrics or "disk_count" in item.usage_metrics


class TestTenantCostSummary:
    @pytest.mark.asyncio
    async def test_summary(
        self, reporting: CostReportingService, populated_tracker: CostTracker
    ) -> None:
        summary = await reporting.get_tenant_cost_summary("t1")
        assert summary["total_cost"] == 700.0
        assert summary["record_count"] == 2

    @pytest.mark.asyncio
    async def test_summary_with_period(
        self, reporting: CostReportingService, populated_tracker: CostTracker
    ) -> None:
        now = datetime.now(UTC)
        period = (now - timedelta(hours=6), now)
        summary = await reporting.get_tenant_cost_summary("t2", period=period)
        assert summary["total_cost"] == 1300.0

    @pytest.mark.asyncio
    async def test_summary_no_data(self, reporting: CostReportingService) -> None:
        summary = await reporting.get_tenant_cost_summary("nonexistent")
        assert summary["total_cost"] == 0.0
        assert summary["record_count"] == 0


class TestWorkflowCostSummary:
    @pytest.mark.asyncio
    async def test_summary(
        self, reporting: CostReportingService, populated_tracker: CostTracker
    ) -> None:
        summary = await reporting.get_workflow_cost_summary("w1")
        assert summary["total_cost"] == 700.0
        assert summary["record_count"] == 2

    @pytest.mark.asyncio
    async def test_summary_no_data(self, reporting: CostReportingService) -> None:
        summary = await reporting.get_workflow_cost_summary("nonexistent")
        assert summary["total_cost"] == 0.0


class TestTopCostDrivers:
    @pytest.mark.asyncio
    async def test_top_tenants(
        self, reporting: CostReportingService, populated_tracker: CostTracker
    ) -> None:
        drivers = await reporting.get_top_cost_drivers("tenant")
        assert len(drivers) == 2
        assert drivers[0]["id"] == "t2"
        assert drivers[0]["cost"] == 1300.0

    @pytest.mark.asyncio
    async def test_top_workflows(
        self, reporting: CostReportingService, populated_tracker: CostTracker
    ) -> None:
        drivers = await reporting.get_top_cost_drivers("workflow")
        assert len(drivers) == 2

    @pytest.mark.asyncio
    async def test_top_with_limit(
        self, reporting: CostReportingService, populated_tracker: CostTracker
    ) -> None:
        drivers = await reporting.get_top_cost_drivers("tenant", limit=1)
        assert len(drivers) == 1

    @pytest.mark.asyncio
    async def test_top_empty(self, reporting: CostReportingService) -> None:
        drivers = await reporting.get_top_cost_drivers("tenant")
        assert drivers == []
