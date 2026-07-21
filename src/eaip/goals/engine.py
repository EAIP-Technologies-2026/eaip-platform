"""GoalEngine — manages goals, evaluates progress, and orchestrates objective deployment."""

from __future__ import annotations

from typing import Any

from eaip.goals.events import (
    GoalCompleted,
    GoalCreated,
    GoalFailed,
    GoalProgressUpdated,
    GoalUpdated,
    ObjectiveAssigned,
)
from eaip.goals.exceptions import GoalNotFoundError, GoalValidationError
from eaip.goals.models import (
    BusinessGoal,
    GoalConfig,
    GoalProgress,
    GoalStatus,
    Objective,
    ObjectiveStatus,
)
from eaip.goals.tracker import GoalTracker
from eaip.logging.context import get_logger


class GoalEngine:
    """In-memory goal engine with lifecycle management and progress evaluation."""

    def __init__(
        self,
        tracker: GoalTracker | None = None,
        config: GoalConfig | None = None,
        event_bus: Any = None,
        workforce_orchestrator: Any = None,
    ) -> None:
        self._goals: dict[str, BusinessGoal] = {}
        self._tracker = tracker or GoalTracker()
        self._config = config or GoalConfig()
        self._event_bus = event_bus
        self._workforce_orchestrator = workforce_orchestrator
        self._progress_cache: dict[str, GoalProgress] = {}
        self._log = get_logger("eaip.goals.engine")

    async def create_goal(self, goal: BusinessGoal) -> BusinessGoal:
        """Create a new goal."""
        if goal.id in self._goals:
            raise GoalValidationError(f"goal already exists: {goal.id!r}")

        self._goals[goal.id] = goal

        # Register KPIs with tracker
        for kpi in goal.kpis:
            self._tracker.register_kpi(kpi)
        for obj in goal.objectives:
            for kpi in obj.kpis:
                self._tracker.register_kpi(kpi)

        await self._publish(
            GoalCreated(
                goal_id=goal.id,
                goal_name=goal.name,
                owner=goal.owner,
                priority=goal.priority.value,
            )
        )
        self._log.info("goal.created", goal_id=goal.id, name=goal.name)
        return goal

    async def update_goal(self, goal_id: str, updates: dict[str, Any]) -> BusinessGoal:
        """Update an existing goal."""
        if goal_id not in self._goals:
            raise GoalNotFoundError(goal_id)

        current = self._goals[goal_id]
        updated = current.model_copy(update=updates)
        self._goals[goal_id] = updated

        await self._publish(GoalUpdated(goal_id=goal_id, changes=updates))
        self._log.info("goal.updated", goal_id=goal_id)
        return updated

    async def get_goal(self, goal_id: str) -> BusinessGoal:
        """Get a goal by ID."""
        if goal_id not in self._goals:
            raise GoalNotFoundError(goal_id)
        return self._goals[goal_id]

    async def list_goals(
        self, status: str | None = None, owner: str | None = None
    ) -> list[BusinessGoal]:
        """List all goals, optionally filtered by status or owner."""
        results: list[BusinessGoal] = []
        for goal in self._goals.values():
            if status and goal.status.value != status:
                continue
            if owner and goal.owner != owner:
                continue
            results.append(goal)
        return results

    async def delete_goal(self, goal_id: str) -> None:
        """Delete a goal."""
        if goal_id not in self._goals:
            raise GoalNotFoundError(goal_id)
        del self._goals[goal_id]
        self._progress_cache.pop(goal_id, None)
        self._log.info("goal.deleted", goal_id=goal_id)

    async def evaluate_progress(self, goal_id: str) -> GoalProgress:
        """Evaluate KPI progress for a goal and return a progress snapshot."""
        goal = await self.get_goal(goal_id)

        kpi_values: dict[str, float] = {}
        for kpi in goal.kpis:
            status = await self._tracker.check_kpi_status(kpi.id)
            kpi_values[kpi.id] = status["progress"]

        objectives_progress: dict[str, float] = {}
        total_weight = sum(o.weight for o in goal.objectives) or 1.0
        for obj in goal.objectives:
            obj_kpi_progress = 0.0
            if obj.kpis:
                obj_progress_sum = 0.0
                for kpi in obj.kpis:
                    status = await self._tracker.check_kpi_status(kpi.id)
                    obj_progress_sum += status["progress"]
                    kpi_values[kpi.id] = status["progress"]
                obj_kpi_progress = obj_progress_sum / len(obj.kpis)
            else:
                obj_kpi_progress = (
                    obj.target_value / max(obj.target_value, 1.0) if obj.target_value > 0 else 0.0
                )
            obj_kpi_progress = min(obj_kpi_progress, 1.0)
            objectives_progress[obj.id] = round(obj_kpi_progress * 100, 2)

        overall = 0.0
        for obj in goal.objectives:
            obj_progress = objectives_progress.get(obj.id, 0.0) / 100.0
            overall += obj_progress * (obj.weight / total_weight)
        overall = round(min(overall * 100, 100.0), 2)

        progress = GoalProgress(
            goal_id=goal_id,
            overall_progress=overall,
            objectives_progress=objectives_progress,
            kpi_values=kpi_values,
        )
        self._progress_cache[goal_id] = progress

        await self._publish(
            GoalProgressUpdated(
                goal_id=goal_id,
                overall_progress=overall,
                objectives_progress=objectives_progress,
                kpi_values=kpi_values,
            )
        )
        return progress

    async def check_goal_status(self, goal_id: str) -> GoalStatus:
        """Check if a goal is completed or failed based on KPI progress."""
        goal = await self.get_goal(goal_id)
        if goal.status in (GoalStatus.COMPLETED, GoalStatus.FAILED, GoalStatus.CANCELLED):
            return goal.status

        if goal_id not in self._progress_cache:
            await self.evaluate_progress(goal_id)

        progress = self._progress_cache[goal_id]

        all_completed = len(goal.objectives) > 0
        for obj in goal.objectives:
            obj_progress = progress.objectives_progress.get(obj.id, 0.0)
            if obj_progress < 100.0:
                all_completed = False
                break

        if all_completed:
            updated = goal.model_copy(update={"status": GoalStatus.COMPLETED})
            self._goals[goal_id] = updated
            await self._publish(
                GoalCompleted(
                    goal_id=goal_id,
                    goal_name=goal.name,
                    final_progress=progress.overall_progress,
                )
            )
            self._log.info("goal.completed", goal_id=goal_id)
            return GoalStatus.COMPLETED

        has_failed = False
        for obj in goal.objectives:
            if obj.status is ObjectiveStatus.FAILED:
                has_failed = True
                break

        if has_failed:
            updated = goal.model_copy(update={"status": GoalStatus.FAILED})
            self._goals[goal_id] = updated
            await self._publish(
                GoalFailed(
                    goal_id=goal_id,
                    goal_name=goal.name,
                    reason="one or more objectives failed",
                )
            )
            self._log.info("goal.failed", goal_id=goal_id)
            return GoalStatus.FAILED

        return goal.status

    async def assign_objective(self, objective_id: str, worker_id: str) -> Objective:
        """Assign an objective to a workforce worker."""
        for goal in self._goals.values():
            for obj in goal.objectives:
                if obj.id == objective_id:
                    updated = obj.model_copy(
                        update={
                            "assigned_worker_id": worker_id,
                            "status": ObjectiveStatus.IN_PROGRESS,
                        }
                    )
                    # Reconstruct goal with updated objective
                    new_objectives = tuple(
                        updated if o.id == objective_id else o for o in goal.objectives
                    )
                    new_goal = goal.model_copy(update={"objectives": new_objectives})
                    self._goals[goal.id] = new_goal

                    await self._publish(
                        ObjectiveAssigned(
                            objective_id=objective_id,
                            goal_id=goal.id,
                            worker_id=worker_id,
                        )
                    )
                    self._log.info(
                        "objective.assigned",
                        objective_id=objective_id,
                        worker_id=worker_id,
                    )
                    return updated

        raise GoalNotFoundError(objective_id)

    async def deploy_objectives(self, goal_id: str) -> list[Objective]:
        """Deploy all objectives as workforce assignments."""
        goal = await self.get_goal(goal_id)
        deployed: list[Objective] = []

        if self._workforce_orchestrator is None:
            self._log.warning("goal.deploy.no_orchestrator", goal_id=goal_id)
            return deployed

        for obj in goal.objectives:
            if obj.status is ObjectiveStatus.PENDING:
                try:
                    assignment = await self._workforce_orchestrator.assign(
                        worker_id=obj.assigned_worker_id or "any",
                        task_description=f"[Goal {goal.name}] {obj.name}: {obj.description}",
                    )
                    updated = await self.assign_objective(obj.id, assignment.worker_id)
                    deployed.append(updated)
                except Exception:
                    self._log.exception("objective.deploy.failed", objective_id=obj.id)

        return deployed

    async def get_progress(self, goal_id: str) -> GoalProgress:
        """Get the current progress snapshot for a goal."""
        if goal_id not in self._progress_cache:
            return await self.evaluate_progress(goal_id)
        return self._progress_cache[goal_id]

    async def _publish(self, event: Any) -> None:
        """Publish an event via the event bus if available."""
        if self._event_bus is not None:
            await self._event_bus.publish(event)

    @property
    def tracker(self) -> GoalTracker:
        return self._tracker

    @property
    def config(self) -> GoalConfig:
        return self._config


__all__ = ["GoalEngine"]
