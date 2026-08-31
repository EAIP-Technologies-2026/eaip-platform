"""Domain events for the agent skill registry."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class SkillRegistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.skillreg.skill.registered"

    skill_id: str
    name: str
    category: str


class SkillUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.skillreg.skill.updated"

    skill_id: str
    changes: dict[str, Any]


class SkillDeprecated(DomainEvent):
    event_type: ClassVar[str] = "eaip.skillreg.skill.deprecated"

    skill_id: str


class SkillMatched(DomainEvent):
    event_type: ClassVar[str] = "eaip.skillreg.skill.matched"

    query: str
    results: tuple[dict[str, Any], ...]


__all__ = [
    "SkillDeprecated",
    "SkillMatched",
    "SkillRegistered",
    "SkillUpdated",
]
