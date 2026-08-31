"""Tests for etemplate domain events."""

from __future__ import annotations

from eaip.etemplate.events import (
    TemplateRegistered,
    TemplateRendered,
    TemplateUpdated,
)
from eaip.events.event import DomainEvent


class TestTemplateRegistered:
    def test_event_type(self) -> None:
        event = TemplateRegistered(template_id="t1", name="Test", format="text")
        assert event.event_type == "eaip.etemplate.template.registered"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = TemplateRegistered(template_id="t1", name="Test", format="text")
        assert event.template_id == "t1"
        assert event.name == "Test"
        assert event.format == "text"


class TestTemplateRendered:
    def test_event_type(self) -> None:
        event = TemplateRendered(template_id="t1", format="text")
        assert event.event_type == "eaip.etemplate.template.rendered"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = TemplateRendered(template_id="t1", format="text")
        assert event.template_id == "t1"
        assert event.format == "text"


class TestTemplateUpdated:
    def test_event_type(self) -> None:
        event = TemplateUpdated(template_id="t1", changes={"name": "New"})
        assert event.event_type == "eaip.etemplate.template.updated"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = TemplateUpdated(template_id="t1", changes={"name": "New"})
        assert event.template_id == "t1"
        assert event.changes == {"name": "New"}


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(TemplateRegistered, DomainEvent)
        assert issubclass(TemplateRendered, DomainEvent)
        assert issubclass(TemplateUpdated, DomainEvent)
