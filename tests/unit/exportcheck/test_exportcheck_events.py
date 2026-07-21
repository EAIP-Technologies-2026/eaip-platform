"""Tests for export compliance domain events."""

from __future__ import annotations

import pytest

from eaip.exportcheck.events import MatchFlagged, PartyScreened, RuleUpdated
from eaip.exportcheck.models import ScreeningStatus
from eaip.events.event import DomainEvent


class TestPartyScreened:
    def test_defaults(self) -> None:
        e = PartyScreened(party_name="Acme Corp", match_score=0.0, status=ScreeningStatus.CLEAR)
        assert e.event_type == "eaip.exportcheck.party.screened"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = PartyScreened(party_name="Bad Co", match_score=0.96, status=ScreeningStatus.BLOCKED)
        assert e.party_name == "Bad Co"
        assert e.match_score == 0.96
        assert e.status is ScreeningStatus.BLOCKED

    def test_frozen(self) -> None:
        e = PartyScreened(party_name="Acme Corp", match_score=0.0, status=ScreeningStatus.CLEAR)
        with pytest.raises((ValueError, TypeError)):
            e.party_name = "Other"


class TestMatchFlagged:
    def test_defaults(self) -> None:
        e = MatchFlagged(party_name="Bad Co", match_score=0.85, matched_list="sdn")
        assert e.event_type == "eaip.exportcheck.match.flagged"

    def test_with_values(self) -> None:
        e = MatchFlagged(party_name="Bad Co", match_score=0.85, matched_list="sdn")
        assert e.party_name == "Bad Co"
        assert e.match_score == 0.85
        assert e.matched_list == "sdn"


class TestRuleUpdated:
    def test_defaults(self) -> None:
        e = RuleUpdated(rule_id="r1", list_type="sdn", action="added")
        assert e.event_type == "eaip.exportcheck.rule.updated"

    def test_with_values(self) -> None:
        e = RuleUpdated(rule_id="r1", list_type="sdn", action="removed")
        assert e.rule_id == "r1"
        assert e.action == "removed"


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [PartyScreened, MatchFlagged, RuleUpdated]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
