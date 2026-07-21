"""Tests for firewall rule management domain events."""

from __future__ import annotations

import pytest

from eaip.events.event import DomainEvent
from eaip.firewall.events import RuleCreated, RuleDeleted, RuleSetActivated, RuleUpdated


class TestRuleCreated:
    def test_defaults(self) -> None:
        e = RuleCreated(rule_id="r1", name="allow-http", action="ALLOW", environment="prod")
        assert e.event_type == "eaip.firewall.rule.created"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = RuleCreated(rule_id="r1", name="allow-http", action="ALLOW", environment="prod")
        assert e.rule_id == "r1"
        assert e.name == "allow-http"

    def test_frozen(self) -> None:
        e = RuleCreated(rule_id="r1", name="allow-http", action="ALLOW", environment="prod")
        with pytest.raises((ValueError, TypeError)):
            e.rule_id = "r2"


class TestRuleUpdated:
    def test_defaults(self) -> None:
        e = RuleUpdated(rule_id="r1", changes={"port": "8080"})
        assert e.event_type == "eaip.firewall.rule.updated"

    def test_with_values(self) -> None:
        e = RuleUpdated(rule_id="r1", changes={"port": "8080"})
        assert e.changes["port"] == "8080"


class TestRuleDeleted:
    def test_defaults(self) -> None:
        e = RuleDeleted(rule_id="r1", name="allow-http")
        assert e.event_type == "eaip.firewall.rule.deleted"

    def test_with_values(self) -> None:
        e = RuleDeleted(rule_id="r1", name="allow-http")
        assert e.name == "allow-http"


class TestRuleSetActivated:
    def test_defaults(self) -> None:
        e = RuleSetActivated(ruleset_id="rs1", name="prod-rules", rule_count=5, environment="prod")
        assert e.event_type == "eaip.firewall.ruleset.activated"

    def test_with_values(self) -> None:
        e = RuleSetActivated(ruleset_id="rs1", name="prod-rules", rule_count=5, environment="prod")
        assert e.rule_count == 5


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [RuleCreated, RuleUpdated, RuleDeleted, RuleSetActivated]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
