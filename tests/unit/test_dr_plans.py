"""Tests for DR plan manager."""

from __future__ import annotations

import pytest

from eaip.dr.exceptions import PlanNotFoundError, StepExecutionError
from eaip.dr.models import (
    DrPlan,
    DrStep,
    PlanStatus,
    StepStatus,
    StepType,
)
from eaip.dr.plans import DrPlanManager


@pytest.fixture
def sample_plan() -> DrPlan:
    step1 = DrStep(
        id="s1",
        plan_id="plan_1",
        name="Verify backup",
        type=StepType.VERIFY,
        order=1,
    )
    step2 = DrStep(
        id="s2",
        plan_id="plan_1",
        name="Failover DB",
        type=StepType.FAILOVER,
        order=2,
        required_steps=("s1",),
    )
    return DrPlan(
        id="plan_1",
        name="East US DR",
        description="DR plan for East US region",
        status=PlanStatus.DRAFT,
        steps=(step1, step2),
    )


@pytest.fixture
def manager() -> DrPlanManager:
    return DrPlanManager()


class TestDrPlanManager:
    def test_create_and_get(self, manager: DrPlanManager, sample_plan: DrPlan) -> None:
        manager.create_plan(sample_plan)
        retrieved = manager.get_plan("plan_1")
        assert retrieved.id == "plan_1"
        assert retrieved.name == "East US DR"

    def test_get_not_found(self, manager: DrPlanManager) -> None:
        with pytest.raises(PlanNotFoundError):
            manager.get_plan("nonexistent")

    def test_create_duplicate(self, manager: DrPlanManager, sample_plan: DrPlan) -> None:
        manager.create_plan(sample_plan)
        with pytest.raises(ValueError, match="already exists"):
            manager.create_plan(sample_plan)

    def test_update_plan(self, manager: DrPlanManager, sample_plan: DrPlan) -> None:
        manager.create_plan(sample_plan)
        updated = manager.update_plan("plan_1", description="Updated description")
        assert updated.description == "Updated description"

    def test_delete_plan(self, manager: DrPlanManager, sample_plan: DrPlan) -> None:
        manager.create_plan(sample_plan)
        manager.delete_plan("plan_1")
        with pytest.raises(PlanNotFoundError):
            manager.get_plan("plan_1")

    def test_list_plans(self, manager: DrPlanManager, sample_plan: DrPlan) -> None:
        assert manager.list_plans() == []
        manager.create_plan(sample_plan)
        assert len(manager.list_plans()) == 1

    def test_activate_plan(self, manager: DrPlanManager, sample_plan: DrPlan) -> None:
        manager.create_plan(sample_plan)
        activated = manager.activate_plan("plan_1")
        assert activated.status == PlanStatus.ACTIVE

    def test_activate_non_draft_fails(self, manager: DrPlanManager, sample_plan: DrPlan) -> None:
        manager.create_plan(sample_plan)
        manager.activate_plan("plan_1")
        with pytest.raises(ValueError, match="Cannot activate"):
            manager.activate_plan("plan_1")

    def test_deactivate_plan(self, manager: DrPlanManager, sample_plan: DrPlan) -> None:
        manager.create_plan(sample_plan)
        manager.activate_plan("plan_1")
        deactivated = manager.deactivate_plan("plan_1")
        assert deactivated.status == PlanStatus.DRAFT

    def test_archive_plan(self, manager: DrPlanManager, sample_plan: DrPlan) -> None:
        manager.create_plan(sample_plan)
        archived = manager.archive_plan("plan_1")
        assert archived.status == PlanStatus.ARCHIVED

    async def test_execute_step_completes(
        self,
        manager: DrPlanManager,
        sample_plan: DrPlan,
    ) -> None:
        manager.create_plan(sample_plan)
        manager.activate_plan("plan_1")
        result = await manager.execute_step("plan_1", "s1")
        assert result.status == StepStatus.COMPLETED
        assert result.duration_ms > 0

    async def test_execute_step_not_found(
        self,
        manager: DrPlanManager,
        sample_plan: DrPlan,
    ) -> None:
        manager.create_plan(sample_plan)
        with pytest.raises(StepExecutionError):
            await manager.execute_step("plan_1", "nonexistent")

    async def test_execute_step_requires_prerequisite(
        self,
        manager: DrPlanManager,
        sample_plan: DrPlan,
    ) -> None:
        manager.create_plan(sample_plan)
        manager.activate_plan("plan_1")
        step2 = next(s for s in sample_plan.steps if s.id == "s2")
        assert "s1" in step2.required_steps
        with pytest.raises(StepExecutionError):
            await manager.execute_step("plan_1", "s2")

    async def test_execute_plan(self, manager: DrPlanManager, sample_plan: DrPlan) -> None:
        manager.create_plan(sample_plan)
        manager.activate_plan("plan_1")
        executed = await manager.execute_plan("plan_1", trigger_reason="Scheduled test")
        assert executed is not None

    async def test_execute_plan_not_active(
        self,
        manager: DrPlanManager,
        sample_plan: DrPlan,
    ) -> None:
        manager.create_plan(sample_plan)
        with pytest.raises(ValueError, match="is not active"):
            await manager.execute_plan("plan_1")

    async def test_get_plan_status(self, manager: DrPlanManager, sample_plan: DrPlan) -> None:
        manager.create_plan(sample_plan)
        status = await manager.get_plan_status("plan_1")
        assert status["plan_id"] == "plan_1"
        assert status["steps_total"] == 2
        assert status["steps_completed"] == 0
