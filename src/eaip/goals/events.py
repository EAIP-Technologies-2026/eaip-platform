"""Goal domain events — published via EventBus during goal lifecycle."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class GoalCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.goals.goal.created"
    goal_id: str = ""
    goal_name: str = ""
    owner: str = ""
    priority: str = ""


class GoalUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.goals.goal.updated"
    goal_id: str = ""
    changes: dict[str, Any] = {}


class GoalCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.goals.goal.completed"
    goal_id: str = ""
    goal_name: str = ""
    final_progress: float = 0.0


class GoalFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.goals.goal.failed"
    goal_id: str = ""
    goal_name: str = ""
    reason: str = ""


class GoalProgressUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.goals.goal.progress_updated"
    goal_id: str = ""
    overall_progress: float = 0.0
    objectives_progress: dict[str, float] = {}
    kpi_values: dict[str, float] = {}


class ObjectiveAssigned(DomainEvent):
    event_type: ClassVar[str] = "eaip.goals.objective.assigned"
    objective_id: str = ""
    goal_id: str = ""
    worker_id: str = ""


class KpiUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.goals.kpi.updated"
    kpi_id: str = ""
    goal_id: str = ""
    previous_value: float = 0.0
    new_value: float = 0.0


class KpiThresholdMet(DomainEvent):
    event_type: ClassVar[str] = "eaip.goals.kpi.threshold_met"
    kpi_id: str = ""
    goal_id: str = ""
    kpi_name: str = ""
    current_value: float = 0.0
    threshold: float = 0.0


GoalEvent = (
    GoalCreated
    | GoalUpdated
    | GoalCompleted
    | GoalFailed
    | GoalProgressUpdated
    | ObjectiveAssigned
    | KpiUpdated
    | KpiThresholdMet
)


__all__ = [
    "GoalCompleted",
    "GoalCreated",
    "GoalEvent",
    "GoalFailed",
    "GoalProgressUpdated",
    "GoalUpdated",
    "KpiThresholdMet",
    "KpiUpdated",
    "ObjectiveAssigned",
]
