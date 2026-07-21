"""Tests for Bootstrap domain events."""

from __future__ import annotations

from eaip.bootstrap.events import (
    BootstrapEvent,
    ProjectScaffolded,
    TemplateCreated,
    TemplateDeleted,
    TemplateUpdated,
)
from eaip.events.event import DomainEvent


class TestBaseEvent:
    def test_all_events_are_domain_events(self) -> None:
        assert issubclass(ProjectScaffolded, DomainEvent)
        assert issubclass(TemplateCreated, DomainEvent)
        assert issubclass(TemplateUpdated, DomainEvent)
        assert issubclass(TemplateDeleted, DomainEvent)

    def test_event_type_values(self) -> None:
        assert ProjectScaffolded.event_type == "eaip.bootstrap.project.scaffolded"
        assert TemplateCreated.event_type == "eaip.bootstrap.template.created"
        assert TemplateUpdated.event_type == "eaip.bootstrap.template.updated"
        assert TemplateDeleted.event_type == "eaip.bootstrap.template.deleted"


class TestProjectScaffolded:
    def test_fields(self) -> None:
        evt = ProjectScaffolded(
            scaffold_id="s1", template_id="t1", project_name="my_proj", files_created=5
        )
        assert evt.scaffold_id == "s1"
        assert evt.files_created == 5


class TestTemplateCreated:
    def test_fields(self) -> None:
        evt = TemplateCreated(template_id="t1", template_name="Agent", template_type="agent")
        assert evt.template_type == "agent"


class TestTemplateUpdated:
    def test_fields(self) -> None:
        evt = TemplateUpdated(template_id="t1", template_name="Agent v2")
        assert evt.template_name == "Agent v2"


class TestTemplateDeleted:
    def test_fields(self) -> None:
        evt = TemplateDeleted(template_id="t1", template_name="Agent")
        assert evt.template_id == "t1"


class TestUnion:
    def test_union_type(self) -> None:
        evt: BootstrapEvent = ProjectScaffolded(
            scaffold_id="s1", template_id="t1", project_name="p", files_created=1
        )
        assert isinstance(evt, ProjectScaffolded)
