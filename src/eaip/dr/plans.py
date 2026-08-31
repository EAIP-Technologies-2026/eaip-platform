"""DR plan management — create, activate, execute, and track recovery plans."""

from __future__ import annotations

import time
from typing import Any

from eaip.dr.events import DrPlanActivated, DrPlanCreated
from eaip.dr.exceptions import PlanNotFoundError, StepExecutionError
from eaip.dr.models import (
    DrPlan,
    DrStep,
    PlanStatus,
    StepStatus,
)
from eaip.logging.context import get_logger


class DrPlanManager:
    """Manages disaster recovery plans and their lifecycle."""

    def __init__(self, event_bus: Any = None) -> None:
        self._plans: dict[str, DrPlan] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.dr.plans")

    def create_plan(self, plan: DrPlan) -> DrPlan:
        if plan.id in self._plans:
            raise ValueError(f"Plan {plan.id} already exists")
        self._plans[plan.id] = plan
        if self._event_bus is not None:
            self._event_bus.publish(DrPlanCreated(plan=plan))
        self._log.info("dr.plan.created", plan_id=plan.id, name=plan.name)
        return plan

    def get_plan(self, plan_id: str) -> DrPlan:
        plan = self._plans.get(plan_id)
        if plan is None:
            raise PlanNotFoundError(f"DR plan {plan_id!r} not found", context={"plan_id": plan_id})
        return plan

    def update_plan(self, plan_id: str, **updates: Any) -> DrPlan:
        plan = self.get_plan(plan_id)
        updated = plan.model_copy(update=updates)
        self._plans[plan_id] = updated
        self._log.info("dr.plan.updated", plan_id=plan_id)
        return updated

    def delete_plan(self, plan_id: str) -> None:
        if plan_id not in self._plans:
            raise PlanNotFoundError(f"DR plan {plan_id!r} not found", context={"plan_id": plan_id})
        del self._plans[plan_id]
        self._log.info("dr.plan.deleted", plan_id=plan_id)

    def list_plans(self) -> list[DrPlan]:
        return list(self._plans.values())

    def activate_plan(self, plan_id: str) -> DrPlan:
        plan = self.get_plan(plan_id)
        if plan.status != PlanStatus.DRAFT:
            raise ValueError(f"Cannot activate plan {plan_id} in status {plan.status}")
        updated = plan.model_copy(update={"status": PlanStatus.ACTIVE})
        self._plans[plan_id] = updated
        if self._event_bus is not None:
            self._event_bus.publish(DrPlanActivated(plan_id=plan_id, plan_name=plan.name))
        self._log.info("dr.plan.activated", plan_id=plan_id)
        return updated

    def deactivate_plan(self, plan_id: str) -> DrPlan:
        plan = self.get_plan(plan_id)
        if plan.status not in (PlanStatus.ACTIVE, PlanStatus.TESTED):
            raise ValueError(f"Cannot deactivate plan {plan_id} in status {plan.status}")
        updated = plan.model_copy(update={"status": PlanStatus.DRAFT})
        self._plans[plan_id] = updated
        self._log.info("dr.plan.deactivated", plan_id=plan_id)
        return updated

    def archive_plan(self, plan_id: str) -> DrPlan:
        plan = self.get_plan(plan_id)
        updated = plan.model_copy(update={"status": PlanStatus.ARCHIVED})
        self._plans[plan_id] = updated
        self._log.info("dr.plan.archived", plan_id=plan_id)
        return updated

    async def execute_step(self, plan_id: str, step_id: str) -> DrStep:
        plan = self.get_plan(plan_id)
        step = next((s for s in plan.steps if s.id == step_id), None)
        if step is None:
            raise StepExecutionError(
                f"Step {step_id!r} not found in plan {plan_id!r}",
                context={"plan_id": plan_id, "step_id": step_id},
            )

        for required_id in step.required_steps:
            required = next((s for s in plan.steps if s.id == required_id), None)
            if required and required.status != StepStatus.COMPLETED:
                raise StepExecutionError(
                    f"Required step {required_id!r} not completed",
                    context={"plan_id": plan_id, "step_id": step_id, "required_step": required_id},
                )

        running = step.model_copy(update={"status": StepStatus.RUNNING})
        self._update_step_in_plan(plan, running)
        t0 = time.monotonic()
        try:
            await self._run_step_action(step)
            completed = running.model_copy(
                update={
                    "status": StepStatus.COMPLETED,
                    "duration_ms": (time.monotonic() - t0) * 1000,
                },
            )
            self._update_step_in_plan(plan, completed)
            return completed
        except Exception as exc:
            failed = running.model_copy(
                update={
                    "status": StepStatus.FAILED,
                    "duration_ms": (time.monotonic() - t0) * 1000,
                    "error": str(exc),
                },
            )
            self._update_step_in_plan(plan, failed)
            raise StepExecutionError(
                f"Step {step_id!r} failed: {exc}",
                context={"plan_id": plan_id, "step_id": step_id},
            ) from exc

    async def _run_step_action(self, step: DrStep) -> None:
        if step.automation_ref and self._event_bus is not None:
            pass
        await _default_step_executor(step)

    def _update_step_in_plan(self, plan: DrPlan, updated_step: DrStep) -> None:
        new_steps = tuple(updated_step if s.id == updated_step.id else s for s in plan.steps)
        self._plans[plan.id] = plan.model_copy(update={"steps": new_steps})

    async def execute_plan(self, plan_id: str, trigger_reason: str = "") -> DrPlan:
        plan = self.get_plan(plan_id)
        if plan.status not in (PlanStatus.ACTIVE, PlanStatus.TESTED):
            raise ValueError(f"Plan {plan_id} is not active (status: {plan.status})")

        ordered = sorted(plan.steps, key=lambda s: s.order)
        for step in ordered:
            await self.execute_step(plan_id, step.id)

        updated = self.get_plan(plan_id)
        self._log.info("dr.plan.executed", plan_id=plan_id, reason=trigger_reason)
        return updated

    async def get_plan_status(self, plan_id: str) -> dict[str, Any]:
        plan = self.get_plan(plan_id)
        steps_total = len(plan.steps)
        steps_completed = sum(1 for s in plan.steps if s.status == StepStatus.COMPLETED)
        steps_failed = sum(1 for s in plan.steps if s.status == StepStatus.FAILED)
        return {
            "plan_id": plan.id,
            "name": plan.name,
            "status": plan.status,
            "steps_total": steps_total,
            "steps_completed": steps_completed,
            "steps_failed": steps_failed,
            "last_tested_at": plan.last_tested_at,
        }


async def _default_step_executor(step: DrStep) -> None:
    if step.type.value in ("verify", "backup", "restore", "notify"):
        return
    if step.type.value == "test":
        return


__all__ = ["DrPlanManager"]
