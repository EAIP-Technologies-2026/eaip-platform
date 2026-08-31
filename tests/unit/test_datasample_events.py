"""Tests for :mod:`eaip.datasample.events`."""

from __future__ import annotations

import pytest

from eaip.datasample.events import SampleCreated, SampleDefinitionUpdated, SampleExecuted
from eaip.events.event import DomainEvent


class TestSampleCreated:
    def test_defaults(self) -> None:
        e = SampleCreated(definition_id="d1", definition_name="User Sample", strategy="random")
        assert isinstance(e, DomainEvent)
        assert e.event_type == "eaip.datasample.sample.created"
        assert e.definition_id == "d1"

    def test_frozen(self) -> None:
        e = SampleCreated(definition_id="d1", definition_name="n", strategy="s")
        with pytest.raises((ValueError, TypeError)):
            e.definition_id = "d2"  # type: ignore[misc]


class TestSampleExecuted:
    def test_defaults(self) -> None:
        e = SampleExecuted(definition_id="d1", sampled_records=100, total_records=1000)
        assert e.event_type == "eaip.datasample.sample.executed"
        assert e.sampled_records == 100
        assert e.total_records == 1000


class TestSampleDefinitionUpdated:
    def test_defaults(self) -> None:
        e = SampleDefinitionUpdated(
            definition_id="d1", definition_name="User", changes={"sample_size": 200}
        )
        assert e.event_type == "eaip.datasample.sample.definition.updated"
        assert e.changes["sample_size"] == 200


class TestAllEvents:
    def test_all_have_unique_event_types(self) -> None:
        events = [SampleCreated, SampleExecuted, SampleDefinitionUpdated]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))

    def test_all_are_domain_events(self) -> None:
        events = [
            SampleCreated(definition_id="d", definition_name="n", strategy="s"),
            SampleExecuted(definition_id="d", sampled_records=0, total_records=0),
            SampleDefinitionUpdated(definition_id="d", definition_name="n", changes={}),
        ]
        for e in events:
            assert isinstance(e, DomainEvent), f"{type(e).__name__} is not a DomainEvent"
