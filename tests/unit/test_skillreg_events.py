"""Tests for skillreg domain events."""

from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.skillreg.events import (
    SkillDeprecated,
    SkillMatched,
    SkillRegistered,
    SkillUpdated,
)


class TestSkillRegistered:
    def test_event_type(self) -> None:
        event = SkillRegistered(skill_id="s1", name="Text", category="nlp")
        assert event.event_type == "eaip.skillreg.skill.registered"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = SkillRegistered(skill_id="s1", name="Text", category="nlp")
        assert event.skill_id == "s1"
        assert event.name == "Text"
        assert event.category == "nlp"


class TestSkillUpdated:
    def test_event_type(self) -> None:
        event = SkillUpdated(skill_id="s1", changes={"name": "New"})
        assert event.event_type == "eaip.skillreg.skill.updated"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = SkillUpdated(skill_id="s1", changes={"name": "New"})
        assert event.skill_id == "s1"
        assert event.changes == {"name": "New"}


class TestSkillDeprecated:
    def test_event_type(self) -> None:
        event = SkillDeprecated(skill_id="s1")
        assert event.event_type == "eaip.skillreg.skill.deprecated"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = SkillDeprecated(skill_id="s1")
        assert event.skill_id == "s1"


class TestSkillMatched:
    def test_event_type(self) -> None:
        event = SkillMatched(query="text", results=())
        assert event.event_type == "eaip.skillreg.skill.matched"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = SkillMatched(query="text", results=({"id": "s1"},))
        assert event.query == "text"
        assert len(event.results) == 1


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(SkillRegistered, DomainEvent)
        assert issubclass(SkillUpdated, DomainEvent)
        assert issubclass(SkillDeprecated, DomainEvent)
        assert issubclass(SkillMatched, DomainEvent)
