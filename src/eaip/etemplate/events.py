"""Domain events for the enterprise template engine."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class TemplateRegistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.etemplate.template.registered"

    template_id: str
    name: str
    format: str


class TemplateRendered(DomainEvent):
    event_type: ClassVar[str] = "eaip.etemplate.template.rendered"

    template_id: str
    format: str


class TemplateUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.etemplate.template.updated"

    template_id: str
    changes: dict[str, Any]


__all__ = [
    "TemplateRegistered",
    "TemplateRendered",
    "TemplateUpdated",
]
