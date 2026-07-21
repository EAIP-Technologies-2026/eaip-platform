"""Domain events emitted by the cloud migration assistant."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class AssessmentCreated(DomainEvent):
    """Emitted when a new migration assessment is created."""

    event_type: ClassVar[str] = "eaip.cloudmigrate.assessment_created"

    assessment_id: str
    source: str
    target: str


class PlanApproved(DomainEvent):
    """Emitted when a migration plan is approved."""

    event_type: ClassVar[str] = "eaip.cloudmigrate.plan_approved"

    plan_id: str
    assessment_id: str


class MigrationStarted(DomainEvent):
    """Emitted when a migration begins execution."""

    event_type: ClassVar[str] = "eaip.cloudmigrate.migration_started"

    plan_id: str
    total_tasks: int


class MigrationCompleted(DomainEvent):
    """Emitted when a migration finishes successfully."""

    event_type: ClassVar[str] = "eaip.cloudmigrate.migration_completed"

    plan_id: str
    completed_tasks: int
    duration_seconds: float


class MigrationFailed(DomainEvent):
    """Emitted when a migration fails."""

    event_type: ClassVar[str] = "eaip.cloudmigrate.migration_failed"

    plan_id: str
    failed_task: str
    reason: str
