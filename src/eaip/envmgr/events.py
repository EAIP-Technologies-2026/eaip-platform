"""Domain events for environment variable management."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class VariableCreated(DomainEvent):
    """Emitted when a new environment variable is created."""

    event_type: ClassVar[str] = "eaip.envmgr.variable.created"

    variable_id: str
    name: str
    environment: str
    scope: str = Field(default="application")
    is_secret: bool = Field(default=False)


class VariableUpdated(DomainEvent):
    """Emitted when an environment variable is updated."""

    event_type: ClassVar[str] = "eaip.envmgr.variable.updated"

    variable_id: str
    name: str
    environment: str
    version: int = Field(default=1)


class VariableDeleted(DomainEvent):
    """Emitted when an environment variable is deleted."""

    event_type: ClassVar[str] = "eaip.envmgr.variable.deleted"

    variable_id: str
    name: str
    environment: str


class VariableGroupCreated(DomainEvent):
    """Emitted when a new variable group is created."""

    event_type: ClassVar[str] = "eaip.envmgr.variable_group.created"

    group_id: str
    name: str
    environment: str
    variable_count: int = Field(default=0)


__all__ = [
    "VariableCreated",
    "VariableDeleted",
    "VariableGroupCreated",
    "VariableUpdated",
]
