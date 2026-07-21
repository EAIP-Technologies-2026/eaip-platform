"""Tests for :mod:`eaip.maskpolicy.events`."""

from __future__ import annotations

import pytest

from eaip.events.event import DomainEvent
from eaip.maskpolicy.events import PolicyApplied, PolicyCreated, PolicyUpdated


class TestPolicyCreated:
    def test_defaults(self) -> None:
        e = PolicyCreated(policy_id="p1", policy_name="PCI", environment="prod")
        assert isinstance(e, DomainEvent)
        assert e.event_type == "eaip.maskpolicy.policy.created"
        assert e.policy_id == "p1"

    def test_frozen(self) -> None:
        e = PolicyCreated(policy_id="p1", policy_name="n", environment="e")
        with pytest.raises((ValueError, TypeError)):
            e.policy_id = "p2"  # type: ignore[misc]


class TestPolicyUpdated:
    def test_defaults(self) -> None:
        e = PolicyUpdated(policy_id="p1", policy_name="PCI", changes={"status": "active"})
        assert e.event_type == "eaip.maskpolicy.policy.updated"
        assert e.changes["status"] == "active"


class TestPolicyApplied:
    def test_defaults(self) -> None:
        e = PolicyApplied(policy_id="p1", policy_name="PCI", rules_applied=3)
        assert e.event_type == "eaip.maskpolicy.policy.applied"
        assert e.rules_applied == 3


class TestAllEvents:
    def test_all_have_unique_event_types(self) -> None:
        events = [PolicyCreated, PolicyUpdated, PolicyApplied]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))

    def test_all_are_domain_events(self) -> None:
        events = [
            PolicyCreated(policy_id="p", policy_name="n", environment="e"),
            PolicyUpdated(policy_id="p", policy_name="n", changes={}),
            PolicyApplied(policy_id="p", policy_name="n", rules_applied=0),
        ]
        for e in events:
            assert isinstance(e, DomainEvent), f"{type(e).__name__} is not a DomainEvent"
