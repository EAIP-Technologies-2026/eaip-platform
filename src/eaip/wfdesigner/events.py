"""Domain events for the workflow designer."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class BlueprintCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.wfdesigner.blueprint_created"

    blueprint_id: str
    name: str


class BlueprintPublished(DomainEvent):
    event_type: ClassVar[str] = "eaip.wfdesigner.blueprint_published"

    blueprint_id: str
    name: str
    version: int


class BlueprintVersioned(DomainEvent):
    event_type: ClassVar[str] = "eaip.wfdesigner.blueprint_versioned"

    blueprint_id: str
    old_version: int
    new_version: int


class NodeConfigured(DomainEvent):
    event_type: ClassVar[str] = "eaip.wfdesigner.node_configured"

    blueprint_id: str
    node_id: str
    node_type: str


__all__ = [
    "BlueprintCreated",
    "BlueprintPublished",
    "BlueprintVersioned",
    "NodeConfigured",
]
