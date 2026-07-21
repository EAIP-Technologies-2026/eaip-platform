"""Domain events for email template design."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class TemplateCreated(DomainEvent):
    """Emitted when a new email template is created."""

    event_type: ClassVar[str] = "eaip.emailtpl.template.created"

    template_id: str
    name: str
    category: str


class TemplatePublished(DomainEvent):
    """Emitted when a template is published."""

    event_type: ClassVar[str] = "eaip.emailtpl.template.published"

    template_id: str
    name: str
    version: int


class TemplateRendered(DomainEvent):
    """Emitted when a template is rendered with variables."""

    event_type: ClassVar[str] = "eaip.emailtpl.template.rendered"

    template_id: str
    variable_count: int


__all__ = [
    "TemplateCreated",
    "TemplatePublished",
    "TemplateRendered",
]
