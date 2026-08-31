"""Bootstrap domain events."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ProjectScaffolded(DomainEvent):
    event_type: ClassVar[str] = "eaip.bootstrap.project.scaffolded"
    scaffold_id: str = ""
    template_id: str = ""
    project_name: str = ""
    files_created: int = 0


class TemplateCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.bootstrap.template.created"
    template_id: str = ""
    template_name: str = ""
    template_type: str = ""


class TemplateUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.bootstrap.template.updated"
    template_id: str = ""
    template_name: str = ""


class TemplateDeleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.bootstrap.template.deleted"
    template_id: str = ""
    template_name: str = ""


BootstrapEvent = ProjectScaffolded | TemplateCreated | TemplateUpdated | TemplateDeleted

__all__ = [
    "BootstrapEvent",
    "ProjectScaffolded",
    "TemplateCreated",
    "TemplateDeleted",
    "TemplateUpdated",
]
