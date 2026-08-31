"""Strategy domain events — published via EventBus during strategy lifecycle."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class ObjectiveCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.strategy.objective.created"
    objective_id: str = ""
    title: str = ""
    priority: str = ""


class ObjectiveUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.strategy.objective.updated"
    objective_id: str = ""
    changes: dict[str, Any] = {}


class ObjectiveSuperseded(DomainEvent):
    event_type: ClassVar[str] = "eaip.strategy.objective.superseded"
    old_objective_id: str = ""
    new_objective_id: str = ""


class InitiativeCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.strategy.initiative.created"
    initiative_id: str = ""
    objective_id: str = ""
    title: str = ""


class InitiativeLinked(DomainEvent):
    event_type: ClassVar[str] = "eaip.strategy.initiative.linked"
    initiative_id: str = ""
    objective_id: str = ""


class InitiativeStatusChanged(DomainEvent):
    event_type: ClassVar[str] = "eaip.strategy.initiative.status_changed"
    initiative_id: str = ""
    old_status: str = ""
    new_status: str = ""


class ConstraintCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.strategy.constraint.created"
    constraint_id: str = ""
    constraint_type: str = ""
    severity: str = ""


class ConstraintViolated(DomainEvent):
    event_type: ClassVar[str] = "eaip.strategy.constraint.violated"
    constraint_id: str = ""
    context: str = ""


class StateSnapshotCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.strategy.state.snapshot_created"
    state_id: str = ""
    version: int = 0


class StateChanged(DomainEvent):
    event_type: ClassVar[str] = "eaip.strategy.state.changed"
    old_state_id: str = ""
    new_state_id: str = ""


StrategyEvent = (
    ObjectiveCreated
    | ObjectiveUpdated
    | ObjectiveSuperseded
    | InitiativeCreated
    | InitiativeLinked
    | InitiativeStatusChanged
    | ConstraintCreated
    | ConstraintViolated
    | StateSnapshotCreated
    | StateChanged
)


__all__ = [
    "ConstraintCreated",
    "ConstraintViolated",
    "InitiativeCreated",
    "InitiativeLinked",
    "InitiativeStatusChanged",
    "ObjectiveCreated",
    "ObjectiveCreated",
    "ObjectiveSuperseded",
    "ObjectiveUpdated",
    "StateChanged",
    "StateSnapshotCreated",
    "StrategyEvent",
]
