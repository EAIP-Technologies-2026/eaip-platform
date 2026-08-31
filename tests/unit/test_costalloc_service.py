"""Tests for :mod:`eaip.costalloc.allocator`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.costalloc.allocator import CostAllocationService
from eaip.costalloc.exceptions import RuleNotFoundError
from eaip.costalloc.models import AllocationRule, CostAllocation


@pytest.fixture
def service() -> CostAllocationService:
    return CostAllocationService()


class TestCostAllocationService:
    @pytest.mark.asyncio
    async def test_allocate_cost(self, service: CostAllocationService) -> None:
        now = datetime.now(UTC)
        a = CostAllocation(
            id="a1", tenant_id="t1", amount=100.0, currency="USD", period_start=now, period_end=now
        )
        result = await service.allocate_cost(a)
        assert result.id == "a1"

    @pytest.mark.asyncio
    async def test_list_allocations_empty(self, service: CostAllocationService) -> None:
        assert await service.list_allocations() == []

    @pytest.mark.asyncio
    async def test_create_and_list_rules(self, service: CostAllocationService) -> None:
        rule = AllocationRule(id="r1", name="Team A", dimension="department", percentage=50.0)
        await service.create_rule(rule)
        rules = await service.list_rules()
        assert len(rules) == 1

    @pytest.mark.asyncio
    async def test_get_rule_found(self, service: CostAllocationService) -> None:
        rule = AllocationRule(id="r1", name="Team A", dimension="department", percentage=50.0)
        await service.create_rule(rule)
        found = await service.get_rule("r1")
        assert found is not None
        assert found.name == "Team A"

    @pytest.mark.asyncio
    async def test_get_rule_not_found(self, service: CostAllocationService) -> None:
        found = await service.get_rule("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_update_rule(self, service: CostAllocationService) -> None:
        rule = AllocationRule(id="r1", name="Team A", dimension="department", percentage=50.0)
        await service.create_rule(rule)
        updated = await service.update_rule("r1", {"percentage": 75.0})
        assert updated.percentage == 75.0

    @pytest.mark.asyncio
    async def test_update_rule_not_found(self, service: CostAllocationService) -> None:
        with pytest.raises(RuleNotFoundError):
            await service.update_rule("nonexistent", {"percentage": 50.0})

    @pytest.mark.asyncio
    async def test_get_allocation_found(self, service: CostAllocationService) -> None:
        now = datetime.now(UTC)
        a = CostAllocation(
            id="a1", tenant_id="t1", amount=100.0, currency="USD", period_start=now, period_end=now
        )
        await service.allocate_cost(a)
        found = await service.get_allocation("a1")
        assert found is not None
        assert found.amount == 100.0

    @pytest.mark.asyncio
    async def test_get_allocation_not_found(self, service: CostAllocationService) -> None:
        found = await service.get_allocation("nonexistent")
        assert found is None
