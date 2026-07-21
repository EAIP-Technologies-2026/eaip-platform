"""Domain events for the data classification module."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class ClassificationRuleCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.dataclassify.rule.created"
    rule_id: str
    rule_name: str
    category: str


class ClassificationRuleUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.dataclassify.rule.updated"
    rule_id: str
    rule_name: str
    changes: dict[str, Any] = Field(default_factory=dict)


class ClassificationPerformed(DomainEvent):
    event_type: ClassVar[str] = "eaip.dataclassify.classification.performed"
    resource_id: str
    classes_found: tuple[str, ...] = Field(default=())
    confidence: float = Field(default=0.0)


__all__ = [
    "ClassificationPerformed",
    "ClassificationRuleCreated",
    "ClassificationRuleUpdated",
]
