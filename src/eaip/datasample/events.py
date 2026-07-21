"""Domain events for the data sampling module."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class SampleCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.datasample.sample.created"
    definition_id: str
    definition_name: str
    strategy: str


class SampleExecuted(DomainEvent):
    event_type: ClassVar[str] = "eaip.datasample.sample.executed"
    definition_id: str
    sampled_records: int
    total_records: int


class SampleDefinitionUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.datasample.sample.definition.updated"
    definition_id: str
    definition_name: str
    changes: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "SampleCreated",
    "SampleDefinitionUpdated",
    "SampleExecuted",
]
