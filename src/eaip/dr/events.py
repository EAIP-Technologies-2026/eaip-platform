"""Domain events for disaster recovery."""

from __future__ import annotations

from typing import ClassVar

from eaip.dr.models import DrPlan, DrTestResult, FailoverEvent
from eaip.events.event import DomainEvent


class DrPlanCreated(DomainEvent):
    event_type: ClassVar[str] = "dr.plan.created"
    plan: DrPlan


class DrPlanActivated(DomainEvent):
    event_type: ClassVar[str] = "dr.plan.activated"
    plan_id: str
    plan_name: str


class DrPlanTested(DomainEvent):
    event_type: ClassVar[str] = "dr.plan.tested"
    plan_id: str
    result: DrTestResult


class DrPlanTestFailed(DomainEvent):
    event_type: ClassVar[str] = "dr.plan.test_failed"
    plan_id: str
    error: str


class FailoverStarted(DomainEvent):
    event_type: ClassVar[str] = "dr.failover.started"
    event: FailoverEvent


class FailoverCompleted(DomainEvent):
    event_type: ClassVar[str] = "dr.failover.completed"
    event: FailoverEvent


class FailoverRolledBack(DomainEvent):
    event_type: ClassVar[str] = "dr.failover.rolled_back"
    event: FailoverEvent


class FailoverFailed(DomainEvent):
    event_type: ClassVar[str] = "dr.failover.failed"
    event: FailoverEvent
    error: str


class RtoRpoViolation(DomainEvent):
    event_type: ClassVar[str] = "dr.violation"
    plan_id: str
    plan_name: str
    rto_seconds: int
    rpo_seconds: int
    actual_seconds: float
    violation_type: str  # "rto" or "rpo"


__all__ = [
    "DrPlanActivated",
    "DrPlanCreated",
    "DrPlanTestFailed",
    "DrPlanTested",
    "FailoverCompleted",
    "FailoverFailed",
    "FailoverRolledBack",
    "FailoverStarted",
    "RtoRpoViolation",
]
