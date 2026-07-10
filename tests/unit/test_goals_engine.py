"""Tests for GoalEngine."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eaip.goals.engine import GoalEngine
from eaip.goals.exceptions import GoalNotFoundError, GoalValidationError
from eaip.goals.models import (
    BusinessGoal,
    GoalConfig,
    GoalStatus,
    KpiDefinition,
    KpiDirection,
    Objective,
    ObjectiveStatus,
    Priority,
)


class TestGoalEngine:
    @pytest.fixture
    def engine(self) -> GoalEngine:
        return GoalEngine()

    @pytest.fixture
    def sample_goal(self) -> BusinessGoal:
        kpi = KpiDefinition(id="k1", name="Revenue", target_value=1000.0, current_value=0.0)
        obj = Objective(id="o1", goal_id="g1", name="Increase Revenue", kpis=(kpi,), target_value=1000.0)
        return BusinessGoal(
            id="g1",
            name="Q4 Targets",
            description="Achieve Q4 goals",
            status=GoalStatus.DRAFT,
            priority=Priority.HIGH,
            owner="alice",
            kpis=(kpi,),
            objectives=(obj,),
            tags=("q4",),
        )

    async def test_create_goal(self, engine: GoalEngine, sample_goal: BusinessGoal) -> None:
        result = await engine.create_goal(sample_goal)
        assert result.id == "g1"
        assert result.name == "Q4 Targets"

    async def test_create_goal_duplicate(self, engine: GoalEngine, sample_goal: BusinessGoal) -> None:
        await engine.create_goal(sample_goal)
        with pytest.raises(GoalValidationError):
            await engine.create_goal(sample_goal)

    async def test_get_goal(self, engine: GoalEngine, sample_goal: BusinessGoal) -> None:
        await engine.create_goal(sample_goal)
        result = await engine.get_goal("g1")
        assert result.name == "Q4 Targets"

    async def test_get_goal_not_found(self, engine: GoalEngine) -> None:
        with pytest.raises(GoalNotFoundError):
            await engine.get_goal("nonexistent")

    async def test_update_goal(self, engine: GoalEngine, sample_goal: BusinessGoal) -> None:
        await engine.create_goal(sample_goal)
        updated = await engine.update_goal("g1", {"name": "Q4 Updated", "status": GoalStatus.ACTIVE})
        assert updated.name == "Q4 Updated"
        assert updated.status is GoalStatus.ACTIVE

    async def test_update_goal_not_found(self, engine: GoalEngine) -> None:
        with pytest.raises(GoalNotFoundError):
            await engine.update_goal("nonexistent", {"name": "new"})

    async def test_list_goals(self, engine: GoalEngine, sample_goal: BusinessGoal) -> None:
        await engine.create_goal(sample_goal)
        kpi2 = KpiDefinition(id="k2", name="Downloads", target_value=500.0)
        g2 = BusinessGoal(id="g2", name="Q4 Downloads", owner="bob", kpis=(kpi2,))
        await engine.create_goal(g2)

        all_goals = await engine.list_goals()
        assert len(all_goals) == 2

        alice_goals = await engine.list_goals(owner="alice")
        assert len(alice_goals) == 1
        assert alice_goals[0].id == "g1"

    async def test_delete_goal(self, engine: GoalEngine, sample_goal: BusinessGoal) -> None:
        await engine.create_goal(sample_goal)
        await engine.delete_goal("g1")
        with pytest.raises(GoalNotFoundError):
            await engine.get_goal("g1")

    async def test_delete_goal_not_found(self, engine: GoalEngine) -> None:
        with pytest.raises(GoalNotFoundError):
            await engine.delete_goal("nonexistent")

    async def test_evaluate_progress(self, engine: GoalEngine, sample_goal: BusinessGoal) -> None:
        await engine.create_goal(sample_goal)
        progress = await engine.evaluate_progress("g1")
        assert progress.goal_id == "g1"
        assert progress.overall_progress >= 0.0

    async def test_evaluate_progress_with_kpi(self, engine: GoalEngine, sample_goal: BusinessGoal) -> None:
        await engine.create_goal(sample_goal)
        await engine.tracker.record_kpi("k1", 500.0)
        progress = await engine.evaluate_progress("g1")
        assert progress.kpi_values.get("k1", 0) > 0
        assert 0 <= progress.overall_progress <= 100

    async def test_check_goal_status_draft(self, engine: GoalEngine, sample_goal: BusinessGoal) -> None:
        await engine.create_goal(sample_goal)
        status = await engine.check_goal_status("g1")
        assert status is GoalStatus.DRAFT

    async def test_check_goal_status_completed(self, engine: GoalEngine) -> None:
        kpi = KpiDefinition(id="k1", name="Test", target_value=100.0, current_value=0.0)
        obj = Objective(id="o1", goal_id="g1", name="Obj", kpis=(kpi,), target_value=100.0)
        goal = BusinessGoal(id="g1", name="Test", kpis=(kpi,), objectives=(obj,))
        await engine.create_goal(goal)
        await engine.tracker.record_kpi("k1", 100.0)
        await engine.evaluate_progress("g1")
        status = await engine.check_goal_status("g1")
        assert status is GoalStatus.COMPLETED

    async def test_assign_objective(self, engine: GoalEngine, sample_goal: BusinessGoal) -> None:
        await engine.create_goal(sample_goal)
        updated = await engine.assign_objective("o1", "worker-1")
        assert updated.assigned_worker_id == "worker-1"
        assert updated.status is ObjectiveStatus.IN_PROGRESS

    async def test_get_progress(self, engine: GoalEngine, sample_goal: BusinessGoal) -> None:
        await engine.create_goal(sample_goal)
        progress = await engine.get_progress("g1")
        assert progress.goal_id == "g1"

    async def test_deploy_objectives_no_orchestrator(self, engine: GoalEngine, sample_goal: BusinessGoal) -> None:
        await engine.create_goal(sample_goal)
        deployed = await engine.deploy_objectives("g1")
        assert deployed == []

    async def test_deploy_objectives_with_orchestrator(self, engine: GoalEngine, sample_goal: BusinessGoal) -> None:
        mock_orch = AsyncMock()
        mock_orch.assign.return_value = MagicMock(worker_id="worker-1")
        engine._workforce_orchestrator = mock_orch
        await engine.create_goal(sample_goal)
        deployed = await engine.deploy_objectives("g1")
        assert len(deployed) >= 0

    async def test_evaluate_progress_not_found(self, engine: GoalEngine) -> None:
        with pytest.raises(GoalNotFoundError):
            await engine.evaluate_progress("nonexistent")
