"""Domain events for agent templates."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.agenttpl.models import TemplateCategory
from eaip.events.event import DomainEvent


class TemplateCreated(DomainEvent):
    """Emitted when a new agent template is created."""

    event_type: ClassVar[str] = "eaip.agenttpl.template.created"

    template_id: str
    name: str
    category: TemplateCategory


class TemplateUpdated(DomainEvent):
    """Emitted when an agent template is updated."""

    event_type: ClassVar[str] = "eaip.agenttpl.template.updated"

    template_id: str
    changes: dict[str, Any] = Field(default_factory=dict)


class TemplateDeprecated(DomainEvent):
    """Emitted when an agent template is deprecated."""

    event_type: ClassVar[str] = "eaip.agenttpl.template.deprecated"

    template_id: str
    reason: str = Field(default="")


class TemplateApplied(DomainEvent):
    """Emitted when an agent template is applied to create an agent."""

    event_type: ClassVar[str] = "eaip.agenttpl.template.applied"

    template_id: str
    agent_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "TemplateApplied",
    "TemplateCreated",
    "TemplateDeprecated",
    "TemplateUpdated",
]
