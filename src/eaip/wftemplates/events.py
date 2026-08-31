"""Workflow Template Library domain events."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class TemplateCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.wftemplates.template.created"
    template_id: str = ""
    template_name: str = ""
    category: str = ""


class TemplatePublished(DomainEvent):
    event_type: ClassVar[str] = "eaip.wftemplates.template.published"
    template_id: str = ""
    template_name: str = ""
    version: str = ""


class TemplateArchived(DomainEvent):
    event_type: ClassVar[str] = "eaip.wftemplates.template.archived"
    template_id: str = ""
    template_name: str = ""


class TemplateImported(DomainEvent):
    event_type: ClassVar[str] = "eaip.wftemplates.template.imported"
    template_id: str = ""
    template_name: str = ""
    target_workflow_id: str = ""


class CategoryCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.wftemplates.category.created"
    category_id: str = ""
    category_name: str = ""


class CategoryUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.wftemplates.category.updated"
    category_id: str = ""
    category_name: str = ""


WFTemplatesEvent = (
    TemplateCreated
    | TemplatePublished
    | TemplateArchived
    | TemplateImported
    | CategoryCreated
    | CategoryUpdated
)

__all__ = [
    "CategoryCreated",
    "CategoryUpdated",
    "TemplateArchived",
    "TemplateCreated",
    "TemplateImported",
    "TemplatePublished",
    "WFTemplatesEvent",
]
