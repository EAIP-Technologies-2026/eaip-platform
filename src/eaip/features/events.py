"""Domain events for the feature flag & experimentation engine."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class FlagCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.features.flag.created"

    flag_id: str
    key: str
    name: str
    enabled: bool
    tags: tuple[str, ...] = Field(default=())


class FlagUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.features.flag.updated"

    flag_id: str
    key: str
    changes: dict[str, Any] = Field(default_factory=dict)


class FlagEnabled(DomainEvent):
    event_type: ClassVar[str] = "eaip.features.flag.enabled"

    flag_id: str
    key: str
    rollout_percentage: int


class FlagDisabled(DomainEvent):
    event_type: ClassVar[str] = "eaip.features.flag.disabled"

    flag_id: str
    key: str


class FlagRolloutChanged(DomainEvent):
    event_type: ClassVar[str] = "eaip.features.flag.rollout_changed"

    flag_id: str
    key: str
    previous_percentage: int
    new_percentage: int


class ExperimentCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.features.experiment.created"

    experiment_id: str
    name: str
    feature_key: str


class ExperimentStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.features.experiment.started"

    experiment_id: str
    feature_key: str


class ExperimentCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.features.experiment.completed"

    experiment_id: str
    feature_key: str


class ExperimentResultRecorded(DomainEvent):
    event_type: ClassVar[str] = "eaip.features.experiment.result_recorded"

    experiment_id: str
    result_id: str
    metric_name: str
    metric_value: float


class VariantAssigned(DomainEvent):
    event_type: ClassVar[str] = "eaip.features.variant.assigned"

    experiment_id: str
    variant_id: str
    entity_id: str


__all__ = [
    "ExperimentCompleted",
    "ExperimentCreated",
    "ExperimentResultRecorded",
    "ExperimentStarted",
    "FlagCreated",
    "FlagDisabled",
    "FlagEnabled",
    "FlagRolloutChanged",
    "FlagUpdated",
    "VariantAssigned",
]
