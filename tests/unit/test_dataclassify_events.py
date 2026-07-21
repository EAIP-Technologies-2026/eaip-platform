"""Tests for :mod:`eaip.dataclassify.events`."""

from __future__ import annotations

import pytest

from eaip.dataclassify.events import (
    ClassificationPerformed,
    ClassificationRuleCreated,
    ClassificationRuleUpdated,
)
from eaip.events.event import DomainEvent


class TestClassificationRuleCreated:
    def test_defaults(self) -> None:
        e = ClassificationRuleCreated(rule_id="r1", rule_name="SSN Rule", category="restricted")
        assert isinstance(e, DomainEvent)
        assert e.event_type == "eaip.dataclassify.rule.created"
        assert e.rule_id == "r1"
        assert e.category == "restricted"

    def test_frozen(self) -> None:
        e = ClassificationRuleCreated(rule_id="r1", rule_name="n", category="c")
        with pytest.raises((ValueError, TypeError)):
            e.rule_id = "r2"  # type: ignore[misc]


class TestClassificationRuleUpdated:
    def test_defaults(self) -> None:
        e = ClassificationRuleUpdated(
            rule_id="r1", rule_name="SSN", changes={"category": "confidential"}
        )
        assert e.event_type == "eaip.dataclassify.rule.updated"
        assert e.changes["category"] == "confidential"


class TestClassificationPerformed:
    def test_defaults(self) -> None:
        e = ClassificationPerformed(
            resource_id="res-1",
            classes_found=("SSN",),
            confidence=0.9,
        )
        assert e.event_type == "eaip.dataclassify.classification.performed"
        assert e.resource_id == "res-1"
        assert "SSN" in e.classes_found


class TestAllEvents:
    def test_all_have_unique_event_types(self) -> None:
        events = [
            ClassificationRuleCreated,
            ClassificationRuleUpdated,
            ClassificationPerformed,
        ]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))

    def test_all_are_domain_events(self) -> None:
        events = [
            ClassificationRuleCreated(rule_id="r1", rule_name="n", category="c"),
            ClassificationRuleUpdated(rule_id="r1", rule_name="n", changes={}),
            ClassificationPerformed(resource_id="r", classes_found=(), confidence=0.0),
        ]
        for e in events:
            assert isinstance(e, DomainEvent), f"{type(e).__name__} is not a DomainEvent"
