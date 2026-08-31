"""Tests for DR failover manager."""

from __future__ import annotations

import pytest

from eaip.dr.exceptions import FailoverError, PlanNotFoundError
from eaip.dr.failover import FailoverManager
from eaip.dr.models import (
    DrPlan,
    FailoverEventStatus,
    PlanStatus,
)


@pytest.fixture
def active_plan() -> DrPlan:
    return DrPlan(id="plan_1", name="East US DR", status=PlanStatus.ACTIVE)


@pytest.fixture
def draft_plan() -> DrPlan:
    return DrPlan(id="plan_draft", name="Draft Plan", status=PlanStatus.DRAFT)


@pytest.fixture
def manager(active_plan: DrPlan) -> FailoverManager:
    m = FailoverManager()
    m.register_plan(active_plan)
    return m


class TestFailoverManager:
    async def test_initiate_failover(self, manager: FailoverManager) -> None:
        event = await manager.initiate_failover("plan_1", reason="Region outage")
        assert event.plan_id == "plan_1"
        assert event.status == FailoverEventStatus.IN_PROGRESS
        assert event.reason == "Region outage"

    async def test_initiate_failover_plan_not_found(
        self,
        manager: FailoverManager,
    ) -> None:
        with pytest.raises(PlanNotFoundError):
            await manager.initiate_failover("nonexistent")

    async def test_initiate_failover_not_active(
        self,
        manager: FailoverManager,
        draft_plan: DrPlan,
    ) -> None:
        manager.register_plan(draft_plan)
        with pytest.raises(FailoverError, match="not active"):
            await manager.initiate_failover("plan_draft")

    async def test_complete_failover(self, manager: FailoverManager) -> None:
        event = await manager.initiate_failover("plan_1")
        completed = await manager.complete_failover(event.id, duration_ms=1500.0)
        assert completed.status == FailoverEventStatus.COMPLETED
        assert completed.duration_ms == 1500.0

    async def test_complete_failover_not_found(
        self,
        manager: FailoverManager,
    ) -> None:
        with pytest.raises(FailoverError, match="not found"):
            await manager.complete_failover("nonexistent")

    async def test_complete_already_completed(self, manager: FailoverManager) -> None:
        event = await manager.initiate_failover("plan_1")
        await manager.complete_failover(event.id)
        with pytest.raises(FailoverError, match="Cannot complete"):
            await manager.complete_failover(event.id)

    async def test_rollback_failover(self, manager: FailoverManager) -> None:
        event = await manager.initiate_failover("plan_1")
        rolled = await manager.rollback_failover(event.id)
        assert rolled.status == FailoverEventStatus.ROLLED_BACK

    async def test_rollback_from_completed(self, manager: FailoverManager) -> None:
        event = await manager.initiate_failover("plan_1")
        await manager.complete_failover(event.id)
        rolled = await manager.rollback_failover(event.id)
        assert rolled.status == FailoverEventStatus.ROLLED_BACK

    async def test_rollback_not_found(self, manager: FailoverManager) -> None:
        with pytest.raises(FailoverError, match="not found"):
            await manager.rollback_failover("nonexistent")

    async def test_get_failover_status(self, manager: FailoverManager) -> None:
        event = await manager.initiate_failover("plan_1")
        retrieved = await manager.get_failover_status(event.id)
        assert retrieved.id == event.id

    async def test_get_failover_status_not_found(
        self,
        manager: FailoverManager,
    ) -> None:
        with pytest.raises(FailoverError):
            await manager.get_failover_status("nonexistent")

    async def test_list_failover_history(self, manager: FailoverManager) -> None:
        await manager.initiate_failover("plan_1", reason="Test 1")
        await manager.initiate_failover("plan_1", reason="Test 2")
        history = await manager.list_failover_history("plan_1")
        assert len(history) == 2

    async def test_list_failover_history_empty(
        self,
        manager: FailoverManager,
    ) -> None:
        history = await manager.list_failover_history("plan_1")
        assert history == []

    async def test_list_failover_history_limit(
        self,
        manager: FailoverManager,
    ) -> None:
        for i in range(5):
            await manager.initiate_failover("plan_1", reason=f"Test {i}")
        history = await manager.list_failover_history("plan_1", limit=3)
        assert len(history) == 3

    async def test_is_autofailover_enabled(self, manager: FailoverManager) -> None:
        manager.register_config("plan_1", auto_failover=True)
        assert await manager.is_autofailover_enabled("plan_1") is True

    async def test_is_autofailover_disabled(self, manager: FailoverManager) -> None:
        assert await manager.is_autofailover_enabled("plan_1") is False

    async def test_check_healthy(self, manager: FailoverManager) -> None:
        assert await manager.check_health("plan_1") is True

    async def test_check_healthy_no_plan(self, manager: FailoverManager) -> None:
        assert await manager.check_health("nonexistent") is False
