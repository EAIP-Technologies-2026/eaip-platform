"""Domain events for the compensation runtime."""

from __future__ import annotations

from typing import ClassVar

from eaip.compensation.models import (
    CompensationPlan,
    CompensationStep,
    CompensationTransaction,
)
from eaip.events.event import DomainEvent


class CompensationPlanCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.compensation.plan.created"
    plan: CompensationPlan


class CompensationPlanExecuted(DomainEvent):
    event_type: ClassVar[str] = "eaip.compensation.plan.executed"
    plan: CompensationPlan


class CompensationPlanFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.compensation.plan.failed"
    plan: CompensationPlan
    error: str


class CompensationPlanRolledBack(DomainEvent):
    event_type: ClassVar[str] = "eaip.compensation.plan.rolled_back"
    plan: CompensationPlan


class CompensationStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.compensation.started"
    plan_id: str
    plan_name: str


class CompensationStepStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.compensation.step.started"
    plan_id: str
    step: CompensationStep


class CompensationStepCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.compensation.step.completed"
    plan_id: str
    step: CompensationStep
    duration_ms: float


class CompensationStepFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.compensation.step.failed"
    plan_id: str
    step: CompensationStep
    error: str


class CompensationStepSkipped(DomainEvent):
    event_type: ClassVar[str] = "eaip.compensation.step.skipped"
    plan_id: str
    step: CompensationStep
    reason: str


class CompensationCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.compensation.completed"
    plan_id: str
    plan_name: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    duration_ms: float


class CompensationFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.compensation.failed"
    plan_id: str
    plan_name: str
    error: str


class CompensationRolledBack(DomainEvent):
    event_type: ClassVar[str] = "eaip.compensation.rolled_back"
    plan_id: str
    plan_name: str


class CompensationTransactionCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.compensation.transaction.created"
    transaction: CompensationTransaction


class CompensationTransactionCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.compensation.transaction.completed"
    transaction: CompensationTransaction


__all__ = [
    "CompensationCompleted",
    "CompensationFailed",
    "CompensationPlanCreated",
    "CompensationPlanExecuted",
    "CompensationPlanFailed",
    "CompensationPlanRolledBack",
    "CompensationRolledBack",
    "CompensationStarted",
    "CompensationStepCompleted",
    "CompensationStepFailed",
    "CompensationStepSkipped",
    "CompensationStepStarted",
    "CompensationTransactionCompleted",
    "CompensationTransactionCreated",
]
