"""Tests for :mod:`eaip.cost.tracker`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from eaip.cost.models import Category, CostRecord
from eaip.cost.tracker import CostTracker


@pytest.fixture
def tracker() -> CostTracker:
    return CostTracker()


@pytest.fixture
def sample_records(tracker: CostTracker) -> list[CostRecord]:
    now = datetime.now(UTC)
    records = [
        CostRecord(
            id="r1",
            category=Category.COMPUTE,
            amount=100.0,
            currency="USD",
            tenant_id="t1",
            workflow_id="w1",
            resource_type="vm",
            resource_id="vm-1",
            timestamp=now - timedelta(hours=2),
        ),
        CostRecord(
            id="r2",
            category=Category.STORAGE,
            amount=50.0,
            currency="USD",
            tenant_id="t1",
            workflow_id="w1",
            resource_type="disk",
            resource_id="disk-1",
            timestamp=now - timedelta(hours=1),
        ),
        CostRecord(
            id="r3",
            category=Category.AI,
            amount=200.0,
            currency="USD",
            tenant_id="t2",
            workflow_id="w2",
            agent_id="a1",
            resource_type="gpu",
            resource_id="gpu-1",
            timestamp=now,
        ),
        CostRecord(
            id="r4",
            category=Category.COMPUTE,
            amount=75.0,
            currency="USD",
            tenant_id="t1",
            workflow_id="w2",
            resource_type="vm",
            resource_id="vm-2",
            timestamp=now + timedelta(hours=1),
        ),
    ]
    for r in records:
        tracker._records.append(r)
    return records


class TestRecordCost:
    @pytest.mark.asyncio
    async def test_record_cost(self, tracker: CostTracker) -> None:
        r = CostRecord(id="new", category=Category.NETWORK, amount=25.0, currency="USD")
        await tracker.record_cost(r)
        assert len(tracker._records) == 1


class TestQueryCosts:
    @pytest.mark.asyncio
    async def test_query_no_filters(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        results = await tracker.query_costs()
        assert len(results) == 4

    @pytest.mark.asyncio
    async def test_query_by_tenant(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        results = await tracker.query_costs(tenant_id="t1")
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_query_by_workflow(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        results = await tracker.query_costs(workflow_id="w1")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_query_by_agent(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        results = await tracker.query_costs(agent_id="a1")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_query_by_category(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        results = await tracker.query_costs(category=Category.COMPUTE)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_query_by_category_string(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        results = await tracker.query_costs(category="compute")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_query_by_time_range(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        now = datetime.now(UTC)
        results = await tracker.query_costs(start=now - timedelta(hours=3), end=now)
        assert len(results) == 3  # r1, r2, r3 all within last 3h

    @pytest.mark.asyncio
    async def test_query_no_results(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        results = await tracker.query_costs(tenant_id="nonexistent")
        assert results == []

    @pytest.mark.asyncio
    async def test_query_multiple_filters(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        results = await tracker.query_costs(tenant_id="t1", category=Category.COMPUTE)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_query_empty_tracker(self, tracker: CostTracker) -> None:
        results = await tracker.query_costs()
        assert results == []


class TestGetTotalCost:
    @pytest.mark.asyncio
    async def test_total_cost_tenant(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        total = await tracker.get_total_cost("tenant", "t1")
        assert total == 225.0

    @pytest.mark.asyncio
    async def test_total_cost_workflow(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        total = await tracker.get_total_cost("workflow", "w1")
        assert total == 150.0

    @pytest.mark.asyncio
    async def test_total_cost_agent(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        total = await tracker.get_total_cost("agent", "a1")
        assert total == 200.0

    @pytest.mark.asyncio
    async def test_total_cost_with_period(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        now = datetime.now(UTC)
        period = (now - timedelta(hours=3), now - timedelta(minutes=30))
        total = await tracker.get_total_cost("tenant", "t1", period=period)
        assert total == 150.0

    @pytest.mark.asyncio
    async def test_total_cost_no_match(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        total = await tracker.get_total_cost("agent", "nonexistent")
        assert total == 0.0

    @pytest.mark.asyncio
    async def test_total_cost_empty(self, tracker: CostTracker) -> None:
        total = await tracker.get_total_cost("global")
        assert total == 0.0


class TestGetCostByCategory:
    @pytest.mark.asyncio
    async def test_all_tenants(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        breakdown = await tracker.get_cost_by_category()
        assert breakdown["compute"] == 175.0
        assert breakdown["storage"] == 50.0
        assert breakdown["ai"] == 200.0

    @pytest.mark.asyncio
    async def test_by_tenant(self, tracker: CostTracker, sample_records: list[CostRecord]) -> None:
        breakdown = await tracker.get_cost_by_category(tenant_id="t1")
        assert breakdown["compute"] == 175.0
        assert breakdown["storage"] == 50.0
        assert "ai" not in breakdown

    @pytest.mark.asyncio
    async def test_with_period(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        now = datetime.now(UTC)
        period = (now - timedelta(hours=3), now - timedelta(minutes=30))
        breakdown = await tracker.get_cost_by_category(period=period)
        assert breakdown["compute"] == 100.0

    @pytest.mark.asyncio
    async def test_empty_result(self, tracker: CostTracker) -> None:
        breakdown = await tracker.get_cost_by_category(tenant_id="nonexistent")
        assert breakdown == {}


class TestGetCostTrend:
    @pytest.mark.asyncio
    async def test_trend(self, tracker: CostTracker, sample_records: list[CostRecord]) -> None:
        trend = await tracker.get_cost_trend("tenant", "t1", interval=timedelta(hours=1))
        assert len(trend) >= 1

    @pytest.mark.asyncio
    async def test_trend_empty(self, tracker: CostTracker) -> None:
        trend = await tracker.get_cost_trend("tenant", "nonexistent")
        assert trend == []

    @pytest.mark.asyncio
    async def test_trend_default_interval(
        self, tracker: CostTracker, sample_records: list[CostRecord]
    ) -> None:
        trend = await tracker.get_cost_trend("tenant", "t1")
        assert len(trend) >= 1
