"""Compensation service - plan creation, execution, and rollback orchestration."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from eaip.compensation.events import (
    CompensationCompleted,
    CompensationFailed,
    CompensationPlanCreated,
    CompensationPlanExecuted,
    CompensationPlanFailed,
    CompensationPlanRolledBack,
    CompensationRolledBack,
    CompensationStarted,
    CompensationStepCompleted,
    CompensationStepFailed,
    CompensationStepSkipped,
    CompensationStepStarted,
    CompensationTransactionCompleted,
    CompensationTransactionCreated,
)
from eaip.compensation.exceptions import (
    CompensationExecutionError,
    CompensationPlanNotFoundError,
    CompensationPlanValidationError,
    CompensationRollbackError,
    CompensationStepError,
)
from eaip.compensation.models import (
    CompensationAction,
    CompensationConfig,
    CompensationPlan,
    CompensationResult,
    CompensationStatus,
    CompensationStep,
    CompensationStrategy,
    CompensationTransaction,
)
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger


class CompensationService:
    def __init__(
        self,
        config: CompensationConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._config = config or CompensationConfig()
        self._event_bus = event_bus or EventBus()
        self._log = get_logger("eaip.compensation.service")
        self._plans: dict[str, CompensationPlan] = {}
        self._transactions: dict[str, CompensationTransaction] = {}

    @property
    def config(self) -> CompensationConfig:
        return self._config

    @property
    def plans(self) -> dict[str, CompensationPlan]:
        return dict(self._plans)

    @property
    def transactions(self) -> dict[str, CompensationTransaction]:
        return dict(self._transactions)

    async def create_plan(
        self,
        name: str,
        workflow_id: str,
        workflow_name: str = "",
        steps: tuple[CompensationStep, ...] = (),
        strategy: CompensationStrategy = CompensationStrategy.SEQUENTIAL,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> CompensationPlan:
        if not name:
            raise CompensationPlanValidationError("Plan name is required")
        if not workflow_id:
            raise CompensationPlanValidationError("Workflow ID is required")

        plan = CompensationPlan(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            steps=steps,
            strategy=strategy,
            metadata=metadata or {},
        )
        self._plans[plan.id] = plan
        await self._event_bus.publish(CompensationPlanCreated(plan=plan))
        self._log.info("plan.created", plan_id=plan.id, plan_name=plan.name)
        return plan

    async def get_plan(self, plan_id: str) -> CompensationPlan:
        plan = self._plans.get(plan_id)
        if plan is None:
            raise CompensationPlanNotFoundError(
                f"Compensation plan {plan_id!r} not found",
                context={"plan_id": plan_id},
            )
        return plan

    async def list_plans(
        self,
        workflow_id: str | None = None,
        status: CompensationStatus | None = None,
    ) -> list[CompensationPlan]:
        result = list(self._plans.values())
        if workflow_id is not None:
            result = [p for p in result if p.workflow_id == workflow_id]
        if status is not None:
            result = [p for p in result if p.status == status]
        return result

    async def execute_plan(
        self,
        plan_id: str,
        context: dict[str, Any] | None = None,
    ) -> CompensationResult:
        plan = await self.get_plan(plan_id)

        if plan.status not in (CompensationStatus.PENDING, CompensationStatus.FAILED):
            raise CompensationExecutionError(
                f"Plan {plan_id!r} cannot be executed in status {plan.status}",
                context={"plan_id": plan_id, "status": plan.status},
            )

        started_at = datetime.now(UTC)

        plan = CompensationPlan(
            id=plan.id,
            name=plan.name,
            description=plan.description,
            workflow_id=plan.workflow_id,
            workflow_name=plan.workflow_name,
            steps=plan.steps,
            strategy=plan.strategy,
            scope=plan.scope,
            status=CompensationStatus.COMPENSATING,
            created_at=plan.created_at,
            executed_at=started_at,
            error=None,
            metadata=plan.metadata,
        )
        self._plans[plan_id] = plan

        await self._event_bus.publish(
            CompensationStarted(plan_id=plan.id, plan_name=plan.name),
        )

        try:
            result = await self._execute_steps(plan, context)
            duration_ms = (datetime.now(UTC) - started_at).total_seconds() * 1000
            plan = CompensationPlan(
                id=plan.id,
                name=plan.name,
                description=plan.description,
                workflow_id=plan.workflow_id,
                workflow_name=plan.workflow_name,
                steps=result.get("updated_steps", plan.steps),
                strategy=plan.strategy,
                scope=plan.scope,
                status=CompensationStatus.COMPLETED,
                created_at=plan.created_at,
                executed_at=plan.executed_at,
                completed_at=datetime.now(UTC),
                error=None,
                metadata=plan.metadata,
            )
            self._plans[plan_id] = plan
            await self._event_bus.publish(CompensationPlanExecuted(plan=plan))
            await self._event_bus.publish(
                CompensationCompleted(
                    plan_id=plan.id,
                    plan_name=plan.name,
                    total_steps=result["total_steps"],
                    completed_steps=result["completed_steps"],
                    failed_steps=result["failed_steps"],
                    duration_ms=duration_ms,
                ),
            )
            return CompensationResult(
                plan_id=plan.id,
                plan_name=plan.name,
                status=CompensationStatus.COMPLETED,
                total_steps=result["total_steps"],
                completed_steps=result["completed_steps"],
                failed_steps=result["failed_steps"],
                skipped_steps=result["skipped_steps"],
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = (datetime.now(UTC) - started_at).total_seconds() * 1000
            plan = CompensationPlan(
                id=plan.id,
                name=plan.name,
                description=plan.description,
                workflow_id=plan.workflow_id,
                workflow_name=plan.workflow_name,
                steps=plan.steps,
                strategy=plan.strategy,
                scope=plan.scope,
                status=CompensationStatus.FAILED,
                created_at=plan.created_at,
                executed_at=plan.executed_at,
                completed_at=datetime.now(UTC),
                error=str(exc),
                metadata=plan.metadata,
            )
            self._plans[plan_id] = plan
            await self._event_bus.publish(CompensationPlanFailed(plan=plan, error=str(exc)))
            await self._event_bus.publish(
                CompensationFailed(
                    plan_id=plan.id,
                    plan_name=plan.name,
                    error=str(exc),
                ),
            )
            raise CompensationExecutionError(
                f"Compensation plan {plan_id!r} execution failed: {exc}",
                context={"plan_id": plan_id},
                cause=exc,
            ) from exc

    async def _execute_steps(
        self,
        plan: CompensationPlan,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        updated_steps: list[CompensationStep] = []
        completed = 0
        failed = 0
        skipped = 0

        for step in plan.steps:
            step_started = datetime.now(UTC)

            if step.status == CompensationStatus.SKIPPED:
                updated_steps.append(step)
                skipped += 1
                continue

            await self._event_bus.publish(
                CompensationStepStarted(plan_id=plan.id, step=step),
            )

            try:
                await self._execute_step_actions(plan.id, step, context)
                step_duration = (datetime.now(UTC) - step_started).total_seconds() * 1000
                updated_step = CompensationStep(
                    id=step.id,
                    name=step.name,
                    description=step.description,
                    actions=step.actions,
                    status=CompensationStatus.COMPLETED,
                    depends_on=step.depends_on,
                    timeout_seconds=step.timeout_seconds,
                    metadata=step.metadata,
                )
                updated_steps.append(updated_step)
                completed += 1
                await self._event_bus.publish(
                    CompensationStepCompleted(
                        plan_id=plan.id,
                        step=updated_step,
                        duration_ms=step_duration,
                    ),
                )
            except Exception as exc:
                updated_step = CompensationStep(
                    id=step.id,
                    name=step.name,
                    description=step.description,
                    actions=step.actions,
                    status=CompensationStatus.FAILED,
                    depends_on=step.depends_on,
                    timeout_seconds=step.timeout_seconds,
                    metadata=step.metadata,
                )
                updated_steps.append(updated_step)
                failed += 1
                await self._event_bus.publish(
                    CompensationStepFailed(plan_id=plan.id, step=updated_step, error=str(exc)),
                )
                if plan.strategy in (
                    CompensationStrategy.FAIL_FAST,
                    CompensationStrategy.SEQUENTIAL,
                ):
                    for remaining in plan.steps[len(updated_steps) :]:
                        skipped_step = CompensationStep(
                            id=remaining.id,
                            name=remaining.name,
                            description=remaining.description,
                            actions=remaining.actions,
                            status=CompensationStatus.SKIPPED,
                            depends_on=remaining.depends_on,
                            timeout_seconds=remaining.timeout_seconds,
                            metadata=remaining.metadata,
                        )
                        updated_steps.append(skipped_step)
                        skipped += 1
                        await self._event_bus.publish(
                            CompensationStepSkipped(
                                plan_id=plan.id,
                                step=skipped_step,
                                reason=f"Previous step failed ({exc})",
                            ),
                        )
                    break

        return {
            "updated_steps": tuple(updated_steps),
            "total_steps": len(plan.steps),
            "completed_steps": completed,
            "failed_steps": failed,
            "skipped_steps": skipped,
        }

    async def _execute_step_actions(
        self,
        plan_id: str,
        step: CompensationStep,
        context: dict[str, Any] | None = None,
    ) -> None:
        for action in step.actions:
            transaction = CompensationTransaction(
                id=str(uuid.uuid4()),
                plan_id=plan_id,
                step_id=step.id,
                action=action,
                status=CompensationStatus.COMPENSATING,
            )
            self._transactions[transaction.id] = transaction
            await self._event_bus.publish(
                CompensationTransactionCreated(transaction=transaction),
            )

            try:
                async with asyncio.timeout(step.timeout_seconds):
                    await self._execute_action(action, context)
                transaction = CompensationTransaction(
                    id=transaction.id,
                    plan_id=transaction.plan_id,
                    step_id=transaction.step_id,
                    action=transaction.action,
                    status=CompensationStatus.COMPLETED,
                    started_at=transaction.started_at,
                    completed_at=datetime.now(UTC),
                    result="completed",
                )
                self._transactions[transaction.id] = transaction
                await self._event_bus.publish(
                    CompensationTransactionCompleted(transaction=transaction),
                )
            except Exception as exc:
                transaction = CompensationTransaction(
                    id=transaction.id,
                    plan_id=transaction.plan_id,
                    step_id=transaction.step_id,
                    action=transaction.action,
                    status=CompensationStatus.FAILED,
                    started_at=transaction.started_at,
                    completed_at=datetime.now(UTC),
                    error=str(exc),
                )
                self._transactions[transaction.id] = transaction
                raise CompensationStepError(
                    f"Step {step.id!r} action {action.action_type!r} failed: {exc}",
                    context={
                        "plan_id": plan_id,
                        "step_id": step.id,
                        "action_type": action.action_type,
                    },
                    cause=exc,
                ) from exc

    async def _execute_action(
        self,
        action: CompensationAction,
        _context: dict[str, Any] | None = None,
    ) -> None:
        if action.action_type == "noop":
            return
        self._log.info(
            "action.executing",
            step_id=action.step_id,
            action_type=action.action_type,
        )

    async def rollback_plan(self, plan_id: str) -> CompensationResult:
        plan = await self.get_plan(plan_id)

        if plan.status not in (CompensationStatus.COMPLETED, CompensationStatus.FAILED):
            raise CompensationRollbackError(
                f"Plan {plan_id!r} cannot be rolled back in status {plan.status}",
                context={"plan_id": plan_id, "status": plan.status},
            )

        started_at = datetime.now(UTC)

        plan = CompensationPlan(
            id=plan.id,
            name=plan.name,
            description=plan.description,
            workflow_id=plan.workflow_id,
            workflow_name=plan.workflow_name,
            steps=plan.steps,
            strategy=plan.strategy,
            scope=plan.scope,
            status=CompensationStatus.ROLLED_BACK,
            created_at=plan.created_at,
            executed_at=plan.executed_at,
            completed_at=datetime.now(UTC),
            error=None,
            metadata=plan.metadata,
        )
        self._plans[plan_id] = plan

        await self._event_bus.publish(CompensationPlanRolledBack(plan=plan))
        await self._event_bus.publish(
            CompensationRolledBack(plan_id=plan.id, plan_name=plan.name),
        )

        duration_ms = (datetime.now(UTC) - started_at).total_seconds() * 1000

        return CompensationResult(
            plan_id=plan.id,
            plan_name=plan.name,
            status=CompensationStatus.ROLLED_BACK,
            total_steps=len(plan.steps),
            duration_ms=duration_ms,
        )

    async def get_transaction(self, transaction_id: str) -> CompensationTransaction:
        transaction = self._transactions.get(transaction_id)
        if transaction is None:
            raise CompensationPlanNotFoundError(
                f"Transaction {transaction_id!r} not found",
                context={"transaction_id": transaction_id},
            )
        return transaction


__all__ = ["CompensationService"]
