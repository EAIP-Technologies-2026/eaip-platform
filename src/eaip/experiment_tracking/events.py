"""Experiment tracking domain events — published via EventBus during experiment operations."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class ExperimentCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.experiment.created"
    experiment_id: str = ""
    name: str = ""
    variant_count: int = 0


class ExperimentUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.experiment.updated"
    experiment_id: str = ""
    changes: dict[str, Any] = Field(default_factory=dict)
    previous_status: str = ""


class ExperimentDeleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.experiment.deleted"
    experiment_id: str = ""
    name: str = ""


class ExperimentActivated(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.experiment.activated"
    experiment_id: str = ""
    name: str = ""


class ExperimentPaused(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.experiment.paused"
    experiment_id: str = ""
    name: str = ""


class ExperimentCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.experiment.completed"
    experiment_id: str = ""
    name: str = ""
    winning_variant_id: str = ""


class ExperimentCancelled(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.experiment.cancelled"
    experiment_id: str = ""
    name: str = ""


class ExperimentRunStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.run.started"
    run_id: str = ""
    experiment_id: str = ""
    variant_id: str = ""


class ExperimentRunCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.run.completed"
    run_id: str = ""
    experiment_id: str = ""
    variant_id: str = ""


class ExperimentRunFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.run.failed"
    run_id: str = ""
    experiment_id: str = ""
    variant_id: str = ""
    error_message: str = ""


class ExperimentComparisonComputed(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.comparison.computed"
    comparison_id: str = ""
    experiment_id: str = ""
    metric_id: str = ""
    significant: bool = False
    p_value: float = 0.0


class ExperimentReportGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.report.generated"
    report_id: str = ""
    experiment_id: str = ""
    title: str = ""
    comparison_count: int = 0


class ExperimentHypothesisTested(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.hypothesis.tested"
    hypothesis_id: str = ""
    experiment_id: str = ""
    metric_id: str = ""
    accepted: bool = False
    p_value: float = 0.0


class ExperimentVariantAdded(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.variant.added"
    experiment_id: str = ""
    variant_id: str = ""
    variant_name: str = ""


class ExperimentVariantRemoved(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.variant.removed"
    experiment_id: str = ""
    variant_id: str = ""
    variant_name: str = ""


class ExperimentAssignmentLogged(DomainEvent):
    event_type: ClassVar[str] = "eaip.experiment_tracking.assignment.logged"
    experiment_id: str = ""
    variant_id: str = ""
    entity_id: str = ""


ExperimentTrackingEvent = (
    ExperimentCreated
    | ExperimentUpdated
    | ExperimentDeleted
    | ExperimentActivated
    | ExperimentPaused
    | ExperimentCompleted
    | ExperimentCancelled
    | ExperimentRunStarted
    | ExperimentRunCompleted
    | ExperimentRunFailed
    | ExperimentComparisonComputed
    | ExperimentReportGenerated
    | ExperimentHypothesisTested
    | ExperimentVariantAdded
    | ExperimentVariantRemoved
    | ExperimentAssignmentLogged
)


__all__ = [
    "ExperimentActivated",
    "ExperimentAssignmentLogged",
    "ExperimentCancelled",
    "ExperimentComparisonComputed",
    "ExperimentCompleted",
    "ExperimentCreated",
    "ExperimentDeleted",
    "ExperimentHypothesisTested",
    "ExperimentPaused",
    "ExperimentReportGenerated",
    "ExperimentRunCompleted",
    "ExperimentRunFailed",
    "ExperimentRunStarted",
    "ExperimentTrackingEvent",
    "ExperimentUpdated",
    "ExperimentVariantAdded",
    "ExperimentVariantRemoved",
]
