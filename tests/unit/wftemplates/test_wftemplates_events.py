"""Tests for Workflow Template domain events."""

from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.wftemplates.events import (
    CategoryCreated,
    CategoryUpdated,
    TemplateArchived,
    TemplateCreated,
    TemplateImported,
    TemplatePublished,
    WFTemplatesEvent,
)


class TestBaseEvent:
    def test_all_events_are_domain_events(self) -> None:
        assert issubclass(TemplateCreated, DomainEvent)
        assert issubclass(TemplatePublished, DomainEvent)
        assert issubclass(TemplateArchived, DomainEvent)
        assert issubclass(TemplateImported, DomainEvent)
        assert issubclass(CategoryCreated, DomainEvent)
        assert issubclass(CategoryUpdated, DomainEvent)

    def test_event_type_values(self) -> None:
        assert TemplateCreated.event_type == "eaip.wftemplates.template.created"
        assert TemplatePublished.event_type == "eaip.wftemplates.template.published"
        assert TemplateArchived.event_type == "eaip.wftemplates.template.archived"
        assert TemplateImported.event_type == "eaip.wftemplates.template.imported"
        assert CategoryCreated.event_type == "eaip.wftemplates.category.created"
        assert CategoryUpdated.event_type == "eaip.wftemplates.category.updated"


class TestTemplateCreated:
    def test_fields(self) -> None:
        evt = TemplateCreated(template_id="t1", template_name="Test", category="etl")
        assert evt.template_id == "t1"
        assert evt.template_name == "Test"
        assert evt.category == "etl"


class TestTemplatePublished:
    def test_fields(self) -> None:
        evt = TemplatePublished(template_id="t1", template_name="Test", version="2.0.0")
        assert evt.version == "2.0.0"


class TestTemplateArchived:
    def test_fields(self) -> None:
        evt = TemplateArchived(template_id="t1", template_name="Test")
        assert evt.template_id == "t1"


class TestTemplateImported:
    def test_fields(self) -> None:
        evt = TemplateImported(template_id="t1", template_name="Test", target_workflow_id="wf_t1")
        assert evt.target_workflow_id == "wf_t1"


class TestCategoryCreated:
    def test_fields(self) -> None:
        evt = CategoryCreated(category_id="c1", category_name="ETL")
        assert evt.category_id == "c1"


class TestCategoryUpdated:
    def test_fields(self) -> None:
        evt = CategoryUpdated(category_id="c1", category_name="ETL v2")
        assert evt.category_name == "ETL v2"


class TestUnion:
    def test_union_type(self) -> None:
        evt: WFTemplatesEvent = TemplateCreated(template_id="t1", template_name="T", category="c")
        assert isinstance(evt, TemplateCreated)
