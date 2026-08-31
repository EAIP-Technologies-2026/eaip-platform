"""Domain events for the model registry."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class ModelRegistered(DomainEvent):
    """Emitted when a model is registered."""

    event_type: ClassVar[str] = "eaip.modelreg.model.registered"

    model_id: str
    name: str
    provider: str


class ModelVersioned(DomainEvent):
    """Emitted when a new version of a model is added."""

    event_type: ClassVar[str] = "eaip.modelreg.model.versioned"

    model_id: str
    version: str
    artifacts: tuple[str, ...] = Field(default=())


class ModelDeprecated(DomainEvent):
    """Emitted when a model is deprecated."""

    event_type: ClassVar[str] = "eaip.modelreg.model.deprecated"

    model_id: str
    reason: str = Field(default="")


class ModelArchived(DomainEvent):
    """Emitted when a model is archived."""

    event_type: ClassVar[str] = "eaip.modelreg.model.archived"

    model_id: str
    reason: str = Field(default="")


__all__ = [
    "ModelArchived",
    "ModelDeprecated",
    "ModelRegistered",
    "ModelVersioned",
]
